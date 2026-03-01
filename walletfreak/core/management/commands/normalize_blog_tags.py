import ast
from django.core.management.base import BaseCommand
from django.core.cache import cache
from core.services import db


def parse_tags_to_list(tags):
    """
    Normalize tags from any format to a proper list of strings.
    Handles:
      - "['Guide', 'Strategy', 'Tips']"  (Python list string)
      - "Reviews, Strategy, Tips"         (comma-separated string)
      - ["Guide", "Strategy"]             (already a list)
      - None / empty
    """
    if not tags:
        return []

    if isinstance(tags, list):
        # Already a list, but check for nested stringified list
        if len(tags) == 1 and isinstance(tags[0], str) and tags[0].startswith('['):
            try:
                loaded = ast.literal_eval(tags[0])
                if isinstance(loaded, list):
                    return [str(t).strip() for t in loaded if str(t).strip()]
            except (ValueError, SyntaxError):
                pass
        return [str(t).strip() for t in tags if str(t).strip()]

    if isinstance(tags, str):
        # Try parsing as Python literal (e.g. "['Guide', 'Strategy']")
        if tags.startswith('[') and tags.endswith(']'):
            try:
                loaded = ast.literal_eval(tags)
                if isinstance(loaded, list):
                    return [str(t).strip() for t in loaded if str(t).strip()]
            except (ValueError, SyntaxError):
                pass

        # Comma-separated string
        return [t.strip() for t in tags.split(',') if t.strip()]

    return []


class Command(BaseCommand):
    help = 'Normalize blog tags in Firestore from strings to proper arrays'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without writing to Firestore',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be written\n'))

        blogs_ref = db.db.collection('blogs')
        docs = blogs_ref.stream()

        updated = 0
        skipped = 0
        errors = 0

        for doc in docs:
            blog = doc.to_dict()
            slug = blog.get('slug', doc.id)
            raw_tags = blog.get('tags')

            # Parse to proper list
            normalized = parse_tags_to_list(raw_tags)

            # Check if already a proper list
            if isinstance(raw_tags, list) and raw_tags == normalized:
                skipped += 1
                continue

            self.stdout.write(
                f'  {slug}:\n'
                f'    before: {repr(raw_tags)}\n'
                f'    after:  {normalized}'
            )

            if not dry_run:
                try:
                    blogs_ref.document(doc.id).update({'tags': normalized})
                    updated += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    ERROR updating {slug}: {e}'))
                    errors += 1
            else:
                updated += 1

        # Clear caches
        if not dry_run and updated > 0:
            cache.delete('all_published_blogs')
            cache.delete('blog_sidebar_tags')
            self.stdout.write(self.style.SUCCESS('\nCleared blog caches.'))

        self.stdout.write(
            f'\nDone. Updated: {updated}, Skipped (already OK): {skipped}, Errors: {errors}'
        )
