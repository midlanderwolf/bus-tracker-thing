#!/usr/bin/env python3
"""
User migration script for bustimes.org to ticketer tracker.

This script migrates user accounts from the existing bustimes.org database
(port 5432) to the new dashboard database (port 5433).
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tracker.models import User


def get_bustimes_connection():
    """Connect to existing bustimes.org database"""
    return psycopg2.connect(
        host=os.environ.get('BUSTIMES_DB_HOST', 'localhost'),
        port=os.environ.get('BUSTIMES_DB_PORT', '5432'),
        dbname=os.environ.get('BUSTIMES_DB_NAME', 'postgres'),
        user=os.environ.get('BUSTIMES_DB_USER', 'postgres'),
        password=os.environ.get('BUSTIMES_DB_PASSWORD', 'postgres')
    )


def get_dashboard_connection():
    """Connect to dashboard database"""
    return psycopg2.connect(
        host=os.environ.get('DASHBOARD_DB_HOST', 'localhost'),
        port=os.environ.get('DASHBOARD_DB_PORT', '5433'),
        dbname=os.environ.get('DASHBOARD_DB_NAME', 'dashboard'),
        user=os.environ.get('DASHBOARD_DB_USER', 'dashboard_user'),
        password=os.environ.get('DASHBOARD_DB_PASSWORD', 'dashboard_password')
    )


def analyze_bustimes_schema():
    """Analyze the bustimes.org database schema"""
    print("Analyzing bustimes.org database schema...")

    try:
        conn = get_bustimes_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if users table exists
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                AND table_name = 'users'
            """)

            if not cur.fetchone():
                print("ERROR: 'users' table not found in bustimes database")
                return False

            # Analyze users table structure
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'users'
                ORDER BY ordinal_position
            """)

            columns = cur.fetchall()
            print(f"Users table has {len(columns)} columns:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")

            # Sample user data
            cur.execute("SELECT COUNT(*) as user_count FROM users")
            user_count = cur.fetchone()['user_count']
            print(f"Total users in bustimes database: {user_count}")

            if user_count > 0:
                cur.execute("""
                    SELECT id, username, email, date_joined
                    FROM users
                    LIMIT 5
                """)
                sample_users = cur.fetchall()
                print("Sample users:")
                for user in sample_users:
                    print(f"  - ID: {user['id']}, Username: {user['username']}, Email: {user['email']}")

        return True

    except Exception as e:
        print(f"ERROR analyzing bustimes database: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def migrate_users():
    """Migrate users from bustimes to dashboard database"""
    print("Starting user migration...")

    try:
        bustimes_conn = get_bustimes_connection()
        dashboard_conn = get_dashboard_connection()

        # Get all users from bustimes
        with bustimes_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, username, email, password, is_active,
                       date_joined, last_login, trusted, ip_address, score
                FROM users
                ORDER BY id
            """)
            bustimes_users = cur.fetchall()

        print(f"Found {len(bustimes_users)} users to migrate")

        migrated = 0
        skipped = 0

        for bustimes_user in bustimes_users:
            try:
                # Check if user already exists in dashboard
                existing_user = User.objects.filter(
                    bustimes_id=bustimes_user['id']
                ).first()

                if existing_user:
                    print(f"Skipping existing user: {bustimes_user['username']}")
                    skipped += 1
                    continue

                # Check if username already exists
                if User.objects.filter(username=bustimes_user['username']).exists():
                    print(f"Username conflict for: {bustimes_user['username']}, skipping")
                    skipped += 1
                    continue

                # Create new user (email is username field in bustimes.org)
                user = User.objects.create(
                    username=bustimes_user['username'],
                    email=bustimes_user['email'],
                    password=bustimes_user['password'],  # Password is already hashed
                    is_active=bustimes_user['is_active'],
                    date_joined=bustimes_user['date_joined'],
                    last_login=bustimes_user['last_login'],
                    trusted=bustimes_user.get('trusted'),
                    ip_address=bustimes_user.get('ip_address'),
                    score=bustimes_user.get('score'),
                    bustimes_id=bustimes_user['id']
                )

                print(f"Migrated user: {user.username}")
                migrated += 1

            except Exception as e:
                print(f"ERROR migrating user {bustimes_user['username']}: {e}")
                continue

        print(f"Migration complete: {migrated} migrated, {skipped} skipped")

    except Exception as e:
        print(f"ERROR during migration: {e}")
    finally:
        if 'bustimes_conn' in locals():
            bustimes_conn.close()
        if 'dashboard_conn' in locals():
            dashboard_conn.close()


def verify_migration():
    """Verify that migration was successful"""
    print("Verifying migration...")

    try:
        # Get counts from both databases
        bustimes_conn = get_bustimes_connection()
        with bustimes_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            bustimes_count = cur.fetchone()[0]

        dashboard_count = User.objects.count()

        print(f"Bustimes users: {bustimes_count}")
        print(f"Dashboard users: {dashboard_count}")

        if dashboard_count >= bustimes_count:
            print("✓ Migration successful")
        else:
            print("⚠ Migration may be incomplete")

    except Exception as e:
        print(f"ERROR verifying migration: {e}")
    finally:
        if 'bustimes_conn' in locals():
            bustimes_conn.close()


def main():
    """Main migration function"""
    print("Bustimes.org to Ticketer Tracker User Migration")
    print("=" * 50)

    if len(sys.argv) > 1 and sys.argv[1] == '--analyze':
        # Just analyze the schema
        if analyze_bustimes_schema():
            print("Schema analysis complete")
        else:
            print("Schema analysis failed")
        return

    # Full migration
    if not analyze_bustimes_schema():
        print("Cannot proceed with migration due to schema issues")
        return

    migrate_users()
    verify_migration()

    print("Migration process complete")


if __name__ == '__main__':
    main()