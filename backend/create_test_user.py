"""
Script to create a test user for login testing
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from database.database import engine
from models.user import User
from utils.security import get_password_hash

def create_test_user():
    """Create a test user for development"""
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == "testuser").first()
    
    if existing_user:
        print(f"Test user already exists: {existing_user.username} / {existing_user.email}")
        # Update password to known value
        existing_user.hashed_password = get_password_hash("password123")
        db.commit()
        print("Password updated to 'password123'")
    else:
        # Create test user
        test_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db.add(test_user)
        db.commit()
        print(f"Created test user: testuser / test@example.com with password: password123")
    
    # Verify the user can be found and password works
    from utils.security import verify_password
    
    user = db.query(User).filter(User.username == "testuser").first()
    if user:
        print(f"Found user: {user.username} / {user.email}")
        is_valid = verify_password("password123", user.hashed_password)
        print(f"Password valid: {is_valid}")
    else:
        print("Failed to find user after creation!")

if __name__ == "__main__":
    create_test_user() 