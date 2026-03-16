from .base import BaseFirestoreService
from .users import UserMixin
from .cards import CardMixin
from .personalities import PersonalityMixin
from .blogs import BlogMixin
from .notifications import NotificationMixin
from .in_app_notifications import InAppNotificationMixin
from .datapoints import DataPointMixin
from .subscriptions import SubscriptionMixin
from .loyalty import LoyaltyMixin
from .hotel_prices import HotelPriceMixin

class FirestoreService(
    UserMixin,
    CardMixin,
    PersonalityMixin,
    BlogMixin,
    NotificationMixin,
    InAppNotificationMixin,
    DataPointMixin,
    SubscriptionMixin,
    LoyaltyMixin,
    HotelPriceMixin,
    BaseFirestoreService
):
    """
    Main service class combining all mixins.
    """
    pass

# Create singleton instance
db = FirestoreService()
