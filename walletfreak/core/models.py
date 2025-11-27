from django.db import models
import json


class FirestoreProxyModel(models.Model):
    """
    Base proxy model for Firestore data.
    This doesn't create actual database tables but allows Django admin to work with Firestore.
    """
    class Meta:
        abstract = True
        managed = False


class CreditCard(FirestoreProxyModel):
    """
    Proxy model for credit cards stored in Firestore.
    Allows Django admin to manage credit card data.
    """
    # These fields mirror the Firestore structure
    card_id = models.CharField(max_length=200, primary_key=True)
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200, blank=True)
    annual_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image_url = models.URLField(blank=True)
    apply_url = models.URLField(blank=True)
    
    # JSON field to store benefits as text (will be parsed/serialized)
    benefits_json = models.TextField(blank=True, help_text="JSON array of benefits")
    
    # Personality associations
    personalities_json = models.TextField(blank=True, help_text="JSON array of personality IDs")
    
    class Meta:
        managed = False
        verbose_name = "Credit Card"
        verbose_name_plural = "Credit Cards"
    
    def __str__(self):
        return self.name
    
    @property
    def benefits(self):
        """Parse benefits from JSON"""
        if self.benefits_json:
            try:
                return json.loads(self.benefits_json)
            except:
                return []
        return []
    
    @benefits.setter
    def benefits(self, value):
        """Serialize benefits to JSON"""
        self.benefits_json = json.dumps(value, indent=2)
    
    @property
    def personalities(self):
        """Parse personalities from JSON"""
        if self.personalities_json:
            try:
                return json.loads(self.personalities_json)
            except:
                return []
        return []
    
    @personalities.setter
    def personalities(self, value):
        """Serialize personalities to JSON"""
        self.personalities_json = json.dumps(value)


class Personality(FirestoreProxyModel):
    """
    Proxy model for personalities stored in Firestore.
    """
    personality_id = models.CharField(max_length=200, primary_key=True)
    name = models.CharField(max_length=200)
    tagline = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, blank=True, help_text="Emoji icon")
    
    class Meta:
        managed = False
        verbose_name = "Personality"
        verbose_name_plural = "Personalities"
    
    def __str__(self):
        return self.name
