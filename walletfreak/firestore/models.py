from django.db import models

class CreditCard(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255)
    network = models.CharField(max_length=255)
    annual_fee = models.IntegerField(default=0)
    image_url = models.URLField(max_length=500, blank=True)
    apply_url = models.URLField(max_length=500, blank=True)
    credit_range = models.CharField(max_length=100, blank=True)
    rewards_rate = models.CharField(max_length=255, blank=True)
    intro_offer = models.TextField(blank=True)
    
    # JSON fields stored as text for simplicity in admin
    benefits = models.JSONField(default=list, blank=True)
    pros = models.JSONField(default=list, blank=True)
    cons = models.JSONField(default=list, blank=True)
    best_for = models.JSONField(default=list, blank=True)
    
    # New fields
    verdict = models.TextField(blank=True)
    referral_links = models.JSONField(default=list, blank=True)
    
    class Meta:
        managed = False  # No database table creation
        verbose_name = "Credit Card (Firestore)"
        verbose_name_plural = "Credit Cards (Firestore)"
        app_label = 'firestore'

    def __str__(self):
        return self.name

class Personality(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    description = models.TextField()
    image_url = models.URLField(max_length=500, blank=True)
    tagline = models.CharField(max_length=255, blank=True)
    
    # New fields
    avatar_url = models.URLField(max_length=500, blank=True)
    
    # JSON fields
    traits = models.JSONField(default=list, blank=True)
    recommended_cards = models.JSONField(default=list, blank=True)
    
    class Meta:
        managed = False
        verbose_name = "Personality (Firestore)"
        verbose_name_plural = "Personalities (Firestore)"
        app_label = 'firestore'

    def __str__(self):
        return self.name
