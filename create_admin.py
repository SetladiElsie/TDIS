"""
Create Admin User Script
========================

Use this script to create the first admin user for production deployment.

Usage:
    python create_admin.py

The script will prompt you for:
- Admin name
- Admin email
- Admin password (with strength validation)
"""

import sys
import getpass
from app import create_app
from models import db, User
from auth import hash_password, validate_password_strength

def create_admin_user():
    """Interactive script to create an admin user"""
    
    print("=" * 60)
    print("TDIS - Create Admin User")
    print("=" * 60)
    print()
    
    # Create app context
    app = create_app('production')
    
    with app.app_context():
        # Check if admin exists
        admin_count = User.query.filter_by(is_admin=True, is_active=True).count()
        
        if admin_count > 0:
            print(f"⚠️  Warning: {admin_count} admin user(s) already exist.")
            response = input("Do you want to create another admin? (y/n): ").strip().lower()
            if response != 'y':
                print("Cancelled.")
                return
            print()
        
        # Get admin details
        print("Enter admin details:")
        print()
        
        name = input("Full Name: ").strip()
        if not name:
            print("❌ Error: Name is required")
            sys.exit(1)
        
        email = input("Email Address: ").strip().lower()
        if not email or '@' not in email:
            print("❌ Error: Valid email is required")
            sys.exit(1)
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"❌ Error: User with email {email} already exists")
            sys.exit(1)
        
        # Get password with validation
        print()
        print("Password requirements:")
        print("  - At least 8 characters")
        print("  - One uppercase letter")
        print("  - One lowercase letter")
        print("  - One number")
        print("  - One special character (!@#$%^&*...)")
        print()
        
        while True:
            password = getpass.getpass("Password: ")
            password_confirm = getpass.getpass("Confirm Password: ")
            
            if password != password_confirm:
                print("❌ Passwords do not match. Try again.")
                print()
                continue
            
            # Validate password strength
            is_valid, errors = validate_password_strength(password)
            if not is_valid:
                print("❌ Password does not meet requirements:")
                for error in errors:
                    print(f"  - {error}")
                print()
                continue
            
            break
        
        # Create admin user
        try:
            user = User(
                name=name,
                email=email,
                password_hash=hash_password(password),
                is_admin=True,
                is_active=True,
                must_change_password=False
            )
            
            db.session.add(user)
            db.session.commit()
            
            print()
            print("=" * 60)
            print("✅ Admin user created successfully!")
            print("=" * 60)
            print()
            print(f"Name:  {name}")
            print(f"Email: {email}")
            print(f"Admin: Yes")
            print()
            print("You can now log in to the TDIS portal with these credentials.")
            print()
            
        except Exception as e:
            print()
            print(f"❌ Error creating admin user: {str(e)}")
            sys.exit(1)


if __name__ == '__main__':
    try:
        create_admin_user()
    except KeyboardInterrupt:
        print()
        print("Cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print()
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
