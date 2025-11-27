from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Make a user a superuser by email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the user to make superuser')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully made {email} a superuser'))
        except User.DoesNotExist:
            # Create the user if they don't exist
            username = email
            password = 'admin_password_123'  # Temporary password
            user = User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Created superuser {email} with temporary password'))
