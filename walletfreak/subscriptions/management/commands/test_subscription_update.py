from django.core.management.base import BaseCommand
from core.services import db
import uuid

class Command(BaseCommand):
    help = 'Test subscription update logic'

    def handle(self, *args, **options):
        # 1. Create a dummy user ID (we don't strictly need a full user doc if 'update' fails on missing, we'll see)
        # Actually update() requires the doc to exist. So let's create one.
        uid = f"test_user_{uuid.uuid4().hex[:8]}"
        self.stdout.write(f"Creating test user {uid}...")
        
        try:
            db.create_user_profile(uid, {
                'username': uid,
                'email': f"{uid}@example.com"
            })
            self.stdout.write("User created.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to create user: {e}"))
            return

        # 2. Mock subscription update
        sub_id = "sub_test_123"
        self.stdout.write(f"Updating subscription for {uid} with sub_id={sub_id}...")
        
        success = db.update_subscription(
            uid,
            'active',
            subscription_id=sub_id
        )
        
        if success:
            self.stdout.write(self.style.SUCCESS("update_subscription returned True"))
        else:
            self.stdout.write(self.style.ERROR("update_subscription returned False"))

        # 3. Verify
        user = db.get_user_profile(uid)
        self.stdout.write(f"User profile data: {user}")
        
        if user.get('stripe_subscription_id') == sub_id and user.get('subscription_status') == 'active':
            self.stdout.write(self.style.SUCCESS("VERIFIED: Subscription data saved correctly."))
        else:
            self.stdout.write(self.style.ERROR("FAILED: Subscription data NOT saved correctly."))
            
        # Clean up optional
        # db.delete_document('users', uid)
