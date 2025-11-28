import os
import django
from django.utils import timezone
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'walletfreak.settings')
django.setup()

from core.services import db

# Define sample posts
posts = [
    {
        "title": "The Ultimate Guide to Airport Lounges: Is Priority Pass enough?",
        "slug": "ultimate-guide-airport-lounges",
        "excerpt": "Why you should never sit at the gate again, and which cards get you into the best clubs including Centurion and Sapphire Lounges.",
        "content": "Full content here...",
        "author_name": "Alex Smith",
        "author_uid": "admin",
        "status": "published",
        "featured_image": "https://images.unsplash.com/photo-1542296332-2e44a996aa0d?auto=format&fit=crop&q=80&w=2000",
        "tags": ["Guide", "Travel", "Lounges"],
        "published_at": datetime.datetime.now() - datetime.timedelta(days=45),
        "created_at": datetime.datetime.now() - datetime.timedelta(days=45)
    },
    {
        "title": "Is the Amex Gold still worth $250?",
        "slug": "amex-gold-worth-it",
        "excerpt": "With the recent changes to the dining credit and annual fee rumors, we break down the math.",
        "content": "Content...",
        "author_name": "Sarah Jones",
        "author_uid": "admin",
        "status": "published",
        "featured_image": "https://images.unsplash.com/photo-1613243555988-441166d4d6fd?auto=format&fit=crop&q=80&w=800",
        "tags": ["Review", "Amex"],
        "published_at": datetime.datetime.now() - datetime.timedelta(days=47),
        "created_at": datetime.datetime.now() - datetime.timedelta(days=47)
    },
    {
        "title": "How to maximize the Chase Trifecta in 2024",
        "slug": "maximize-chase-trifecta",
        "excerpt": "The Freedom Flex, Freedom Unlimited, and Sapphire Reserve are a powerful combo. Here's how to use them.",
        "content": "Content...",
        "author_name": "Mike Chen",
        "author_uid": "admin",
        "status": "published",
        "featured_image": "https://images.unsplash.com/photo-1563013544-824ae1b704d3?auto=format&fit=crop&q=80&w=800",
        "tags": ["Guide", "Chase"],
        "published_at": datetime.datetime.now() - datetime.timedelta(days=51),
        "created_at": datetime.datetime.now() - datetime.timedelta(days=51)
    },
    {
        "title": "Stop using your debit card for groceries",
        "slug": "stop-using-debit-card",
        "excerpt": "You're leaving 4-6% on the table every time you swipe that debit card at the supermarket.",
        "content": "Content...",
        "author_name": "Alex Smith",
        "author_uid": "admin",
        "status": "published",
        "featured_image": "https://images.unsplash.com/photo-1580913428706-c311ab527ebc?auto=format&fit=crop&q=80&w=800",
        "tags": ["Tips", "Savings"],
        "published_at": datetime.datetime.now() - datetime.timedelta(days=58),
        "created_at": datetime.datetime.now() - datetime.timedelta(days=58)
    },
    {
        "title": "Breaking: Delta SkyMiles changes devalue points",
        "slug": "delta-skymiles-devaluation",
        "excerpt": "Another blow to SkyMiles members as redemption rates increase overnight without warning.",
        "content": "Content...",
        "author_name": "Sarah Jones",
        "author_uid": "admin",
        "status": "published",
        "featured_image": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&q=80&w=800",
        "tags": ["News", "Delta"],
        "published_at": datetime.datetime.now() - datetime.timedelta(days=61),
        "created_at": datetime.datetime.now() - datetime.timedelta(days=61)
    },
    {
        "title": "Capital One Lounge: Denver First Look",
        "slug": "capital-one-lounge-denver",
        "excerpt": "We toured the new space in DEN and it might just be the best domestic lounge in the US.",
        "content": "Content...",
        "author_name": "Mike Chen",
        "author_uid": "admin",
        "status": "published",
        "featured_image": "https://images.unsplash.com/photo-1596265371388-43edbaadab56?auto=format&fit=crop&q=80&w=800",
        "tags": ["Review", "Lounges"],
        "published_at": datetime.datetime.now() - datetime.timedelta(days=64),
        "created_at": datetime.datetime.now() - datetime.timedelta(days=64)
    },
    {
        "title": "The secret to waiving annual fees (Retention Offers)",
        "slug": "waiving-annual-fees",
        "excerpt": "Before you cancel that card, make this one phone call. It could save you $695.",
        "content": "Content...",
        "author_name": "Alex Smith",
        "author_uid": "admin",
        "status": "published",
        "featured_image": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&q=80&w=800",
        "tags": ["Tips", "Savings"],
        "published_at": datetime.datetime.now() - datetime.timedelta(days=69),
        "created_at": datetime.datetime.now() - datetime.timedelta(days=69)
    }
]

print("Populating Firestore with blog posts...")

# We can't easily delete all documents in a collection without listing them all first.
# For now, we'll just add them. In a real scenario, we might want to clear them first.
# Or we can check if they exist by slug.

for post_data in posts:
    # Check if exists
    existing = db.get_blog_by_slug(post_data['slug'])
    if existing:
        print(f"Updating post: {post_data['title']}")
        db.update_blog(existing['id'], post_data)
    else:
        print(f"Creating post: {post_data['title']}")
        db.create_blog(post_data)

print("Done populating Firestore.")
