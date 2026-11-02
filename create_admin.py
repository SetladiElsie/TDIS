#!/usr/bin/env python3
"""
Create an admin user for TDIS application.
Run this script in Render Shell or locally to create the first admin user.
"""
import sys
from app import create_app
from models import db, User
from auth import hash_password

def create_admin_user(name, email, password):
    """Create an admin user"""
    app = create_app('production')
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"❌ User with email {email} already exists!")
            return False
        
        # Create new admin user
        admin = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            is_admin=True,
            is_active=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"✅ Admin user created successfully!")
        print(f"   Name: {name}")
        print(f"   Email: {email}")
        print(f"   Admin: Yes")
        print(f"\nYou can now log in with these credentials.")
        return True

if __name__ == '__main__':
    print("=" * 60)
    print("TDIS Admin User Creation")
    print("=" * 60)
    
    # Get user input
    if len(sys.argv) == 4:
        # Command line arguments
        name = sys.argv[1]
        email = sys.argv[2]
        password = sys.argv[3]
    else:
        # Interactive mode
        print("\nEnter admin user details:")
        name = input("Name: ").strip()
        email = input("Email: ").strip()
        password = input("Password: ").strip()
        
        if not name or not email or not password:
            print("❌ All fields are required!")
            sys.exit(1)
    
    # Validate email format
    if '@' not in email:
        print("❌ Invalid email format!")
        sys.exit(1)
    
    # Create the admin user
    success = create_admin_user(name, email, password)
    sys.exit(0 if success else 1)
