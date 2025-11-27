# Django Admin Firebase Authentication Setup

This document explains how the Django admin portal (`/admin/`) is integrated with Firebase authentication.

## Overview

The Django admin portal now uses Firebase authentication instead of traditional Django username/password authentication. Access is controlled by the `is_super_staff` field in the user's Firestore profile.

## How It Works

### 1. Authentication Flow

1. User logs in via Firebase (Google, email/password, etc.) on the main site
2. When accessing `/admin/`, the system checks:
   - Is the user authenticated via Firebase (session has `uid`)?
   - Does the user have `is_super_staff: true` in their Firestore profile?
3. If both conditions are met, the user is granted admin access
4. If not, they are redirected to the home page

### 2. Components

#### [`core/admin_auth.py`](core/admin_auth.py)
Custom authentication backend that:
- Verifies Firebase tokens
- Checks `is_super_staff` permission in Firestore
- Creates/updates Django User objects with admin privileges

#### [`core/middleware.py`](core/middleware.py)
Middleware that:
- Intercepts requests to `/admin/`
- Validates Firebase authentication
- Checks Firestore permissions
- Automatically logs users into Django admin if authorized
- Redirects unauthorized users to home page

#### [`settings.py`](walletfreak/settings.py)
Configuration:
```python
MIDDLEWARE = [
    # ... other middleware
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.FirebaseAdminMiddleware',  # Custom Firebase admin auth
    # ... other middleware
]

AUTHENTICATION_BACKENDS = [
    'core.admin_auth.FirebaseAdminBackend',  # Firebase admin authentication
    'django.contrib.auth.backends.ModelBackend',  # Default Django auth (fallback)
]
```

## Granting Admin Access

### Method 1: Using the Helper Script (Recommended)

Use the provided script to grant or revoke admin access:

```bash
# Grant admin access
python walletfreak/set_super_staff.py user@example.com True

# Revoke admin access
python walletfreak/set_super_staff.py user@example.com False

# You can also use Firebase UID instead of email
python walletfreak/set_super_staff.py abc123uid True
```

### Method 2: Manually in Firestore

1. Go to Firebase Console → Firestore Database
2. Navigate to the `users` collection
3. Find the user document (by UID)
4. Add or update the field:
   ```
   is_super_staff: true
   ```

### Method 3: Programmatically

```python
from core.services import FirestoreService

db = FirestoreService()

# Grant admin access
db.update_document('users', 'user_uid_here', {'is_super_staff': True})

# Revoke admin access
db.update_document('users', 'user_uid_here', {'is_super_staff': False})
```

## Security Features

1. **No Password Storage**: Admin access doesn't require Django passwords - Firebase handles all authentication
2. **Real-time Permission Checks**: Permissions are verified on each request to `/admin/`
3. **Automatic Revocation**: If `is_super_staff` is removed from Firestore, access is immediately revoked
4. **Session-based**: Uses existing Firebase authentication session
5. **Redirect Protection**: Unauthorized users are redirected away from admin pages

## User Experience

### For Admin Users (is_super_staff: true)
1. Log in to the site normally via Firebase
2. Navigate to `/admin/`
3. Automatically granted access to Django admin
4. Can manage all Django models and data

### For Regular Users (is_super_staff: false or not set)
1. Log in to the site normally via Firebase
2. Attempt to navigate to `/admin/`
3. Automatically redirected to home page
4. No error message (silent redirect for security)

## Troubleshooting

### User can't access admin despite having is_super_staff: true

1. **Check Firestore**: Verify the field exists and is set to `true` (boolean, not string)
2. **Check Firebase Auth**: Ensure user is logged in (check browser session)
3. **Clear Session**: Log out and log back in
4. **Check Middleware Order**: Ensure `FirebaseAdminMiddleware` is after `AuthenticationMiddleware` in settings

### Admin access not being revoked

1. **Check Firestore**: Verify `is_super_staff` is set to `false` or removed
2. **Clear Django Session**: The middleware checks on each request, but cached sessions might persist briefly
3. **Restart Server**: In development, restart the Django server

### Script errors when setting super_staff

1. **Firebase Credentials**: Ensure Firebase Admin SDK is properly initialized
2. **User Exists**: Verify the user exists in Firebase Authentication
3. **Permissions**: Check that your service account has Firestore write permissions

## Best Practices

1. **Limit Admin Users**: Only grant `is_super_staff` to trusted users
2. **Regular Audits**: Periodically review who has admin access in Firestore
3. **Use Email for Script**: When using the helper script, prefer email over UID for clarity
4. **Document Changes**: Keep a log of who was granted/revoked admin access and when
5. **Test in Development**: Always test permission changes in development first

## Migration Notes

If you had existing Django admin users:
- They will no longer be able to log in with username/password
- They must log in via Firebase first
- Then be granted `is_super_staff: true` in Firestore
- Their existing Django User records will be updated automatically

## Related Files

- [`core/admin_auth.py`](core/admin_auth.py) - Authentication backend
- [`core/middleware.py`](core/middleware.py) - Admin access middleware
- [`set_super_staff.py`](set_super_staff.py) - Helper script
- [`walletfreak/settings.py`](walletfreak/settings.py) - Django configuration