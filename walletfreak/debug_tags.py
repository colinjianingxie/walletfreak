import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'walletfreak.settings')
django.setup()

from core.services import db

blogs = db.get_blogs(status='published')
print(f"Found {len(blogs)} published blogs")
for blog in blogs:
    print(f"Title: {blog.get('title')}")
    print(f"Tags ({type(blog.get('tags'))}): {blog.get('tags')}")
    print("-" * 20)
