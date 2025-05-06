from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.database import get_db
from models.user import User
from models.preference import UserPreference
from schemas.user import UserResponse
from schemas.preference import PreferenceCreate, PreferenceResponse
from utils.auth import get_current_user, get_current_active_user

router = APIRouter(tags=["Users"])

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user profile information
    """
    return current_user

@router.get("/users/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get user by ID
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.get("/users/{user_id}/preferences", response_model=PreferenceResponse)
async def get_user_preferences(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get preferences for a user. Users can only access their own preferences.
    """
    # Ensure user can only access their own preferences
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own preferences"
        )
    
    # Get preferences from database
    preferences = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    
    # If preferences don't exist, return default empty preferences
    if not preferences:
        return {
            "user_id": user_id,
            "dietary_restrictions": [],
            "favorite_cuisines": [],
            "cooking_skill_level": "beginner",
            "health_goals": [],
            "allergies": []
        }
    
    # Convert the DB model to a dictionary and explicitly use the list properties
    response_data = {
        "user_id": preferences.user_id,
        "dietary_restrictions": preferences.dietary_restrictions_list,
        "favorite_cuisines": preferences.favorite_cuisines_list,
        "cooking_skill_level": preferences.cooking_skill_level,
        "health_goals": preferences.health_goals_list,
        "allergies": preferences.allergies_list
    }
    
    return response_data

@router.put("/users/{user_id}/preferences", response_model=PreferenceResponse)
async def update_user_preferences(
    user_id: int,
    preferences: PreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update preferences for a user. Users can only update their own preferences.
    """
    # Ensure user can only update their own preferences
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own preferences"
        )
    
    # Check if preferences exist
    db_preferences = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    
    if db_preferences:
        # Update existing preferences with proper list handling
        db_preferences.dietary_restrictions = ",".join(preferences.dietary_restrictions)
        db_preferences.favorite_cuisines = ",".join(preferences.favorite_cuisines)
        db_preferences.cooking_skill_level = preferences.cooking_skill_level
        db_preferences.health_goals = ",".join(preferences.health_goals)
        db_preferences.allergies = ",".join(preferences.allergies)
    else:
        # Create new preferences
        db_preferences = UserPreference(
            user_id=user_id,
            dietary_restrictions=preferences.dietary_restrictions,
            favorite_cuisines=preferences.favorite_cuisines,
            cooking_skill_level=preferences.cooking_skill_level,
            health_goals=preferences.health_goals,
            allergies=preferences.allergies
        )
        db.add(db_preferences)
    
    db.commit()
    db.refresh(db_preferences)
    
    # Convert the DB model to a dictionary and explicitly use the list properties
    response_data = {
        "user_id": db_preferences.user_id,
        "dietary_restrictions": db_preferences.dietary_restrictions_list,
        "favorite_cuisines": db_preferences.favorite_cuisines_list,
        "cooking_skill_level": db_preferences.cooking_skill_level,
        "health_goals": db_preferences.health_goals_list,
        "allergies": db_preferences.allergies_list
    }
    
    return response_data 