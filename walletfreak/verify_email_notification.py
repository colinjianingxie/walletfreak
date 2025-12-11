
import threading
import time
from blog.models import Blog
from core.services import db
from django.conf import settings
from django.core import mail

def run_verification():
    print("--- Starting SMTP Email Verification Script ---")
    
    # 1. Find a target user
    print("Fetching users from Firestore...")
    users_ref = db.db.collection('users')
    
    target_user_email = None
    target_user_uid = None
    users = users_ref.limit(5).stream()
    
    for doc in users:
        data = doc.to_dict()
        if data.get('email'):
            # Check/Update preferences
            uid = doc.id
            print(f"Found user: {data.get('email')} ({uid})")
            
            # Enable blog updates for this user temporarily
            current_prefs = db.get_user_notification_preferences(uid)
            blog_prefs = current_prefs.get('blog_updates', {})
            if not blog_prefs.get('enabled'):
                print("Enabling blog_updates for test...")
                blog_prefs['enabled'] = True
                current_prefs['blog_updates'] = blog_prefs
                db.update_user_notification_preferences(uid, current_prefs)
            
            target_user_email = data.get('email')
            target_user_uid = uid
            break
    
    if not target_user_uid:
        print("No suitable user found. Please create a user with an email first.")
        return

    print(f"Targeting user: {target_user_email}")

    # 2. Create a dummy blog post
    print("Creating test blog post...")
    test_slug = 'test-notification-email-verification-smtp'
    
    # Cleanup previous 
    Blog.objects.filter(slug=test_slug).delete()
    
    blog = Blog.objects.create(
        title="SMTP Verification Test",
        slug=test_slug,
        content="This is a test post to verify REAL email notifications via Gmail SMTP.",
        excerpt="If you received this, the SMTP configuration is working!",
        author_uid="system_test",
        author_name="System Test",
        status='draft'
    )
    
    # 3. Publish to trigger signal
    print("Publishing post to trigger signal...")
    blog.status = 'published'
    blog.save()
    
    print("Waiting for background thread to send email...")
    time.sleep(5) # Wait a bit longer for real network call
    
    # 4. Cleanup
    print("Cleaning up test post...")
    blog.delete()
    
    print("--- Verification Script Complete ---")
    print("Please check the inbox for: " + str(target_user_email))

run_verification()
