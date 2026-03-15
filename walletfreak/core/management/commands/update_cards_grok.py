import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from core.card_pipeline import CardUpdatePipeline, deprecate_card


class Command(BaseCommand):
    help = 'Updates credit card data using Grok API with relational file structure versioning'

    def add_arguments(self, parser):
        parser.add_argument('--cards', type=str, help='Comma-separated list of card slugs to update')
        parser.add_argument('--auto-seed', action='store_true', help='Automatically seed after update')
        parser.add_argument('--premium-only', action='store_true', help='Only update premium cards (annual_fee > 0)')
        parser.add_argument('--dry-run', action='store_true', help='Preview without making API calls')
        parser.add_argument('--update-types', type=str, default='all',
                            help='Components to update: header, bonus, benefits, rates, questions, all')
        parser.add_argument('--prompt', action='store_true', help='Output prompt for debugging')
        parser.add_argument('--batch-size', type=int, default=1,
                            help='Number of cards per API call (1=default, 3-5 recommended for cost savings)')
        parser.add_argument('--deprecate', type=str, help='Deprecate a card: slug:reason:successor1,successor2')

    def handle(self, *args, **options):
        master_dir = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'master_cards')
        os.makedirs(master_dir, exist_ok=True)

        # Handle deprecation
        if options.get('deprecate'):
            self._handle_deprecation(master_dir, options['deprecate'])
            return

        api_key = os.environ.get('GROK_API_KEY')
        if not api_key:
            self.stdout.write(self.style.ERROR("GROK_API_KEY not found in environment variables"))
            return

        # Parse update types
        valid_types = {'header', 'bonus', 'benefits', 'rates', 'questions', 'all'}
        update_types_list = [t.strip() for t in options['update_types'].split(',') if t.strip()]
        invalid_types = set(update_types_list) - valid_types
        if invalid_types:
            self.stdout.write(self.style.ERROR(f"Invalid update types: {', '.join(invalid_types)}"))
            return
        if 'all' in update_types_list:
            update_types_list = ['header', 'bonus', 'benefits', 'rates', 'questions']

        self.stdout.write(f"Update types: {', '.join(update_types_list)}")

        # Determine slugs
        if options.get('cards'):
            slugs = [s.strip() for s in options['cards'].split(',') if s.strip()]
        else:
            slugs = [d for d in os.listdir(master_dir) if os.path.isdir(os.path.join(master_dir, d))]

        # Premium filter
        if options.get('premium_only'):
            slugs = self._filter_premium(master_dir, slugs)

        # Skip deprecated cards unless explicitly named
        if not options.get('cards'):
            slugs = self._filter_active(master_dir, slugs)

        # Dry-run preview
        if options.get('dry_run'):
            self.stdout.write(self.style.SUCCESS(f"\nDRY RUN - {len(slugs)} cards would be updated:"))
            for i, slug in enumerate(slugs, 1):
                header_path = os.path.join(master_dir, slug, 'header.json')
                if os.path.exists(header_path):
                    with open(header_path, 'r') as f:
                        h = json.load(f)
                    self.stdout.write(f"  {i}. {h.get('name', slug)} (${h.get('annual_fee', 0)}/year)")
                else:
                    self.stdout.write(f"  {i}. {slug} (NEW CARD)")
            return

        # Run pipeline
        self.stdout.write(f"Processing {len(slugs)} cards...")
        pipeline = CardUpdatePipeline(api_key=api_key, master_dir=master_dir, logger_obj=self.stdout)

        batch_size = options.get('batch_size', 1)
        if batch_size > 1:
            self.stdout.write(f"Batch mode: {batch_size} cards per API call")

        results = pipeline.run(
            slugs=slugs,
            update_types=update_types_list,
            prompt_only=options.get('prompt', False),
            auto_seed=options.get('auto_seed', False),
            batch_size=batch_size,
        )

        for r in results:
            if r.prompt_text:
                self.stdout.write(self.style.SUCCESS(f"\nPrompt for {r.slug}:"))
                self.stdout.write("-" * 50)
                self.stdout.write(r.prompt_text)
            elif r.success:
                cost_str = f" (${r.usage.total_cost:.4f})" if r.usage.total_tokens else ""
                self.stdout.write(self.style.SUCCESS(f"Updated {r.slug}{cost_str}"))
                if r.usage.total_tokens:
                    self.stdout.write(f"  Tokens: {r.usage.prompt_tokens:,} in + {r.usage.completion_tokens:,} out")
                if r.changelog:
                    self.stdout.write(f"  Changelog: {r.changelog.summary}")
            else:
                self.stdout.write(self.style.ERROR(f"Failed {r.slug}: {r.error}"))

    def _filter_premium(self, master_dir, slugs):
        filtered = []
        for slug in slugs:
            header_path = os.path.join(master_dir, slug, 'header.json')
            if os.path.exists(header_path):
                try:
                    with open(header_path, 'r') as f:
                        h = json.load(f)
                    if (h.get('annual_fee') or 0) > 0:
                        filtered.append(slug)
                except Exception:
                    pass
        self.stdout.write(f"Filtered to {len(filtered)} premium cards")
        return filtered

    def _filter_active(self, master_dir, slugs):
        """Skip deprecated cards when running on all cards."""
        filtered = []
        for slug in slugs:
            header_path = os.path.join(master_dir, slug, 'header.json')
            if os.path.exists(header_path):
                try:
                    with open(header_path, 'r') as f:
                        h = json.load(f)
                    if h.get('is_active', True):
                        filtered.append(slug)
                    else:
                        self.stdout.write(self.style.WARNING(f"Skipping deprecated: {slug}"))
                except Exception:
                    filtered.append(slug)
            else:
                filtered.append(slug)  # New card
        return filtered

    def _handle_deprecation(self, master_dir, deprecate_arg):
        """Handle --deprecate slug:reason:successor1,successor2"""
        parts = deprecate_arg.split(':', 2)
        slug = parts[0]
        reason = parts[1] if len(parts) > 1 else ""
        superseded_by = parts[2].split(',') if len(parts) > 2 and parts[2] else None

        import datetime
        deprecated_at = datetime.date.today().isoformat()

        try:
            deprecate_card(master_dir, slug, deprecated_at, superseded_by, reason)
            self.stdout.write(self.style.SUCCESS(f"Deprecated {slug} as of {deprecated_at}"))
            if superseded_by:
                self.stdout.write(f"  Superseded by: {', '.join(superseded_by)}")
        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(str(e)))
