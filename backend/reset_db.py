"""
Script to reset the database and create fresh tables
"""
import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from database.database import Base, engine
from models.user import User
from models.recipe import Recipe  
from models.preference import UserPreference

def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database reset complete!")
    
    # Create sample data
    create_sample_data()
    
    print("Done!")

def create_sample_data():
    """Create sample data for testing"""
    from sqlalchemy.orm import sessionmaker
    from utils.security import get_password_hash
    
    Session = sessionmaker(bind=engine)
    db = Session()
    
    print("Creating sample user...")
    # Create a test user
    test_user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    print("Creating sample preferences...")
    # Create preferences for test user
    test_preferences = UserPreference(
        user_id=test_user.id,
        dietary_restrictions=["vegetarian", "gluten-free"],
        favorite_cuisines=["italian", "mexican", "indian"],
        cooking_skill_level="intermediate",
        health_goals=["weight_loss", "heart_health"],
        allergies=["nuts"]
    )
    db.add(test_preferences)
    
    print("Creating sample recipes...")
    # Create some sample recipes
    recipes = [
        {
            "title": "Spaghetti Carbonara",
            "description": "Classic Italian pasta dish with eggs, cheese, and bacon.",
            "ingredients": ["spaghetti", "eggs", "parmesan cheese", "pancetta", "black pepper", "olive oil"],
            "instructions": ["Boil pasta according to package instructions", "Fry pancetta until crispy", "Mix eggs with cheese", "Combine everything", "Season with black pepper"],
            "cooking_time": 30,
            "difficulty": "easy",
            "cuisine": "italian",
            "dietary_restrictions": []
        },
        {
            "title": "Vegetable Curry",
            "description": "Spicy vegetable curry with coconut milk.",
            "ingredients": ["potatoes", "carrots", "peas", "coconut milk", "curry powder", "garlic", "onion"],
            "instructions": ["Chop vegetables", "Sauté garlic and onion", "Add vegetables and spices", "Pour in coconut milk", "Simmer until vegetables are tender"],
            "cooking_time": 45,
            "difficulty": "medium",
            "cuisine": "indian",
            "dietary_restrictions": ["vegetarian", "vegan", "gluten-free"]
        },
        {
            "title": "Vegetarian Tacos",
            "description": "Delicious tacos filled with spiced beans and vegetables.",
            "ingredients": ["corn tortillas", "black beans", "bell peppers", "onions", "avocado", "salsa", "lime"],
            "instructions": ["Heat tortillas", "Cook beans with spices", "Sauté vegetables", "Assemble tacos", "Top with salsa and avocado"],
            "cooking_time": 20,
            "difficulty": "easy", 
            "cuisine": "mexican",
            "dietary_restrictions": ["vegetarian", "gluten-free"]
        }
    ]
    
    for recipe_data in recipes:
        db_recipe = Recipe(
            title=recipe_data["title"],
            description=recipe_data["description"],
            ingredients=json.dumps(recipe_data["ingredients"]),
            instructions=json.dumps(recipe_data["instructions"]),
            cooking_time=recipe_data["cooking_time"],
            difficulty=recipe_data["difficulty"],
            cuisine=recipe_data["cuisine"],
            dietary_restrictions=json.dumps(recipe_data["dietary_restrictions"]),
            is_ai_generated=False
        )
        db.add(db_recipe)
    
    db.commit()
    print(f"Created {len(recipes)} sample recipes")

if __name__ == "__main__":
    reset_database() 