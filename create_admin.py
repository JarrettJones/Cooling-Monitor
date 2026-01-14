"""
Script to create an initial admin user for the Cooling Monitor system
Run this script to create your first admin account
"""
import asyncio
import sys
from sqlalchemy import select
from app.database import async_session_maker, init_db
from app.models.user import User

async def create_admin_user():
    """Create an admin user"""
    print("\n🔐 Cooling Monitor - Create Admin User\n")
    
    # Initialize database
    await init_db()
    
    # Get username
    username = input("Enter username (3-50 characters): ").strip()
    if len(username) < 3 or len(username) > 50:
        print("❌ Username must be between 3 and 50 characters")
        sys.exit(1)
    
    # Get password
    password = input("Enter password (minimum 6 characters): ").strip()
    if len(password) < 6:
        print("❌ Password must be at least 6 characters")
        sys.exit(1)
    
    # Confirm password
    password_confirm = input("Confirm password: ").strip()
    if password != password_confirm:
        print("❌ Passwords do not match")
        sys.exit(1)
    
    # Create user
    async with async_session_maker() as db:
        # Check if username already exists
        result = await db.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"❌ User '{username}' already exists")
            sys.exit(1)
        
        # Create admin user
        admin_user = User(
            username=username,
            hashed_password=User.hash_password(password),
            is_admin=1  # Admin role
        )
        
        db.add(admin_user)
        await db.commit()
        
        print(f"\n✅ Admin user '{username}' created successfully!")
        print(f"\nYou can now login at: http://localhost:8000/login")
        print(f"Username: {username}")

if __name__ == "__main__":
    try:
        asyncio.run(create_admin_user())
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
