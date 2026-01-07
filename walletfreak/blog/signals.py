from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Blog
from core.services import db
from django.conf import settings
import threading

# Flag to prevent infinite loops during sync operations
_disable_firestore_sync = False

@receiver(post_save, sender=Blog)
def sync_blog_to_firestore(sender, instance, created, **kwargs):
    """
    Sync blog post to Firestore on save.
    """
    if _disable_firestore_sync:
        return

    try:
        data = instance.to_dict()
        # Ensure we use the slug as the document ID
        doc_id = instance.slug
        
        # We can use update_blog (which handles notifications) if it exists, 
        # or create_blog. Since update_blog expects an ID...
        
        # Check if it exists first to decide? 
        # Actually create_blog uses 'set' (merge=True usually or overwrite).
        # core.services.blogs.create_blog uses create_document -> set.
        # core.services.blogs.update_blog uses update_document -> update.
        
        # If we use create_blog, it might overwrite fields if not careful, 
        # but to_dict() has all fields.
        
        # However, update_blog has logic for notifications.
        # Logic: If it's a new post (created=True) OR we just published it.
        
        if created:
            db.create_blog(data)
        else:
            db.update_blog(doc_id, data)
            
    except Exception as e:
        print(f"Error syncing blog to Firestore: {e}")

@receiver(post_delete, sender=Blog)
def delete_blog_from_firestore(sender, instance, **kwargs):
    """
    Delete blog post from Firestore on delete.
    """
    if _disable_firestore_sync:
        return

    try:
        db.delete_blog(instance.slug)
    except Exception as e:
        print(f"Error deleting blog from Firestore: {e}")

@receiver(post_save, sender=Blog)
def send_blog_notification(sender, instance, created, **kwargs):
    """
    Send email notification when a blog post is published.
    """
    # ... (Keep existing logic or rely on update_blog's internal notification logic?)
    # update_blog in core/services/blogs.py DOES handle notifications.
    # So we can effectively disable this signal if we trust update_blog.
    # BUT wait, update_blog runs in a thread. 
    # If we call db.update_blog above, it will trigger the notification.
    # So we should probably REMOVE this separate signal to avoid duplicates.
    pass
