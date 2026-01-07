from datetime import datetime
from firebase_admin import firestore

class SubscriptionMixin:
    """
    Mixin for managing User Subscriptions and Stripe mappings in Firestore.
    """
    
    def get_user_stripe_id(self, uid):
        """
        Get the Stripe Customer ID for a user from their Firestore profile.
        """
        user_profile = self.get_user_profile(uid)
        if user_profile:
            return user_profile.get('stripe_customer_id')
        return None

    def update_user_stripe_id(self, uid, stripe_customer_id):
        """
        Update the Stripe Customer ID for a user.
        """
        try:
            # We store this on the user document itself for easy access
            self.db.collection('users').document(uid).update({
                'stripe_customer_id': stripe_customer_id,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"Error updating stripe_customer_id for {uid}: {e}")
            return False

    def update_subscription(self, uid, status, subscription_id=None, current_period_end=None, cancel_at_period_end=False, price_id=None):
        """
        Update subscription status in Firestore.
        """
        try:
            data = {
                'subscription_status': status,
                'stripe_subscription_id': subscription_id,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            if current_period_end:
                data['subscription_end_date'] = current_period_end
            
            if cancel_at_period_end is not None:
                data['cancel_at_period_end'] = cancel_at_period_end
                
            if price_id:
                data['price_id'] = price_id
            
            # Map 'active' or 'trialing' to generic premium flag if widely used, 
            # though we are moving away from is_premium field, some old logic might check it.
            # Best to keep it synced for safety if any legacy code checks it.
            if status in ['active', 'trialing']:
                data['is_premium'] = True
            else:
                data['is_premium'] = False

            self.db.collection('users').document(uid).update(data)
            return True
        except Exception as e:
            print(f"Error updating subscription for {uid}: {e}")
            return False

    def get_user_subscription(self, uid):
        """
        Get subscription details for a user.
        """
        user_profile = self.get_user_profile(uid)
        if not user_profile:
            return None
            
        return {
            'status': user_profile.get('subscription_status', 'inactive'),
            'stripe_subscription_id': user_profile.get('stripe_subscription_id'),
            'current_period_end': user_profile.get('subscription_end_date'),
            'cancel_at_period_end': user_profile.get('cancel_at_period_end', False),
            'price_id': user_profile.get('price_id'),
            'is_premium': user_profile.get('is_premium', False)
        }
