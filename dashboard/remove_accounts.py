#!/usr/bin/env python
"""
Script to safely remove all user accounts and related data.
Run with: python manage.py shell < remove_accounts.py
"""

from tracker.models import User, TrackingSession, VehiclePosition
from django.contrib.auth.models import User as AuthUser

def remove_all_accounts():
    """Remove all user accounts and related data"""

    print("Starting account removal process...")

    # Count records before deletion
    user_count = User.objects.count()
    auth_user_count = AuthUser.objects.count()
    session_count = TrackingSession.objects.count()
    position_count = VehiclePosition.objects.count()

    print(f"Found {user_count} custom users, {auth_user_count} auth users")
    print(f"Found {session_count} tracking sessions, {position_count} vehicle positions")

    # Confirm deletion
    confirm = input("This will delete ALL user data. Type 'YES' to continue: ")
    if confirm != 'YES':
        print("Operation cancelled.")
        return

    try:
        # Delete in correct order (respecting foreign keys)
        print("Deleting vehicle positions...")
        VehiclePosition.objects.all().delete()

        print("Deleting tracking sessions...")
        TrackingSession.objects.all().delete()

        print("Deleting custom users...")
        User.objects.all().delete()

        print("Deleting auth users...")
        AuthUser.objects.all().delete()

        print("✅ All accounts and related data removed successfully!")

    except Exception as e:
        print(f"❌ Error during deletion: {e}")
        # Consider rolling back if transaction was used

if __name__ == '__main__':
    remove_all_accounts()