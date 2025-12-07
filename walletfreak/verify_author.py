
from core.services import db
import sys

def verify_blog_author(slug):
    print(f"Checking blog: {slug}")
    blog = db.get_blog_by_slug(slug)
    if not blog:
        print("Blog not found!")
        return

    print(f"Blog ID: {blog.get('id')}")
    print(f"Author UID: {blog.get('author_uid')}")
    
    uid = blog.get('author_uid')
    if uid:
        user = db.get_user_profile(uid)
        if user:
            print(f"User found: {user.get('username')}, {user.get('name')}")
        else:
            print("User NOT found via get_user_profile")
            
            # Debug: list all users
            print("Listing all users to check IDs:")
            users_ref = db.db.collection('users').stream()
            for u in users_ref:
                print(f" - {u.id}: {u.to_dict().get('username')}")
    else:
        print("No author_uid in blog data")

if __name__ == "__main__":
    # Slug from the screenshot: "the-ultimate-guide-to-airport-lounges-is-priority-pass-enough"
    verify_blog_author("the-ultimate-guide-to-airport-lounges-is-priority-pass-enough")
