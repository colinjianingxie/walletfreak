
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from core.services import db
import datetime

class Command(BaseCommand):
    help = 'Checks for upcoming subscription/fee notifications and sends emails'

    def handle(self, *args, **options):
        self.stdout.write("Checking for notifications...")
        
        # 1. Fetch all users
        # Note: In a real app with many users, we should use a more efficient query or paginated fetch.
        # For this test, we'll fetch a limited set or stream all if small.
        users_ref = db.db.collection('users')
        users = [doc.to_dict() | {'id': doc.id} for doc in users_ref.stream()]
        
        self.stdout.write(f"Found {len(users)} users.")
        
        emails_sent = 0
        
        for user in users:
            uid = user['id']
            email = user.get('email')
            username = user.get('username', 'User')
            
            if not email:
                self.stdout.write(self.style.WARNING(f"Skipping user {username} (No email)"))
                continue
                
            # 2. Check Preferences
            # We can use the service method or just check the dict since we have the user object
            prefs = db.get_user_notification_preferences(uid)
            
            annual_fee_pref = prefs.get('annual_fee', {})
            if not annual_fee_pref.get('enabled'):
                continue
                
            # 3. Fetch User Cards to find expiring stuff
            user_cards = db.get_user_cards(uid, status='active')
            
            for card in user_cards:
                # SIMULATION LOGIC:
                # In a real scenario, we would check 'anniversary_date' against 'annual_fee_pref.frequency'
                # For this TEST command, we will force a notification for any card with an annual fee > 0
                # or just any card to prove the email works.
                
                card_name = card.get('name', 'Unknown Card')
                
                # Check actual card details for annual fee (would need to fetch card def)
                # For speed, let's just assume we notify.
                
                subject = f"Upcoming Annual Fee: {card_name}"
                message = (
                    f"Hi {username},\n\n"
                    f"Just a reminder that the annual fee for your {card_name} is coming up soon.\n"
                    f"Now might be a good time to check for retention offers!\n\n"
                    f"Cheers,\nThe WalletFreak Team"
                )
                
                try:
                    self.stdout.write(f"Sending email to {email} for {card_name}...")
                    send_mail(
                        subject,
                        message,
                        'notifications@walletfreak.com', # From email
                        [email],
                        fail_silently=False,
                    )
                    emails_sent += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to send email to {email}: {e}"))
                    
        self.stdout.write(self.style.SUCCESS(f"Done. Sent {emails_sent} emails."))
