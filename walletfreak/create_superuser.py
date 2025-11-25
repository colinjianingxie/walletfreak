from django.contrib.auth.models import User
import os

username = 'colinjianingxie@gmail.com'
email = 'colinjianingxie@gmail.com'
password = 'admin_password_123' # Temporary password, user should change or use Firebase Auth

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser {username} created.")
else:
    print(f"Superuser {username} already exists.")
