from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from blog.models import Blog
from .models import Notification, GlobalNotification

@receiver(post_save, sender=Blog)
def notify_new_blog_post(sender, instance, created, **kwargs):
    """
    Create a GlobalNotification when a new blog post is published.
    This replaces the Fan-Out-On-Write approach with a single write (Fan-Out-On-Read).
    """
    if instance.status == 'published' and created:
        # Check if we already have a global notification for this (idempotency check slightly weak but okay)
        exists = GlobalNotification.objects.filter(
            link__endswith=f"/{instance.slug}/", 
            notification_type='blog'
        ).exists()
        
        if not exists:
            GlobalNotification.objects.create(
                title=f"New Article: {instance.title}",
                message=instance.excerpt or "Check out the latest insights.",
                link=f"/blog/{instance.slug}/",
                notification_type='blog'
            )
