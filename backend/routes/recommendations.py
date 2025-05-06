from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import json
from json import JSONDecodeError
from sqlalchemy.sql import text

from database.database import get_db
from models import User, Recipe, UserPreference
from schemas.recipe import RecipeGenerationRequest, RecipeSimilarityRequest, RecipeInDB, RecipeBrief, RecipeResponse
from utils.openai_helper import generate_recipe, get_cuisine_recommendations
from utils.recommendation import RecipeRecommender
from utils.auth import get_current_user

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize recommendation engine
recipe_recommender = None

@router.post("/generate", response_model=RecipeInDB)
async def generate_recipe_endpoint(
    request: RecipeGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a personalized recipe using OpenAI based on user preferences
    """
    try:
        # Map request to parameters expected by generate_recipe function
        cuisine_preferences = request.cuisine_preferences if hasattr(request, "cuisine_preferences") else ([request.cuisine] if request.cuisine else [])
        
        # Handle different field names between frontend and backend
        meal_type = request.meal_type if hasattr(request, "meal_type") else request.dish_type or "dinner"
        skill_level = request.skill_level if hasattr(request, "skill_level") else request.difficulty or "medium"
        max_cooking_time = request.max_cooking_time if hasattr(request, "max_cooking_time") else request.cooking_time or 60
        
        # Extract flavor preferences or use default
        flavor_preferences = request.flavor_preferences if hasattr(request, "flavor_preferences") else {"medium": 3}
        
        # Extract ingredients to include
        ingredients_to_include = request.ingredients_to_include if hasattr(request, "ingredients_to_include") else request.ingredients
        
        # Extract allergies and health goals (new)
        allergies = request.allergies or []
        health_goals = request.health_goals or []
        
        # Generate recipe via OpenAI
        recipe_data = await generate_recipe(
            cuisine_preferences=cuisine_preferences,
            dietary_restrictions=request.dietary_restrictions or [],
            flavor_preferences=flavor_preferences,
            meal_type=meal_type,
            skill_level=skill_level,
            max_cooking_time=max_cooking_time,
            ingredients_to_include=ingredients_to_include,
            allergies=allergies, # Pass allergies
            health_goals=health_goals # Pass health goals
        )
        
        # Process recipe data to ensure correct types
        cuisine = recipe_data.get("cuisine", "")
        if isinstance(cuisine, list):
            cuisine = ", ".join(cuisine)
            
        # Get ingredients either as a list or from JSON string
        ingredients = recipe_data.get("ingredients", "[]")
        if isinstance(ingredients, str):
            try:
                # Try to parse as JSON
                ingredients_list = json.loads(ingredients)
            except json.JSONDecodeError:
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
        dietary_restrictions = recipe_data.get("dietary_restrictions", "[]")
        if isinstance(dietary_restrictions, str):
            try:
                dietary_restrictions_list = json.loads(dietary_restrictions)
            except json.JSONDecodeError:
                dietary_restrictions_list = [item.strip() for item in dietary_restrictions.replace('\n', ',').split(',') if item.strip()]
        else:
            dietary_restrictions_list = dietary_restrictions if dietary_restrictions else []
            
        # Store dietary restrictions as JSON string
        dietary_restrictions_json = json.dumps(dietary_restrictions_list)
        
        # Get tags
        tags = recipe_data.get("tags", [])
        if isinstance(tags, str):
            try:
                tags_list = json.loads(tags)
            except json.JSONDecodeError:
                tags_list = [item.strip() for item in tags.replace('\n', ',').split(',') if item.strip()]
        else:
            tags_list = tags if tags else []
            
        # Store tags as JSON string
        tags_json = json.dumps(tags_list)
        
        # Get time values with proper defaults
        prep_time = recipe_data.get("prep_time", 0)
        cook_time = recipe_data.get("cook_time", 0)
        total_time = recipe_data.get("total_time", 0)
        
        # If total time is not provided, calculate it
        if total_time == 0:
            total_time = prep_time + cook_time
        
        # Create a new recipe in the database
        db_recipe = Recipe(
            title=recipe_data.get("title", ""),
            description=recipe_data.get("description", ""),
            ingredients=ingredients_json,
            instructions=instructions_json,
            cuisine=cuisine,
            prep_time=prep_time,
            cooking_time=cook_time,
            total_time=total_time,
            difficulty=recipe_data.get("difficulty", "medium"),
            dietary_restrictions=dietary_restrictions_json,
            tags=tags_json,
            is_ai_generated=True,
            generated_for_user_id=current_user.id
        )
        
        db.add(db_recipe)
        db.commit()
        db.refresh(db_recipe)
        
        # Convert strings back to lists for API response
        recipe_dict = {
            "id": db_recipe.id,
            "title": db_recipe.title,
            "description": db_recipe.description,
            "ingredients": db_recipe.ingredients_list,
            "instructions": db_recipe.instructions_list,
            "prep_time": db_recipe.prep_time,
            "cooking_time": db_recipe.cooking_time,
            "total_time": db_recipe.total_time,
            "difficulty": db_recipe.difficulty,
            "cuisine": db_recipe.cuisine,
            "dietary_restrictions": db_recipe.dietary_restrictions_list,
            "tags": db_recipe.tags_list,
            "is_ai_generated": db_recipe.is_ai_generated,
            "generated_for_user_id": db_recipe.generated_for_user_id,
            "vegetarian": db_recipe.vegetarian if hasattr(db_recipe, "vegetarian") else False,
            "vegan": db_recipe.vegan if hasattr(db_recipe, "vegan") else False,
            "gluten_free": db_recipe.gluten_free if hasattr(db_recipe, "gluten_free") else False,
            "dairy_free": db_recipe.dairy_free if hasattr(db_recipe, "dairy_free") else False,
            "nut_free": db_recipe.nut_free if hasattr(db_recipe, "nut_free") else False,
            "spicy_level": db_recipe.spicy_level if hasattr(db_recipe, "spicy_level") else 0,
            "image_url": db_recipe.image_url if hasattr(db_recipe, "image_url") else None,
        }
        
        return recipe_dict
    
    except Exception as e:
        logger.error(f"Error generating recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recipe: {str(e)}"
        )

@router.get("/user", response_model=List[RecipeBrief])
async def get_user_recommendations(
    limit: int = Query(5, ge=1, le=20),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized recipe recommendations based on user preferences using OpenAI
    """
    try:
        # First, get the user's preferences
        user_preferences = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
        
        logger.info(f"Getting recommendations for user {current_user.id}, limit={limit}, offset={offset}")
        
        # If user has no preferences, return general recipes
        if not user_preferences:
            logger.info(f"No preferences found for user {current_user.id}, returning general recipes")
            
            # Use a raw SQL query to avoid columns that might not exist yet
            query = text("""
                SELECT id, title, description, ingredients, instructions, 
                       cooking_time, difficulty, cuisine, dietary_restrictions,
                       is_ai_generated, generated_for_user_id
                FROM recipes
                ORDER BY id DESC
                LIMIT :limit OFFSET :offset
            """)
            
            result = db.execute(query, {"limit": limit, "offset": offset})
            
            # Convert to dictionaries
            db_recipes = []
            for row in result:
                recipe_dict = {
                    "id": row.id,
                    "title": row.title,
                    "description": row.description,
                    "ingredients": row.ingredients,
                    "instructions": row.instructions,
                    "cooking_time": row.cooking_time,
                    "difficulty": row.difficulty,
                    "cuisine": row.cuisine,
                    "dietary_restrictions": row.dietary_restrictions,
                    "is_ai_generated": row.is_ai_generated,
                    "generated_for_user_id": row.generated_for_user_id,
                    # Add default values for new fields
                    "prep_time": 0,
                    "total_time": row.cooking_time,
                    "tags": "[]"
                }
                db_recipes.append(recipe_dict)
            
            if not db_recipes:
                logger.warning("No general recipes found in database")
                return []
                
            # Convert recipes to use list properties
            recipes = []
            for recipe in db_recipes:
                # Parse JSON strings to lists
                try:
                    ingredients_list = json.loads(recipe["ingredients"]) if recipe["ingredients"] else []
                except:
                    ingredients_list = []
                    
                try:
                    instructions_list = json.loads(recipe["instructions"]) if recipe["instructions"] else []
                except:
                    instructions_list = []
                    
                try:
                    # Fix: Ensure dietary_restrictions is properly parsed as a list
                    if recipe["dietary_restrictions"] == "[]" or not recipe["dietary_restrictions"]:
                        dietary_restrictions_list = []
                    else:
                        dietary_restrictions_list = json.loads(recipe["dietary_restrictions"])
                except:
                    dietary_restrictions_list = []
                
                recipes.append({
                    "id": recipe["id"],
                    "title": recipe["title"],
                    "description": recipe["description"],
                    "ingredients": ingredients_list,
                    "instructions": instructions_list,
                    "prep_time": recipe.get("prep_time", 0),
                    "cooking_time": recipe["cooking_time"],
                    "total_time": recipe.get("total_time", recipe["cooking_time"]),
                    "difficulty": recipe["difficulty"],
                    "cuisine": recipe["cuisine"],
                    "dietary_restrictions": dietary_restrictions_list,
                    "is_ai_generated": recipe["is_ai_generated"],
                    "generated_for_user_id": recipe["generated_for_user_id"],
                    "tags": []
                })
            
            logger.info(f"Returning {len(recipes)} general recipes")
            return recipes
        
        # Otherwise, use preferences to generate personalized recommendations
        logger.info(f"Generating personalized recommendations for user {current_user.id} with preferences id={user_preferences.id}")
        
        # First, check if we have enough existing AI-generated recipes for this user
        query = text("""
            SELECT id, title, description, ingredients, instructions, 
                   cooking_time, difficulty, cuisine, dietary_restrictions,
                   is_ai_generated, generated_for_user_id
            FROM recipes
            WHERE generated_for_user_id = :user_id AND is_ai_generated = 1
            ORDER BY id DESC
            LIMIT :limit OFFSET :offset
        """)
        
        result = db.execute(query, {"user_id": current_user.id, "limit": limit, "offset": offset})
        
        # Convert to dictionaries
        existing_recipes = []
        for row in result:
            recipe_dict = {
                "id": row.id,
                "title": row.title,
                "description": row.description,
                "ingredients": row.ingredients,
                "instructions": row.instructions,
                "cooking_time": row.cooking_time,
                "difficulty": row.difficulty,
                "cuisine": row.cuisine,
                "dietary_restrictions": row.dietary_restrictions,
                "is_ai_generated": row.is_ai_generated,
                "generated_for_user_id": row.generated_for_user_id,
                # Add default values for new fields
                "prep_time": 0,
                "total_time": row.cooking_time,
                "tags": "[]"
            }
            existing_recipes.append(recipe_dict)
        
        logger.info(f"Found {len(existing_recipes)} existing AI-generated recipes for user {current_user.id}")
        
        all_recipes = []
        
        # If we have enough recipes, use those
        if len(existing_recipes) >= limit:
            logger.info(f"Using {len(existing_recipes)} existing recipes (limit={limit})")
            
            # Format them properly
            for recipe in existing_recipes:
                try:
                    ingredients_list = json.loads(recipe["ingredients"]) if recipe["ingredients"] else []
                except:
                    ingredients_list = []
                    
                try:
                    instructions_list = json.loads(recipe["instructions"]) if recipe["instructions"] else []
                except:
                    instructions_list = []
                    
                try:
                    # Fix: Ensure dietary_restrictions is properly parsed as a list 
                    if recipe["dietary_restrictions"] == "[]" or not recipe["dietary_restrictions"]:
                        dietary_restrictions_list = []
                    else:
                        dietary_restrictions_list = json.loads(recipe["dietary_restrictions"])
                except:
                    dietary_restrictions_list = []
                
                all_recipes.append({
                    "id": recipe["id"],
                    "title": recipe["title"],
                    "description": recipe["description"],
                    "ingredients": ingredients_list,
                    "instructions": instructions_list,
                    "prep_time": recipe.get("prep_time", 0),
                    "cooking_time": recipe["cooking_time"],
                    "total_time": recipe.get("total_time", recipe["cooking_time"]),
                    "difficulty": recipe["difficulty"],
                    "cuisine": recipe["cuisine"],
                    "dietary_restrictions": dietary_restrictions_list,
                    "is_ai_generated": recipe["is_ai_generated"],
                    "generated_for_user_id": recipe["generated_for_user_id"],
                    "tags": []
                })
                
            logger.info("Returning existing recipes")
            return all_recipes[:limit]
        
        # If we need more recipes, generate them
        needed_recipes = limit - len(existing_recipes)
        logger.info(f"Need to generate {needed_recipes} new recipes")
        
        # Extract user preferences
        cuisines = user_preferences.favorite_cuisines_list
        dietary_restrictions = []
        
        if user_preferences.vegetarian:
            dietary_restrictions.append("vegetarian")
        if user_preferences.vegan:
            dietary_restrictions.append("vegan")
        if user_preferences.gluten_free:
            dietary_restrictions.append("gluten-free")
        if user_preferences.dairy_free:
            dietary_restrictions.append("dairy-free")
        if user_preferences.nut_free:
            dietary_restrictions.append("nut-free")
            
        # Add allergies to dietary restrictions
        if user_preferences.allergies_list:
            dietary_restrictions.extend([f"no {allergy}" for allergy in user_preferences.allergies_list])
        
        logger.debug(f"User cuisines: {cuisines}")
        logger.debug(f"User dietary restrictions: {dietary_restrictions}")
        
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
        
        logger.debug(f"User meal types: {meal_types}")
            
        # Set cooking skill level
        skill_level = user_preferences.cooking_skill_level or "medium"
        
        # Set max cooking time
        max_cooking_time = user_preferences.cooking_time_max or 60
        
        # Generate new recipes one by one
        new_recipes = []
        generated_titles = set()  # Track titles to avoid duplicates
        
        # Add existing recipe titles to generated_titles to avoid duplicates with existing recipes
        for recipe in existing_recipes:
            generated_titles.add(recipe["title"])
            
        logger.debug(f"Existing recipe titles in DB: {generated_titles}")
        
        # Track failed attempts to avoid infinite loops
        failure_count = 0
        max_failures = 5
        
        logger.info(f"Starting generation of {needed_recipes} recipes")
        
        # Import the fallback recipe generator
        from utils.openai_helper import generate_fallback_recipe
        
        for i in range(needed_recipes):
            try:
                # If we've had too many failures, use fallback recipes directly
                if failure_count >= max_failures:
                    # Select a cuisine and meal type
                    cuisine = cuisines[i % len(cuisines)] if cuisines else None
                    meal_type = meal_types[i % len(meal_types)] if meal_types else "dinner"
                    
                    logger.warning(f"Using fallback recipe after {failure_count} failures - cuisine: {cuisine}, meal type: {meal_type}")
                    
                    # Generate a fallback recipe
                    recipe_data = generate_fallback_recipe(
                        cuisine_preferences=[cuisine] if cuisine else [],
                        meal_type=meal_type
                    )
                    
                    logger.debug(f"Fallback recipe generated: {recipe_data.get('title', 'Untitled')}")
                    
                    # Create a RecipeGenerationRequest-like object
                    class MockRequest:
                        def __init__(self, **kwargs):
                            for key, value in kwargs.items():
                                setattr(self, key, value)
                    
                    # Create a recipe in the database
                    mock_request = MockRequest(
                        cuisine=recipe_data.get("cuisine_type", cuisine),
                        dietary_restrictions=recipe_data.get("dietary_restrictions", []),
                        dish_type=recipe_data.get("meal_type", meal_type),
                        difficulty=recipe_data.get("difficulty", skill_level),
                        cooking_time=recipe_data.get("cook_time", max_cooking_time),
                        ingredients=recipe_data.get("ingredients", [])
                    )
                    
                    # Process the recipe
                    db_recipe = Recipe(
                        title=recipe_data.get("title", ""),
                        description=recipe_data.get("description", ""),
                        ingredients=json.dumps(recipe_data.get("ingredients", [])),
                        instructions=json.dumps(recipe_data.get("instructions", [])),
                        cuisine=recipe_data.get("cuisine_type", cuisine),
                        prep_time=recipe_data.get("prep_time", 10),
                        cooking_time=recipe_data.get("cook_time", 30),
                        total_time=recipe_data.get("total_time", 40),
                        difficulty=recipe_data.get("difficulty", "medium"),
                        dietary_restrictions=json.dumps(recipe_data.get("dietary_restrictions", [])),
                        is_ai_generated=True,
                        generated_for_user_id=current_user.id
                    )
                    
                    db.add(db_recipe)
                    db.commit()
                    db.refresh(db_recipe)
                    
                    # Create response format
                    recipe_response = {
                        "id": db_recipe.id,
                        "title": db_recipe.title,
                        "description": db_recipe.description,
                        "ingredients": db_recipe.ingredients_list,
                        "instructions": db_recipe.instructions_list,
                        "prep_time": db_recipe.prep_time,
                        "cooking_time": db_recipe.cooking_time,
                        "total_time": db_recipe.total_time,
                        "difficulty": db_recipe.difficulty,
                        "cuisine": db_recipe.cuisine,
                        "dietary_restrictions": db_recipe.dietary_restrictions_list,
                        "is_ai_generated": db_recipe.is_ai_generated,
                        "generated_for_user_id": db_recipe.generated_for_user_id,
                        "tags": db_recipe.tags_list
                    }
                    
                    new_recipes.append(recipe_response)
                    generated_titles.add(recipe_data.get("title", ""))
                    logger.info(f"Generated fallback recipe: {recipe_data.get('title')}")
                    continue
                
                # Select a random cuisine and meal type if available
                cuisine = cuisines[i % len(cuisines)] if cuisines else None
                meal_type = meal_types[i % len(meal_types)] if meal_types else "dinner"
                
                logger.debug(f"Attempting recipe generation #{i+1}/{needed_recipes}: cuisine={cuisine}, meal_type={meal_type}")
                
                # Create request for recipe generation using the correct fields
                recipe_request = RecipeGenerationRequest(
                    cuisine_preferences=[cuisine] if cuisine else [], # Use the prioritized list field
                    meal_type=meal_type, # Use the prioritized field
                    skill_level=skill_level, # Use the prioritized field
                    max_cooking_time=max_cooking_time, # Use the prioritized field
                    flavor_preferences=flavor_preferences, # Pass flavor prefs
                    dietary_restrictions=dietary_restrictions, # Pass dietary restrictions
                    ingredients_to_include=[], # No specific ingredients required for this context
                    ingredients_to_avoid=[] # No specific ingredients to avoid for this context
                )
                
                # Generate the recipe
                recipe_data = await generate_recipe_endpoint(
                    request=recipe_request,
                    current_user=current_user,
                    db=db
                )
                
                # Check for duplicate titles
                if recipe_data.get("title") in generated_titles:
                    logger.warning(f"Detected duplicate recipe title: '{recipe_data.get('title')}', retry attempt #{failure_count+1}")
                    failure_count += 1
                    
                    # Try different cuisine or meal type
                    continue
                
                # Add title to set of generated titles
                generated_titles.add(recipe_data.get("title"))
                
                new_recipes.append(recipe_data)
                logger.info(f"Successfully generated new recipe: {recipe_data.get('title')}")
                
            except Exception as e:
                logger.error(f"Error generating recommendation {i+1}: {str(e)}")
                failure_count += 1
                logger.warning(f"Generation failure #{failure_count}/{max_failures}")
                continue
        
        # --- Logic Change: Only return NEW recipes if any were generated --- 
        if new_recipes: 
            logger.info(f"Returning {len(new_recipes)} newly generated recipes (limit was {limit})")
            # Note: We return all generated recipes, even if fewer than the limit, as requested.
            # If you strictly wanted only 'limit' number even if more were generated, use new_recipes[:limit]
            return new_recipes 
        else: 
            # Only executes if needed_recipes was 0 or generation failed completely for all needed recipes
            # Combine existing and new recipes, prioritizing new ones (new_recipes will be empty here)
            # Convert existing recipes (raw dicts from DB) to the same format as new_recipes (dicts from endpoint)
            formatted_existing_recipes = []
            for recipe in existing_recipes:
                try:
                    ingredients_list = json.loads(recipe["ingredients"]) if recipe["ingredients"] else []
                except: ingredients_list = []
                try:
                    instructions_list = json.loads(recipe["instructions"]) if recipe["instructions"] else []
                except: instructions_list = []
                try:
                    if recipe["dietary_restrictions"] == "[]" or not recipe["dietary_restrictions"]:
                        dietary_restrictions_list = []
                    else:
                        dietary_restrictions_list = json.loads(recipe["dietary_restrictions"])
                except: dietary_restrictions_list = []
                try:
                    tags_raw = recipe.get("tags", "[]")
                    if isinstance(tags_raw, str) and tags_raw and tags_raw != "[]": tags_list = json.loads(tags_raw)
                    elif isinstance(tags_raw, list): tags_list = tags_raw
                    else: tags_list = []
                except: tags_list = []
                    
                formatted_existing_recipes.append({
                    "id": recipe.get("id"),
                    "title": recipe.get("title"),
                    "description": recipe.get("description"),
                    "ingredients": ingredients_list,
                    "instructions": instructions_list,
                    "prep_time": recipe.get("prep_time", 0),
                    "cooking_time": recipe.get("cooking_time", 0),
                    "total_time": recipe.get("total_time", recipe.get("prep_time", 0) + recipe.get("cooking_time", 0)),
                    "difficulty": recipe.get("difficulty", "medium"),
                    "cuisine": recipe.get("cuisine", ""),
                    "dietary_restrictions": dietary_restrictions_list,
                    "is_ai_generated": recipe.get("is_ai_generated", False),
                    "generated_for_user_id": recipe.get("generated_for_user_id"),
                    "tags": tags_list
                })
            
            # Combine new recipes first (will be empty), then the formatted existing ones
            all_recipes_combined = new_recipes + formatted_existing_recipes
            
            logger.info(f"No new recipes were generated or all generations failed. Returning {len(formatted_existing_recipes)} existing recipes (limit was {limit})")
             
            logger.info(f"Returning {min(len(all_recipes_combined), limit)} recipes to user {current_user.id}")
            return all_recipes_combined[:limit]
    
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )

@router.post("/similar", response_model=List[RecipeBrief])
async def find_similar_recipes(
    request: RecipeSimilarityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return a selection of recipes (currently returns random recipes instead of similar ones)
    """
    try:
        # Get a selection of recipes instead of using the recommender
        query = db.query(Recipe)
        
        # Basic filtering if a recipe ID is provided
        if request.recipe_id:
            query = query.filter(Recipe.id != request.recipe_id)  # Exclude the reference recipe
            
        # Limit the number of recipes returned
        db_recipes = query.limit(10).all()
        
        if len(db_recipes) == 0:
            return []
        
        # Convert recipes to use list properties
        recipes = []
        for recipe in db_recipes:
            recipes.append({
                "id": recipe.id,
                "title": recipe.title,
                "description": recipe.description,
                "ingredients": recipe.ingredients_list,
                "instructions": recipe.instructions_list,
                "cooking_time": recipe.cooking_time,
                "difficulty": recipe.difficulty,
                "cuisine": recipe.cuisine,
                "dietary_restrictions": recipe.dietary_restrictions_list,
                "is_ai_generated": recipe.is_ai_generated,
                "generated_for_user_id": recipe.generated_for_user_id
            })
        
        return recipes
    
    except Exception as e:
        logger.error(f"Error finding similar recipes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar recipes: {str(e)}"
        )

@router.get("/recipes", response_model=List[RecipeResponse])
async def get_recipes(
    search: Optional[str] = None,
    cuisine: Optional[str] = None,
    difficulty: Optional[str] = None,
    dietary_restriction: Optional[str] = None,
    max_cooking_time: Optional[int] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get recipes with optional filtering.
    """
    query = db.query(Recipe)
    
    # Apply filters if provided
    if search:
        query = query.filter(Recipe.title.ilike(f"%{search}%") | Recipe.description.ilike(f"%{search}%"))
    
    if cuisine:
        query = query.filter(Recipe.cuisine.ilike(f"%{cuisine}%"))
    
    if difficulty:
        query = query.filter(Recipe.difficulty == difficulty)
    
    if dietary_restriction:
        query = query.filter(Recipe.dietary_restrictions.ilike(f"%{dietary_restriction}%"))
    
    if max_cooking_time:
        query = query.filter(Recipe.cooking_time <= max_cooking_time)
    
    # Apply pagination
    db_recipes = query.offset(offset).limit(limit).all()
    
    # Return empty list if no recipes found
    if not db_recipes:
        return []
    
    # Convert recipes to use list properties
    recipes = []
    for recipe in db_recipes:
        recipes.append({
            "id": recipe.id,
            "title": recipe.title,
            "description": recipe.description,
            "ingredients": recipe.ingredients_list,
            "instructions": recipe.instructions_list,
            "cooking_time": recipe.cooking_time,
            "difficulty": recipe.difficulty,
            "cuisine": recipe.cuisine,
            "dietary_restrictions": recipe.dietary_restrictions_list,
            "is_ai_generated": recipe.is_ai_generated,
            "generated_for_user_id": recipe.generated_for_user_id
        })
    
    return recipes

@router.get("/featured", response_model=List[RecipeResponse])
async def get_featured_recipes(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get featured recipes regardless of user preferences.
    These are shown to all users as general recommendations.
    """
    try:
        # Use a raw SQL query to avoid columns that might not exist yet
        query = text("""
            SELECT id, title, description, ingredients, instructions, 
                   cooking_time, difficulty, cuisine, dietary_restrictions,
                   is_ai_generated, generated_for_user_id
            FROM recipes
            WHERE is_ai_generated = 0
            ORDER BY id DESC
            LIMIT :limit OFFSET 0
        """)
        
        result = db.execute(query, {"limit": limit})
        
        # Convert to dictionaries
        db_recipes = []
        for row in result:
            recipe_dict = {
                "id": row.id,
                "title": row.title,
                "description": row.description,
                "ingredients": row.ingredients,
                "instructions": row.instructions,
                "cooking_time": row.cooking_time,
                "difficulty": row.difficulty,
                "cuisine": row.cuisine,
                "dietary_restrictions": row.dietary_restrictions,
                "is_ai_generated": row.is_ai_generated,
                "generated_for_user_id": row.generated_for_user_id,
                # Add default values for new fields
                "prep_time": 0,
                "total_time": row.cooking_time,
                "tags": "[]"
            }
            db_recipes.append(recipe_dict)
        
        # Return empty list if no recipes found
        if not db_recipes:
            return []
        
        # Convert recipes to use list properties
        featured_recipes = []
        for recipe in db_recipes:
            # Parse JSON strings to lists
            try:
                ingredients_list = json.loads(recipe["ingredients"]) if recipe["ingredients"] else []
            except:
                ingredients_list = []
                
            try:
                instructions_list = json.loads(recipe["instructions"]) if recipe["instructions"] else []
            except:
                instructions_list = []
                
            try:
                dietary_restrictions_list = json.loads(recipe["dietary_restrictions"]) if recipe["dietary_restrictions"] else []
            except:
                dietary_restrictions_list = []
            
            featured_recipes.append({
                "id": recipe["id"],
                "title": recipe["title"],
                "description": recipe["description"],
                "ingredients": ingredients_list,
                "instructions": instructions_list,
                "prep_time": recipe.get("prep_time", 0),
                "cooking_time": recipe["cooking_time"],
                "total_time": recipe.get("total_time", recipe["cooking_time"]),
                "difficulty": recipe["difficulty"],
                "cuisine": recipe["cuisine"],
                "dietary_restrictions": dietary_restrictions_list,
                "is_ai_generated": recipe["is_ai_generated"],
                "generated_for_user_id": recipe["generated_for_user_id"],
                "tags": []
            })
        
        return featured_recipes
    except Exception as e:
        logger.error(f"Error getting featured recipes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get featured recipes: {str(e)}"
        )

@router.post("/explore")
async def explore_cuisines(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Explore cuisines and dishes based on a natural language query using OpenAI.
    
    Example: "I want to eat biryani" will return similar dishes with their details.
    """
    try:
        # Parse the request body
        body = await request.json()
        query = body.get("query", "")
        limit = body.get("limit", 5)
        
        # Validate input
        if not query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query is required"
            )
            
        # Ensure limit is reasonable
        if limit < 1:
            limit = 3
        elif limit > 10:
            limit = 10
            
        logger.info(f"Exploring cuisines with query: '{query}', limit: {limit}")
        
        # Call OpenAI to get cuisine recommendations
        recommendations = await get_cuisine_recommendations(query, limit)
        
        # Log the results
        logger.info(f"Found {len(recommendations)} cuisine recommendations")
        
        # Return empty list if no recommendations
        if not recommendations:
            logger.warning("No recommendations found, returning empty list")
            return []
            
        return recommendations
    except JSONDecodeError:
        logger.error("Invalid JSON in request body")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in request body"
        )
    except Exception as e:
        logger.error(f"Error exploring cuisines: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explore cuisines: {str(e)}"
        ) 