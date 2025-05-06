from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import asyncio
import json
import os
from sqlalchemy import text

from database.database import get_db, engine
from models.user import User
from models.preference import UserPreference
from models.recipe import Recipe
from schemas.preference import PreferenceCreate, PreferenceResponse
from schemas.recipe import RecipeGenerationRequest
from utils.auth import get_current_active_user
from utils.openai_helper import generate_recipe
from utils.state_manager import active_generation_tasks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/preferences", tags=["Preferences"])

# Number of initial recipes to generate for a new user
INITIAL_RECIPES_COUNT = 6

async def generate_recipes_for_user(user_id: int, preferences_id: int, count: int = INITIAL_RECIPES_COUNT):
    """
    Generate a specified number of recipes based on user preferences and store them in the database.
    First deletes any existing AI-generated recipes for this user.
    Uses a dedicated database session for the background task.
    """
    logger.info(f"Starting background generation for user {user_id}, preferences {preferences_id}, count {count}")
    
    # Check if there's already an active generation for this user
    if user_id in active_generation_tasks:
        logger.info(f"Generation already in progress for user {user_id}, skipping")
        return
    
    # Mark this user as having an active generation
    active_generation_tasks[user_id] = True
    
    try:
        # Create a new database session specifically for this background task
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Check if preferences still exist (they might have been deleted)
            user_preferences = db.query(UserPreference).filter(UserPreference.id == preferences_id).first()
            if not user_preferences:
                logger.error(f"Cannot find preferences with ID {preferences_id}")
                return
            
            # Get user object
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"Cannot find user with ID {user_id}")
                return
            
            logger.info(f"Generating {count} recipes for user {user_id}")
            
            # First, delete all previous AI-generated recipes for this user
            try:
                # Use a direct SQL query for better performance
                deletion_query = text(
                    "DELETE FROM recipes WHERE generated_for_user_id = :user_id AND is_ai_generated = TRUE"
                )
                db.execute(deletion_query, {"user_id": user_id})
                db.commit()
                logger.info(f"Successfully deleted previous recipes for user {user_id}")
            except Exception as e:
                logger.error(f"Error deleting previous recipes: {str(e)}")
                db.rollback()
            
            # Extract user preferences
            cuisines = user_preferences.favorite_cuisines_list
            
            # --- Corrected Dietary Restrictions Logic --- 
            # Get restrictions directly from the stored list property
            dietary_restrictions = user_preferences.dietary_restrictions_list
            logger.debug(f"Extracted dietary restrictions from DB list: {dietary_restrictions}")
            
            # Add boolean flags as well, ensuring no duplicates 
            # (though ideally, the list property should be the source of truth)
            flags_to_add = set() 
            if user_preferences.vegetarian: flags_to_add.add("vegetarian")
            if user_preferences.vegan: flags_to_add.add("vegan")
            if user_preferences.gluten_free: flags_to_add.add("gluten-free")
            if user_preferences.dairy_free: flags_to_add.add("dairy-free")
            if user_preferences.nut_free: flags_to_add.add("nut-free")
            
            # Combine the list from DB string and boolean flags
            current_restrictions_set = set(dietary_restrictions)
            combined_restrictions = list(current_restrictions_set.union(flags_to_add))
            logger.debug(f"Combined dietary restrictions (from list + flags): {combined_restrictions}")
            # --- End Correction --- 
                
            # Extract allergies and health goals separately
            allergies = user_preferences.allergies_list
            health_goals = user_preferences.health_goals_list
            
            # Create flavor preferences dictionary
            flavor_preferences = {
                "spicy": user_preferences.spicy_level,
                "sweet": user_preferences.sweet_level,
                "savory": user_preferences.savory_level,
                "bitter": user_preferences.bitter_level,
                "sour": user_preferences.sour_level
            }
            
            # Determine meal types to focus on
            meal_types = []
            if user_preferences.breakfast:
                meal_types.append("breakfast")
            if user_preferences.lunch:
                meal_types.append("lunch")
            if user_preferences.dinner:
                meal_types.append("dinner")
            if user_preferences.snacks:
                meal_types.append("snack")
            if user_preferences.desserts:
                meal_types.append("dessert")
                
            # Set cooking skill level
            skill_level = user_preferences.cooking_skill_level or "medium"
            
            # Set max cooking time
            max_cooking_time = user_preferences.cooking_time_max or 60
            
            # Generate recipes one by one
            generated_recipes = []
            
            # Keep track of generated titles to avoid duplicates
            generated_titles = set()
            
            for i in range(count):
                try:
                    # Select a random cuisine and meal type if available
                    cuisine = cuisines[i % len(cuisines)] if cuisines else None
                    meal_type = meal_types[i % len(meal_types)] if meal_types else "dinner"
                    
                    logger.info(f"Generating recipe {i+1}/{count} - cuisine: {cuisine}, meal type: {meal_type}")
                    
                    # Generate recipe via OpenAI
                    recipe_data = await generate_recipe(
                        cuisine_preferences=[cuisine] if cuisine else [],
                        dietary_restrictions=combined_restrictions,
                        flavor_preferences=flavor_preferences,
                        meal_type=meal_type,
                        skill_level=skill_level,
                        max_cooking_time=max_cooking_time,
                        allergies=allergies,
                        health_goals=health_goals
                    )
                    
                    # Check for duplicate titles
                    title = recipe_data.get("title", "")
                    if title in generated_titles:
                        logger.warning(f"Skipping duplicate recipe: {title}")
                        continue
                        
                    generated_titles.add(title)
                    
                    # Process recipe data to ensure correct types
                    processed_cuisine = recipe_data.get("cuisine", "")
                    if isinstance(processed_cuisine, list):
                        processed_cuisine = ", ".join(processed_cuisine)
                        
                    # Get ingredients either as a list or from JSON string
                    ingredients = recipe_data.get("ingredients", "[]")
                    if isinstance(ingredients, str):
                        try:
                            # Try to parse as JSON
                            ingredients_list = json.loads(ingredients)
                        except:
                            # If not valid JSON, split by newlines/commas
                            ingredients_list = [item.strip() for item in ingredients.replace('\n', ',').split(',') if item.strip()]
                    else:
                        ingredients_list = ingredients
                        
                    # Make sure ingredients is stored as a JSON string
                    ingredients_json = json.dumps(ingredients_list)
                    
                    # Get instructions either as a list or from newline-separated string
                    instructions = recipe_data.get("instructions", "")
                    if isinstance(instructions, str):
                        # Split by newlines
                        instructions_list = [step.strip() for step in instructions.split('\n') if step.strip()]
                    else:
                        instructions_list = instructions
                        
                    # Store instructions as JSON string
                    instructions_json = json.dumps(instructions_list)
                    
                    # Get dietary restrictions
                    recipe_dietary_restrictions = recipe_data.get("dietary_restrictions", "[]")
                    if isinstance(recipe_dietary_restrictions, str):
                        try:
                            dietary_restrictions_list = json.loads(recipe_dietary_restrictions)
                        except:
                            dietary_restrictions_list = [item.strip() for item in recipe_dietary_restrictions.replace('\n', ',').split(',') if item.strip()]
                    else:
                        dietary_restrictions_list = recipe_dietary_restrictions if recipe_dietary_restrictions else []
                        
                    # Store dietary restrictions as JSON string
                    dietary_restrictions_json = json.dumps(dietary_restrictions_list)
                    
                    # Get prep time and cook time
                    prep_time = recipe_data.get("prep_time", 0)
                    cook_time = recipe_data.get("cook_time", 0)
                    
                    # Create a new recipe in the database
                    db_recipe = Recipe(
                        title=recipe_data.get("title", ""),
                        description=recipe_data.get("description", ""),
                        ingredients=ingredients_json,
                        instructions=instructions_json,
                        cuisine=processed_cuisine,
                        cooking_time=cook_time,  # Use cook_time directly
                        prep_time=prep_time,     # Add prep_time field
                        total_time=prep_time + cook_time,  # Add total time
                        difficulty=recipe_data.get("difficulty", "medium"),
                        dietary_restrictions=dietary_restrictions_json,
                        is_ai_generated=True,
                        generated_for_user_id=user_id
                    )
                    
                    db.add(db_recipe)
                    generated_recipes.append(db_recipe)
                    logger.info(f"Successfully generated recipe: {db_recipe.title}")
                    
                    # Commit each recipe immediately to avoid large transactions
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Error generating recipe {i+1}: {str(e)}")
                    continue
            
            logger.info(f"Generated {len(generated_recipes)} recipes for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error in background task: {str(e)}")
            db.rollback()
        finally:
            # Always close the session
            db.close()
    
    finally:
        # Always remove the lock, even if errors occurred
        if user_id in active_generation_tasks:
            del active_generation_tasks[user_id]
            
    return generated_recipes

