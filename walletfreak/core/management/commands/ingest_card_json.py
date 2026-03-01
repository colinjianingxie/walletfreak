import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from core.card_pipeline import dehydrate_and_save, ChangeTracker, save_changelog


class Command(BaseCommand):
    help = 'Ingests credit card data from a JSON file and updates the master record'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, required=False,
                            help='Path to the JSON file (defaults to ../card_updates.json)')
        parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        file_path = options.get('path') or os.path.join(settings.BASE_DIR, '..', 'card_updates.json')
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        try:
            with open(file_path, 'r') as f:
                new_data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Invalid JSON: {e}"))
            return

        slug = new_data.get('slug-id')
        if not slug:
            self.stdout.write(self.style.ERROR("Input JSON must contain 'slug-id' field"))
            return

        master_dir = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'master_cards')
        os.makedirs(master_dir, exist_ok=True)

        self.stdout.write(f"Processing {slug} from {file_path}...")

        try:
            change_tracker = ChangeTracker(slug) if not dry_run else None
            result = dehydrate_and_save(
                master_dir=master_dir,
                slug=slug,
                new_data=new_data,
                update_types=None,  # Infer from new_data keys
                dry_run=dry_run,
                validate=True,
                change_tracker=change_tracker,
                logger_obj=self.stdout,
            )

            if dry_run:
                self.stdout.write(self.style.SUCCESS(f"Dry run complete for {slug}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated {slug}"))
                self.stdout.write(f"  Created: {result.items_created}, Updated: {result.items_updated}, "
                                  f"Deprecated: {result.items_deprecated}, Cosmetic: {result.cosmetic_updates}")
                if change_tracker and change_tracker.has_changes():
                    changelog_dir = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'changelogs')
                    entry = change_tracker.finalize()
                    save_changelog(changelog_dir, entry)
                    self.stdout.write(f"  Changelog: {entry.summary}")
                self.stdout.write(self.style.WARNING(f"\nNow run: python manage.py seed_db --cards {slug}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing {slug}: {e}"))
            import traceback
            traceback.print_exc()
