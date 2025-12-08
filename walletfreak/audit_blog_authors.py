
import os
import django
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'walletfreak.settings')
django.setup()

from core.services import db

def audit_blog_authors():
    print("Fetching ALL published blogs...")
    blogs = db.get_blogs(status='published')
    print(f"Total blogs: {len(blogs)}")
    
    missing_uid = 0
    missing_username = 0
    valid = 0
    
    for blog in blogs:
        uid = blog.get('author_uid')
        username = blog.get('author_username')
        
        if not uid:
            print(f"❌ Blog '{blog.get('title')}' (ID: {blog.get('id')}) has NO author_uid")
            missing_uid += 1
            continue
            
        if not username or username == 'Unknown':
             # Try to fetch user to see if it exists
            user = db.get_user_profile(uid)
            if not user:
                 print(f"❌ Blog '{blog.get('title')}' (ID: {blog.get('id')}) has author_uid '{uid}' but USER NOT FOUND")
            else:
                 print(f"⚠️ Blog '{blog.get('title')}' (ID: {blog.get('id')}) has user but username is '{username}' (User profile username: '{user.get('username')}')")
            missing_username += 1
        else:
            valid += 1
            
    print(f"\nSummary:")
    print(f"Valid: {valid}")
    print(f"Missing UID: {missing_uid}")
    print(f"Missing/Unknown Username: {missing_username}")

if __name__ == '__main__':
    audit_blog_authors()