@router.post("/", response_model=PreferenceResponse)
async def create_preference(
    preference: PreferenceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new preference for the current user
    """
    # Check if preference already exists
    db_preference = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if db_preference:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has preferences set up. Use PUT to update."
        )
    
    # Create new preference
    db_preference = UserPreference(
        user_id=current_user.id,
        dietary_restrictions=preference.dietary_restrictions,
        favorite_cuisines=preference.favorite_cuisines,
        cooking_skill_level=preference.cooking_skill_level,
        health_goals=preference.health_goals,
        allergies=preference.allergies
    )
    
    db.add(db_preference)
    db.commit()
    db.refresh(db_preference)
    
    # Generate initial recipes for the user in the background
    asyncio.create_task(generate_recipes_for_user(current_user.id, db_preference.id))
    
    # Convert the DB model to a dictionary and explicitly use the list properties
    response_data = {
        "user_id": db_preference.user_id,
        "dietary_restrictions": db_preference.dietary_restrictions_list,
        "favorite_cuisines": db_preference.favorite_cuisines_list,
        "cooking_skill_level": db_preference.cooking_skill_level,
        "health_goals": db_preference.health_goals_list,
        "allergies": db_preference.allergies_list
    }
    
    return response_data

@router.get("/", response_model=PreferenceResponse)
async def get_preference(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's preferences
    """
    db_preference = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if not db_preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found"
        )
    
    # Convert the DB model to a dictionary and explicitly use the list properties
    response_data = {
        "user_id": db_preference.user_id,
        "dietary_restrictions": db_preference.dietary_restrictions_list,
        "favorite_cuisines": db_preference.favorite_cuisines_list,
        "cooking_skill_level": db_preference.cooking_skill_level,
        "health_goals": db_preference.health_goals_list,
        "allergies": db_preference.allergies_list
    }
    
    return response_data

