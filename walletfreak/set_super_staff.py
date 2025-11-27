#!/usr/bin/env python
"""
Helper script to set a user as super_staff in Firestore.
Usage: python set_super_staff.py <user_email_or_uid> [True|False]

Example:
    python set_super_staff.py user@example.com True
    python set_super_staff.py abc123uid False
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'walletfreak.settings')
django.setup()

from core.services import FirestoreService
from firebase_admin import auth

db = FirestoreService()


def set_super_staff(identifier, is_super_staff=True):
    """
    Set is_super_staff for a user in Firestore.
    
    Args:
        identifier: User email or UID
        is_super_staff: Boolean value (default: True)
    """
    try:
        # Try to get user by email first
        try:
            user = auth.get_user_by_email(identifier)
            uid = user.uid
            print(f"Found user by email: {identifier}")
        except:
            # Assume it's a UID
            uid = identifier
            user = auth.get_user(uid)
            print(f"Found user by UID: {uid}")
        
        # Get current user profile
        user_profile = db.get_user_profile(uid)
        
        if not user_profile:
            print(f"Creating new user profile for {uid}")
            user_profile = {
                'email': user.email,
                'name': user.display_name or '',
                'is_super_staff': is_super_staff
            }
            db.create_user_profile(uid, user_profile)
        else:
            print(f"Updating existing user profile for {uid}")
            db.update_document('users', uid, {'is_super_staff': is_super_staff})
        
        print(f"\n✅ Successfully set is_super_staff={is_super_staff} for user:")
        print(f"   UID: {uid}")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.display_name or 'N/A'}")
        
        if is_super_staff:
            print(f"\n🔑 User can now access Django admin at /admin/")
        else:
            print(f"\n🚫 User admin access has been revoked")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python set_super_staff.py <user_email_or_uid> [True|False]")
        print("\nExample:")
        print("  python set_super_staff.py user@example.com True")
        print("  python set_super_staff.py abc123uid False")
        sys.exit(1)
    
    identifier = sys.argv[1]
    is_super_staff = True
    
    if len(sys.argv) > 2:
        is_super_staff = sys.argv[2].lower() in ['true', '1', 'yes', 'y']
    
    set_super_staff(identifier, is_super_staff)