
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
                # Check Card Anniversary for Annual Fee
                anniversary_str = card.get('anniversary_date')
                if anniversary_str:
                    try:
                        # Parse anniversary (assuming YYYY-MM-DD or similar, 
                        # but often we just store the next anniversary date directly for simplicity in MVP)
                        # If we stored just the original date, we'd need to calc next occurrence.
                        # Let's assume anniversary_date IS the next upcoming date for MVP simplicity
                        # or we calc it from `added_at`.
                        
                        # Fallback: if anniversary_date is not set, try to use added_at to find next anniversary
                        next_anniversary = None
                        if anniversary_str:
                            next_anniversary = datetime.datetime.strptime(anniversary_str, "%Y-%m-%d").date()
                        elif card.get('added_at'):
                            # Calculate simple annual recurrence
                            added_at = card.get('added_at') # datetime object from firestore
                            # Convert to date
                            # Localize? Assume UTC for server
                            added_date = added_at.date()
                            today = datetime.date.today()
                            
                            # Find next anniversary
                            # Start with this year
                            candidate = added_date.replace(year=today.year)
                            if candidate < today:
                                candidate = added_date.replace(year=today.year + 1)
                            next_anniversary = candidate
                        
                        if next_anniversary:
                            days_until = (next_anniversary - datetime.date.today()).days
                            
                            # --- Annual Fee Logic ---
                            af_pref = prefs.get('annual_fee', {})
                            if af_pref.get('enabled') and days_until > 0:
                                start_days = af_pref.get('start_days_before', 30)
                                repeat_freq = af_pref.get('repeat_frequency', 30) 
                                
                                # Check if we are in the notification window
                                if days_until <= start_days:
                                    # Check frequency (e.g. if today is the day or if (start_days - days_until) % freq == 0)
                                    # Actually simpler: (days_until - start_days) % repeat_freq == 0? 
                                    # No, we want to notify ON start_days, and then every X days.
                                    # So: (start_days - days_until) >= 0 and (start_days - days_until) % repeat_freq == 0
                                    
                                    if (start_days - days_until) % repeat_freq == 0:
                                         card_def = db.get_card_by_slug(card['card_id'])
                                         if card_def and card_def.get('annual_fee', 0) > 0:
                                             subject = f"Upcoming Annual Fee: {card.get('name')}"
                                             message = (
                                                f"Hi {username},\n\n"
                                                f"Your {card.get('name')} annual fee is due in {days_until} days on {next_anniversary}.\n"
                                                f"Ref: {card_def.get('annual_fee')}\n\n"
                                                f"Cheers,\nThe WalletFreak Team"
                                             )
                                             self.send_email(email, subject, message)
                                             emails_sent += 1

                            # --- Benefit Expiration Logic ---
                            # For MVP we can assume benefits expire on anniversary too (common for travel credits)
                            # or use 'time_category' from card def.
                            # Complex logic reduced to: Check generic benefit expiration if preference enabled
                            be_pref = prefs.get('benefit_expiration', {})
                            if be_pref.get('enabled') and days_until > 0:
                                start_days = be_pref.get('start_days_before', 7)
                                repeat_freq = be_pref.get('repeat_frequency', 1) # Default daily
                                
                                if days_until <= start_days:
                                     if (start_days - days_until) % repeat_freq == 0:
                                         # Just send a generic "Use your benefits" email for now
                                         # Ideally we check if they are actually used (via benefit_usage)
                                         subject = f"Don't lose your benefits: {card.get('name')}"
                                         message = (
                                            f"Hi {username},\n\n"
                                            f"Your benefits for {card.get('name')} might expire in {days_until} days on {next_anniversary}.\n"
                                            f"Make sure to use any remaining travel or dining credits!\n\n"
                                            f"Cheers,\nThe WalletFreak Team"
                                         )
                                         self.send_email(email, subject, message)
                                         emails_sent += 1
                                         
                    except Exception as e:
                        print(f"Error checking card {card.get('card_id')}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Done. Sent {emails_sent} emails."))

    def send_email(self, to_email, subject, message):
         try:
            self.stdout.write(f"Sending email to {to_email}: {subject}")
            send_mail(
                subject,
                message,
                'notifications@walletfreak.com',
                [to_email],
                fail_silently=False,
            )
         except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email to {to_email}: {e}"))
