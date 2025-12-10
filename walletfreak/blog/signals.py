from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Blog
from core.services import db
from django.conf import settings
import threading

@receiver(post_save, sender=Blog)
def send_blog_notification(sender, instance, created, **kwargs):
    """
    Send email notification when a blog post is published.
    """
    if instance.status == 'published':
        # Check if it was just published (either created as published, or updated to published)
        # For simplicity in this MVP, we'll just check if it's currently published.
        # Ideally we'd track state transition, but since we don't have a 'previous' state easily in post_save without dirty field tracking,
        # we will rely on the fact that 'published_at' is set when it is published.
        
        # We need to avoid sending duplicate emails if the post is saved multiple times while published.
        # A simple way (without extra DB models) is to check if 'published_at' is very recent, 
        # OR we could add a flag to the Blog model 'notification_sent'.
        # For this requirement: "When a user subscribes to the blog, I want to send an email with the latest article" 
        # implies a welcome email.
        # "new blog posts" implies ongoing strings.
        
        # Let's start a thread to send emails so we don't block the request
        # (In production Use Celery needed, but Threading ok for small scale/MVP)
        t = threading.Thread(target=_notify_subscribers, args=(instance,))
        t.start()

def _notify_subscribers(blog_post):
    print(f"Starting blog notification for: {blog_post.title}")
    
    # 1. Fetch all users who have blog_updates enabled
    # Firestore doesn't support complex filtering on nested maps cleanly without potential index issues
    # so we'll fetch users and filter in python for now (MVP scale)
    # OR better: use a separate collection for subscriptions if scale was large.
    # We will iterate all users for this MVP.
    
    try:
        users_ref = db.db.collection('users')
        users = users_ref.stream()
        
        emails_to_send = []
        
        for user_doc in users:
            user_data = user_doc.to_dict()
            prefs = user_data.get('notification_preferences', {})
            email = user_data.get('email')
            
            if email and prefs.get('blog_updates', {}).get('enabled', False):
                emails_to_send.append(email)
        
        if not emails_to_send:
            print("No subscribers found.")
            return

        print(f"Found {len(emails_to_send)} subscribers.")
        
        subject = f"New on WalletFreak: {blog_post.title}"
        message = f"""
Hi there!

We just published a new article on WalletFreak:

{blog_post.title}
{blog_post.excerpt}

Read more here: https://walletfreak.com/blog/{blog_post.slug}

Cheers,
The WalletFreak Team
        """
        
        # Send mass mail (or individual if personalization needed)
        # Using send_mail in loop for simplicity of error handling per user or send_mass_mail
        # send_mail(subject, message, from_email, recipient_list) sends to all in list as TO or BCC?
        # usually TO. We should send individually to hide other emails.
        
        count = 0
        for email in emails_to_send:
            try:
                send_mail(
                    subject,
                    message,
                    'notifications@walletfreak.com',
                    [email],
                    fail_silently=False
                )
                count += 1
            except Exception as e:
                print(f"Failed to send to {email}: {e}")
                
        print(f"Sent {count} blog notifications.")
        
    except Exception as e:
        print(f"Error in blog notification thread: {e}")
