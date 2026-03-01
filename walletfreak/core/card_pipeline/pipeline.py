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
from .grok_client import GrokClient
from .prompts import build_update_prompt
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
    ) -> list[PipelineResult]:
        """Run the update pipeline for a list of card slugs.

        Args:
            slugs: Card slug identifiers to process.
            update_types: Components to update (header, benefits, rates, bonus, questions).
            dry_run: Preview changes without API calls or file writes.
            prompt_only: Generate and return prompts without calling API.
            auto_seed: Run seed_db after successful updates.

        Returns:
            List of PipelineResult for each card processed.
        """
        results = []
        updated_slugs = []

        for slug in slugs:
            result = self._process_single_card(slug, update_types, dry_run, prompt_only)
            results.append(result)
            if result.success and not prompt_only:
                updated_slugs.append(slug)

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
            new_data = self.client.call(prompt, apply_url)

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
