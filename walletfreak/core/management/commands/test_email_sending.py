
from django.core.management.base import BaseCommand
from core.services import db

class Command(BaseCommand):
    help = 'Test email sending to specific users'

    def handle(self, *args, **options):
        test_emails = ['wonmargarita@gmail.com', 'johnrhxie2018@gmail.com']
        
        self.stdout.write(f"Testing email sending to: {', '.join(test_emails)}")
        
        for email in test_emails:
            self.stdout.write(f"Sending test email to {email}...")
            try:
                msg_id = db.send_email_notification(
                    to=email,
                    subject="WalletFreak Test Notification",
                    text_content="This is a test email from your WalletFreak Firebase extension integration. If you are reading this, it works!",
                    html_content="<h1>It Works!</h1><p>This is a test email from your <strong>WalletFreak</strong> Firebase extension integration.</p><p>If you are reading this, the system is correctly writing to the 'mail' collection.</p>"
                )
                if msg_id:
                    self.stdout.write(self.style.SUCCESS(f"Successfully queued email for {email} (Doc ID: {msg_id})"))
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to queue email for {email} (returned None)"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Exception sending to {email}: {e}"))
                
        self.stdout.write(self.style.SUCCESS("Test complete."))