@router.put("/", response_model=PreferenceResponse)
async def update_preference(
    preference: PreferenceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's preferences
    """
    db_preference = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if not db_preference:
        # Create if not exists
        return await create_preference(preference, current_user, db)
    
    # Update preference
    db_preference.dietary_restrictions = ",".join(preference.dietary_restrictions)
    db_preference.favorite_cuisines = ",".join(preference.favorite_cuisines)
    db_preference.cooking_skill_level = preference.cooking_skill_level
    db_preference.health_goals = ",".join(preference.health_goals)
    db_preference.allergies = ",".join(preference.allergies)
    
    db.commit()
    db.refresh(db_preference)
    
    # Generate additional recipes based on updated preferences
    asyncio.create_task(generate_recipes_for_user(current_user.id, db_preference.id))
    
    # Convert the DB model to a dictionary and explicitly use the list properties
    response_data = {
        "user_id": db_preference.user_id,
        "dietary_restrictions": db_preference.dietary_restrictions_list,
        "favorite_cuisines": db_preference.favorite_cuisines_list,
        "cooking_skill_level": db_preference.cooking_skill_level,
        "health_goals": db_preference.health_goals_list,
        "allergies": db_preference.allergies_list
    }
    
    return response_data

class QuestionnaireData(BaseModel):
    dietary_restrictions: Optional[List[str]] = []
    favorite_cuisines: Optional[List[str]] = []
    cooking_skill_level: Optional[str] = "beginner"
    health_goals: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    additional_preferences: Optional[Dict[str, Any]] = {}

@router.post("/questionnaire", response_model=PreferenceResponse)
async def submit_questionnaire(
    questionnaire_data: QuestionnaireData,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Process a questionnaire response and update user preferences
    """
    logger.info(f"Questionnaire submission for user: {current_user.username}")
    logger.info(f"Questionnaire data: {questionnaire_data}")
    
    # Check if preference exists
    db_preference = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    
    is_new_preference = False
    if db_preference:
        # Update existing preference
        logger.info("Updating existing preferences")
        db_preference.dietary_restrictions = ",".join(questionnaire_data.dietary_restrictions)
        db_preference.favorite_cuisines = ",".join(questionnaire_data.favorite_cuisines)
        db_preference.cooking_skill_level = questionnaire_data.cooking_skill_level
        db_preference.health_goals = ",".join(questionnaire_data.health_goals)
        db_preference.allergies = ",".join(questionnaire_data.allergies)
    else:
        # Create new preference
        logger.info("Creating new preferences")
        is_new_preference = True
        db_preference = UserPreference(
            user_id=current_user.id,
            dietary_restrictions=questionnaire_data.dietary_restrictions,
            favorite_cuisines=questionnaire_data.favorite_cuisines,
            cooking_skill_level=questionnaire_data.cooking_skill_level,
            health_goals=questionnaire_data.health_goals,
            allergies=questionnaire_data.allergies
        )
        db.add(db_preference)
    
    db.commit()
    db.refresh(db_preference)
    logger.info(f"Preferences saved: {db_preference}")
    
    # Generate recipes based on questionnaire preferences
    # For new users, generate more initial recipes (8), for updates generate fewer (6)
    recipe_count =  6
    asyncio.create_task(generate_recipes_for_user(current_user.id, db_preference.id, count=recipe_count))
    
    # Convert the DB model to a dictionary and explicitly use the list properties
    response_data = {
        "user_id": db_preference.user_id,
        "dietary_restrictions": db_preference.dietary_restrictions_list,
        "favorite_cuisines": db_preference.favorite_cuisines_list,
        "cooking_skill_level": db_preference.cooking_skill_level,
        "health_goals": db_preference.health_goals_list,
        "allergies": db_preference.allergies_list
    }
    
    return response_data

@router.get("/recipe-generation-status")
async def get_recipe_generation_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the status of recipe generation for the current user
    """
    try:
        # Check if user has preferences
        user_preferences = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
        has_preferences = user_preferences is not None
        
        # Check if we have any recipes generated for this user
        from sqlalchemy.sql import text
        
        try:
            query = text("""
                SELECT COUNT(*) FROM recipes 
                WHERE generated_for_user_id = :user_id AND is_ai_generated = 1
            """)
            result = db.execute(query, {"user_id": current_user.id}).scalar()
            recipes_count = result or 0
        except Exception as e:
            logger.error(f"Error counting recipes: {str(e)}")
            recipes_count = 0
            
        # Check if a generation task is currently active
        is_generating = current_user.id in active_generation_tasks
        
        # Determine if generation is complete (either not generating or we have enough recipes)
        generation_complete = not is_generating and (recipes_count >= INITIAL_RECIPES_COUNT or not has_preferences)
        
        return {
            "is_generating": is_generating,
            "recipes_count": recipes_count,
            "has_preferences": has_preferences,
            "generation_complete": generation_complete
        }
    except Exception as e:
        logger.error(f"Error getting recipe generation status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recipe generation status: {str(e)}"
        ) 