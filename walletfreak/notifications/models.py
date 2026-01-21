from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Notification(models.Model):
    """
    Model to store user notifications.
    """
    NOTIFICATION_TYPES = [
        ('blog', 'Blog Post'),
        ('system', 'System Message'),
        ('update', 'Update'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"


class GlobalNotification(models.Model):
    """
    Model for broadcast notifications sent to all users (e.g. new blog posts).
    Fan-out-on-read pattern.
    """
    NOTIFICATION_TYPES = [
        ('blog', 'Blog Post'),
        ('system', 'System Message'),
        ('update', 'Update'),
    ]

    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[Global] {self.title}"


class GlobalNotificationRead(models.Model):
    """
    Tracks which global notifications a user has read.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='global_reads')
    notification = models.ForeignKey(GlobalNotification, on_delete=models.CASCADE, related_name='read_receipts')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'notification')

    def __str__(self):
        return f"{self.user.username} read {self.notification.title}"


class NotificationPreference(models.Model):
    """
    Stores user preferences for notification types.
    If a record exists with is_enabled=False, the user has opted out.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_preferences')
    notification_type = models.CharField(max_length=20, choices=GlobalNotification.NOTIFICATION_TYPES)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'notification_type')

    def __str__(self):
        return f"{self.user.username} - {self.notification_type}: {self.is_enabled}"
