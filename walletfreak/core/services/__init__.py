from .base import BaseFirestoreService
from .users import UserMixin
from .cards import CardMixin
from .personalities import PersonalityMixin
from .blogs import BlogMixin
from .notifications import NotificationMixin
from .datapoints import DataPointMixin
from .subscriptions import SubscriptionMixin

class FirestoreService(
    UserMixin,
    CardMixin,
    PersonalityMixin,
    BlogMixin,
    NotificationMixin,
    DataPointMixin,
    SubscriptionMixin,
    BaseFirestoreService
):
    """
    Main service class combining all mixins.
    """
    pass

# Create singleton instance
db = FirestoreService()
