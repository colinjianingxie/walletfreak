from django.db import models
from core.models import FirestoreProxyModel
from django.utils import timezone
import datetime

class DataPoint(FirestoreProxyModel):
    """
    Proxy model for DataPoints stored in Firestore.
    """
    STATUS_CHOICES = (
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    )

    id = models.CharField(max_length=200, primary_key=True)
    user_id = models.CharField(max_length=200)
    user_display_name = models.CharField(max_length=200)
    card_slug = models.CharField(max_length=100)
    card_name = models.CharField(max_length=200)
    benefit_name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Success')
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    
    # Voting
    upvote_count = models.IntegerField(default=0)
    upvoted_by_json = models.TextField(blank=True, help_text="List of UIDs who upvoted")

    class Meta:
        managed = False
        verbose_name = "Data Point"
        verbose_name_plural = "Data Points"

    def __str__(self):
        return f"{self.user_display_name} - {self.card_name} - {self.status}"
    
    @property
    def user(self):
        """
        Mock user object for template compatibility.
        """
        class MockUser:
            def __init__(self, uid, username):
                self.id = uid
                self.username = username # This is the Handle/Display Name now? No, wait. 
                # In views.py we might need to adjust.
                # If we store 'user_display_name' as the handle, let's expose it.
                # But 'user.username' was used as UID in previous logic!
                # Let's keep 'username' as UID for compatibility with existing loops?
                # Actually, let's map it cleanly:
                pass
        
        # We store 'user_id' (UID) and 'user_display_name' (Handle/FirstLast)
        # Template uses: dp.user.username (Expecting UID for wallet link)
        # Template uses: dp.user_display_name (Expecting Handle)
        
        # So we return a MockUser where username=user_id (UID)
        m = MockUser(self.user_id, self.user_id)
        return m

    @property
    def upvoted_by(self):
        import json
        if self.upvoted_by_json:
            try:
                return json.loads(self.upvoted_by_json)
            except:
                return []
        return []

