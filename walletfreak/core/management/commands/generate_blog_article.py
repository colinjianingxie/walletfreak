"""Management command to auto-generate and publish a blog article using Grok + Unsplash."""

import json
import os
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from core.card_pipeline.grok_client import GrokClient
from core.blog_pipeline.prompts import build_topic_discovery_prompt, build_article_generation_prompt
from core.blog_pipeline.unsplash_client import search_photo


AUTHOR_UID = 'zCQejFW74Xf9Hc6yF37HGEVi4zJ3'


class Command(BaseCommand):
    help = 'Generate and publish a blog article using Grok API and Unsplash'

    def add_arguments(self, parser):
        parser.add_argument('--topic', type=str, help='Override auto-topic selection with a specific topic')
        parser.add_argument('--dry-run', action='store_true', help='Print generated article without saving')
        parser.add_argument('--no-image', action='store_true', help='Skip Unsplash image fetch')

    def handle(self, *args, **options):
        api_key = os.environ.get('GROK_API_KEY')
        if not api_key:
            self.stdout.write(self.style.ERROR("GROK_API_KEY not set"))
            return

        grok = GrokClient(api_key=api_key)
        card_names = self._load_card_names()
        total_cost = 0.0

        # Step 1: Discover topic
        if options.get('topic'):
            topic_data = {
                'topic': options['topic'],
                'angle': options['topic'],
                'keywords': [],
                'category': 'credit-cards',
                'experience_level': 'intermediate',
            }
            self.stdout.write(f"Using manual topic: {options['topic']}")
        else:
            self.stdout.write("Discovering trending topic...")
            prompt = build_topic_discovery_prompt()
            result = grok.call_with_usage(prompt)
            total_cost += result.usage.total_cost

            if not result.data:
                self.stdout.write(self.style.ERROR("Failed to discover topic from Grok"))
                return

            topic_data = result.data
            self.stdout.write(self.style.SUCCESS(
                f"Topic: {topic_data.get('topic')} (${result.usage.total_cost:.4f})"
            ))

        # Step 2: Generate article
        self.stdout.write("Generating article...")
        article_prompt = build_article_generation_prompt(
            topic=topic_data.get('topic', ''),
            angle=topic_data.get('angle', ''),
            keywords=topic_data.get('keywords', []),
            category=topic_data.get('category', 'credit-cards'),
            experience_level=topic_data.get('experience_level', 'intermediate'),
            card_names=card_names,
        )
        result = grok.call_with_usage(article_prompt)
        total_cost += result.usage.total_cost

        if not result.data:
            self.stdout.write(self.style.ERROR("Failed to generate article from Grok"))
            return

        article = result.data
        self.stdout.write(self.style.SUCCESS(
            f"Article: \"{article.get('title')}\" (${result.usage.total_cost:.4f})"
        ))

        # Step 3: Fetch featured image
        featured_image = ''
        if not options.get('no_image'):
            self.stdout.write("Fetching featured image from Unsplash...")
            query = topic_data.get('topic', article.get('title', 'credit cards'))
            photo = search_photo(query)
            if photo:
                featured_image = photo['url']
                self.stdout.write(self.style.SUCCESS(
                    f"Image by {photo['photographer']}: {photo['url'][:80]}..."
                ))
            else:
                self.stdout.write(self.style.WARNING("No image found, continuing without"))

        # Step 4: Build blog data
        now = datetime.now()
        title = article.get('title', 'Untitled')
        slug = slugify(title)

        blog_data = {
            'title': title,
            'slug': slug,
            'content': article.get('content', ''),
            'excerpt': article.get('excerpt', ''),
            'author_uid': AUTHOR_UID,
            'status': 'published',
            'featured_image': featured_image,
            'tags': article.get('tags', 'news'),
            'is_premium': False,
            'read_time': article.get('read_time', 'medium'),
            'experience_level': article.get('experience_level', 'intermediate'),
            'vendor': article.get('vendor', ''),
            'created_at': now,
            'updated_at': now,
            'published_at': now,
            'upvote_count': 0,
            'downvote_count': 0,
            'comment_count': 0,
            'view_count': 0,
            'users_upvoted': [],
        }

        # Dry run: print and exit
        if options.get('dry_run'):
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS("DRY RUN — Article preview:"))
            self.stdout.write("=" * 60)
            self.stdout.write(f"\nTitle: {blog_data['title']}")
            self.stdout.write(f"Slug: {blog_data['slug']}")
            self.stdout.write(f"Tags: {blog_data['tags']}")
            self.stdout.write(f"Vendor: {blog_data['vendor']}")
            self.stdout.write(f"Experience: {blog_data['experience_level']}")
            self.stdout.write(f"Read time: {blog_data['read_time']}")
            self.stdout.write(f"Image: {blog_data['featured_image'] or '(none)'}")
            self.stdout.write(f"\nExcerpt:\n{blog_data['excerpt']}")
            self.stdout.write(f"\nContent:\n{blog_data['content']}")
            self.stdout.write(f"\nTotal cost: ${total_cost:.4f}")
            return

        # Step 5: Check for duplicate slug and save
        from core.services import db

        existing = db.get_blog_by_slug(slug)
        if existing:
            slug = f"{slug}-{int(now.timestamp())}"
            blog_data['slug'] = slug
            self.stdout.write(self.style.WARNING(f"Slug collision, using: {slug}"))

        blog_id = db.create_blog(blog_data)
        self.stdout.write(self.style.SUCCESS(
            f"\nPublished! slug={slug} id={blog_id}"
        ))
        self.stdout.write(f"Total cost: ${total_cost:.4f}")

    def _load_card_names(self) -> list[str]:
        """Load card names from master_cards headers."""
        master_dir = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'master_cards')
        names = []
        if not os.path.isdir(master_dir):
            return names

        for slug in sorted(os.listdir(master_dir)):
            header_path = os.path.join(master_dir, slug, 'header.json')
            if not os.path.isfile(header_path):
                continue
            try:
                with open(header_path) as f:
                    header = json.load(f)
                if header.get('is_active', True):
                    names.append(header.get('name', slug))
            except (json.JSONDecodeError, OSError):
                continue

        return names
