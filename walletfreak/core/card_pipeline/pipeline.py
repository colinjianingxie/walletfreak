"""Pipeline orchestrator — Hydrate -> API -> Validate -> Save -> Changelog."""

import os
import uuid
import logging
from dataclasses import dataclass, field

from django.conf import settings

from .hydrator import hydrate_card
from .dehydrator import dehydrate_and_save, DehydrationResult
from .changelog import ChangeTracker, save_changelog
from .categories import load_category_hierarchy
from .grok_client import GrokClient, ApiUsage
from .prompts import build_update_prompt, build_batch_update_prompt
from .models import ChangelogEntry

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of processing a single card through the pipeline."""
    slug: str
    success: bool = False
    dehydration_result: DehydrationResult | None = None
    changelog: ChangelogEntry | None = None
    validation_errors: list[str] = field(default_factory=list)
    prompt_text: str | None = None
    error: str | None = None
    usage: ApiUsage = field(default_factory=ApiUsage)


class CardUpdatePipeline:
    """Orchestrates the card update pipeline: Hydrate -> Grok API -> Validate -> Dehydrate -> Changelog."""

    def __init__(
        self,
        api_key: str,
        master_dir: str | None = None,
        data_dir: str | None = None,
        changelog_dir: str | None = None,
        logger_obj=None,
    ):
        self.client = GrokClient(api_key)
        self.master_dir = master_dir or os.path.join(settings.BASE_DIR, 'walletfreak_data', 'master_cards')
        self.data_dir = data_dir or os.path.join(settings.BASE_DIR, 'walletfreak_data')
        self.changelog_dir = changelog_dir or os.path.join(settings.BASE_DIR, 'walletfreak_data', 'changelogs')
        self.log = logger_obj or logger
        self.run_id = uuid.uuid4().hex[:8]

    def run(
        self,
        slugs: list[str],
        update_types: list[str],
        dry_run: bool = False,
        prompt_only: bool = False,
        auto_seed: bool = False,
        batch_size: int = 1,
    ) -> list[PipelineResult]:
        """Run the update pipeline for a list of card slugs.

        Args:
            slugs: Card slug identifiers to process.
            update_types: Components to update (header, benefits, rates, bonus, questions).
            dry_run: Preview changes without API calls or file writes.
            prompt_only: Generate and return prompts without calling API.
            auto_seed: Run seed_db after successful updates.
            batch_size: Number of cards per API call. 1 = one card per call (default).
                        3-5 recommended for cost efficiency.

        Returns:
            List of PipelineResult for each card processed.
        """
        results = []
        updated_slugs = []

        if batch_size > 1 and not prompt_only and not dry_run:
            # Process in batches
            for i in range(0, len(slugs), batch_size):
                batch_slugs = slugs[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(slugs) + batch_size - 1) // batch_size
                _log(self.log, f"Batch {batch_num}/{total_batches}: {', '.join(batch_slugs)}")

                batch_results = self._process_batch(batch_slugs, update_types)
                for r in batch_results:
                    results.append(r)
                    if r.success:
                        updated_slugs.append(r.slug)
        else:
            # Process one at a time
            for slug in slugs:
                result = self._process_single_card(slug, update_types, dry_run, prompt_only)
                results.append(result)
                if result.success and not prompt_only:
                    updated_slugs.append(slug)

        # Log cost summary
        total_input = sum(r.usage.prompt_tokens for r in results)
        total_output = sum(r.usage.completion_tokens for r in results)
        total_cost = sum(r.usage.total_cost for r in results)
        if total_input or total_output:
            _log(self.log, f"\n--- Cost Summary ---")
            _log(self.log, f"Cards processed: {len(results)}")
            _log(self.log, f"Total tokens: {total_input:,} input + {total_output:,} output = {total_input + total_output:,}")
            _log(self.log, f"Total cost: ${total_cost:.4f}")
            _log(self.log, f"Avg cost/card: ${total_cost / max(len(results), 1):.4f}")

        if auto_seed and updated_slugs:
            self._auto_seed(updated_slugs)

        return results

    def _process_single_card(
        self,
        slug: str,
        update_types: list[str],
        dry_run: bool,
        prompt_only: bool,
    ) -> PipelineResult:
        """Process a single card through the pipeline."""
        result = PipelineResult(slug=slug)

        try:
            # 1. Hydrate
            current_data = hydrate_card(self.master_dir, slug, update_types)

            # 2. Build prompt
            cat_hierarchy = load_category_hierarchy(self.data_dir)
            prompt = build_update_prompt(current_data, slug, update_types, cat_hierarchy)

            if prompt_only:
                result.prompt_text = prompt
                result.success = True
                return result

            if dry_run:
                result.success = True
                return result

            # 3. Call Grok API
            apply_url = current_data.get('application_link')
            call_result = self.client.call_with_usage(prompt, apply_url)
            result.usage = call_result.usage
            new_data = call_result.data

            if not new_data:
                result.error = "Failed to get valid response from Grok API"
                return result

            # 4. Validate + Dehydrate + Save
            change_tracker = ChangeTracker(slug, run_id=self.run_id)
            dehy_result = dehydrate_and_save(
                master_dir=self.master_dir,
                slug=slug,
                new_data=new_data,
                update_types=update_types,
                dry_run=False,
                validate=True,
                change_tracker=change_tracker,
                logger_obj=self.log,
            )

            result.dehydration_result = dehy_result
            result.validation_errors = dehy_result.validation_errors

            # 5. Changelog
            if change_tracker.has_changes():
                changelog_entry = change_tracker.finalize()
                save_changelog(self.changelog_dir, changelog_entry)
                result.changelog = changelog_entry

            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.exception("Error processing %s", slug)

        return result

    def _process_batch(
        self,
        slugs: list[str],
        update_types: list[str],
    ) -> list[PipelineResult]:
        """Process multiple cards in a single API call."""
        results = {slug: PipelineResult(slug=slug) for slug in slugs}

        try:
            # 1. Hydrate all cards
            cards_data = []
            for slug in slugs:
                try:
                    current_data = hydrate_card(self.master_dir, slug, update_types)
                    cards_data.append((current_data, slug))
                except Exception as e:
                    results[slug].error = str(e)

            if not cards_data:
                return list(results.values())

            # 2. Build batch prompt
            cat_hierarchy = load_category_hierarchy(self.data_dir)
            prompt = build_batch_update_prompt(cards_data, update_types, cat_hierarchy)

            # 3. Call Grok API once for the batch
            call_result = self.client.call_with_usage(prompt)
            batch_response = call_result.data

            # Split cost evenly across cards in the batch
            per_card_usage = ApiUsage(
                prompt_tokens=call_result.usage.prompt_tokens // len(cards_data),
                completion_tokens=call_result.usage.completion_tokens // len(cards_data),
                total_tokens=call_result.usage.total_tokens // len(cards_data),
                input_cost=call_result.usage.input_cost / len(cards_data),
                output_cost=call_result.usage.output_cost / len(cards_data),
                total_cost=call_result.usage.total_cost / len(cards_data),
            )

            if not batch_response or not isinstance(batch_response, dict):
                for slug in slugs:
                    if not results[slug].error:
                        results[slug].error = "Failed to get valid batch response from Grok API"
                        results[slug].usage = per_card_usage
                return list(results.values())

            # 4. Dehydrate each card from the batch response
            for slug in slugs:
                if results[slug].error:
                    continue

                results[slug].usage = per_card_usage
                new_data = batch_response.get(slug)

                if not new_data:
                    results[slug].error = f"Card {slug} missing from batch response"
                    continue

                try:
                    change_tracker = ChangeTracker(slug, run_id=self.run_id)
                    dehy_result = dehydrate_and_save(
                        master_dir=self.master_dir,
                        slug=slug,
                        new_data=new_data,
                        update_types=update_types,
                        dry_run=False,
                        validate=True,
                        change_tracker=change_tracker,
                        logger_obj=self.log,
                    )

                    results[slug].dehydration_result = dehy_result
                    results[slug].validation_errors = dehy_result.validation_errors

                    if change_tracker.has_changes():
                        changelog_entry = change_tracker.finalize()
                        save_changelog(self.changelog_dir, changelog_entry)
                        results[slug].changelog = changelog_entry

                    results[slug].success = True

                except Exception as e:
                    results[slug].error = str(e)
                    logger.exception("Error dehydrating %s from batch", slug)

        except Exception as e:
            for slug in slugs:
                if not results[slug].error:
                    results[slug].error = str(e)
            logger.exception("Batch processing failed")

        return list(results.values())

    def _auto_seed(self, slugs: list[str]):
        """Call seed_db management command for updated cards."""
        from django.core.management import call_command
        try:
            cards_arg = ",".join(slugs)
            call_command('seed_db', cards=cards_arg)
            _log(self.log, "Auto-seed completed.", style='success')
        except Exception as e:
            _log(self.log, f"Auto-seed failed: {e}", style='error')


def _log(log_obj, message: str, style: str | None = None):
    """Log supporting both Django command stdout and standard logging."""
    if hasattr(log_obj, 'write'):
        if style == 'success' and hasattr(log_obj, 'style'):
            log_obj.write(log_obj.style.SUCCESS(message))
        elif style == 'error' and hasattr(log_obj, 'style'):
            log_obj.write(log_obj.style.ERROR(message))
        else:
            log_obj.write(message)
    else:
        log_obj.info(message)
