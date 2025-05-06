import json
import logging
from typing import Dict, List, Optional, Any
import os
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.schemas.recipe import RecipeBrief, RecipeInDB, RecipeGenerationRequest

logger = logging.getLogger(__name__)

# OpenAI API credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

class RecipeGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            logger.warning("No OpenAI API key provided, recipe generation will fail")
    
    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, json.JSONDecodeError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_recipe(self, request: RecipeGenerationRequest) -> Optional[RecipeInDB]:
        """Generate a recipe using OpenAI API based on user preferences"""
        if not self.api_key:
            logger.error("OpenAI API key not provided")
            return None
        
        try:
            # Construct the prompt for recipe generation
            prompt = self._build_recipe_prompt(request)
            
            # Make API call to OpenAI
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": "gpt-4-turbo", # Can be configured based on needs
                "messages": [
                    {"role": "system", "content": "You are a professional chef and culinary expert who creates delicious recipes."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(OPENAI_API_URL, json=payload, headers=headers, timeout=60.0)
                response.raise_for_status()
                response_data = response.json()
            
            # Extract and process the recipe from the response
            recipe_text = response_data['choices'][0]['message']['content']
            parsed_recipe = self._parse_recipe(recipe_text, request)
            
            if not parsed_recipe:
                logger.error(f"Failed to parse recipe: {recipe_text}")
                return None
                
            return parsed_recipe
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during recipe generation: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error during recipe generation: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during recipe generation: {e}")
            return None
    
    def _build_recipe_prompt(self, request: RecipeGenerationRequest) -> str:
        """Build a prompt for recipe generation based on user preferences"""
        preferences = []
        
        if request.cuisine_type:
            preferences.append(f"cuisine type: {request.cuisine_type}")
        
        if request.meal_type:
            preferences.append(f"meal type: {request.meal_type}")
        
        if request.difficulty:
            preferences.append(f"difficulty level: {request.difficulty}")
        
        # Add dietary restrictions
        restrictions = []
        if request.vegetarian:
            restrictions.append("vegetarian")
        if request.vegan:
            restrictions.append("vegan")
        if request.gluten_free:
            restrictions.append("gluten-free")
        if request.dairy_free:
            restrictions.append("dairy-free")
        if request.nut_free:
            restrictions.append("nut-free")
        
        if restrictions:
            preferences.append(f"dietary restrictions: {', '.join(restrictions)}")
        
        if request.spicy_level is not None:
            spicy_levels = ["not spicy", "mildly spicy", "medium spicy", "very spicy", "extremely spicy"]
            if 0 <= request.spicy_level <= 4:
                preferences.append(f"spiciness: {spicy_levels[request.spicy_level]}")
        
        if request.max_prep_time:
            preferences.append(f"preparation time: maximum {request.max_prep_time} minutes")
        
        if request.max_cook_time:
            preferences.append(f"cooking time: maximum {request.max_cook_time} minutes")
        
        if request.additional_preferences:
            preferences.append(f"additional preferences: {request.additional_preferences}")
        
        preferences_str = "; ".join(preferences)
        
        prompt = f"""Create a delicious recipe with the following preferences: {preferences_str}.

Please format your response as a JSON object with the following structure:
{{
    "title": "Recipe Title",
    "description": "Brief description of the recipe",
    "cuisine_type": "Cuisine type",
    "meal_type": "Meal type (breakfast, lunch, dinner, snack, dessert)",
    "prep_time": prep time in minutes (integer),
    "cook_time": cook time in minutes (integer),
    "difficulty": "easy, medium, or hard",
    "vegetarian": boolean,
    "vegan": boolean,
    "gluten_free": boolean,
    "dairy_free": boolean,
    "nut_free": boolean,
    "spicy_level": integer from 0-4,
    "ingredients": ["ingredient 1 with quantity", "ingredient 2 with quantity", ...],
    "instructions": ["step 1", "step 2", ...]
}}

Ensure all fields are present and properly formatted.
"""
        return prompt
    
    def _parse_recipe(self, recipe_text: str, request: RecipeGenerationRequest) -> Optional[RecipeInDB]:
        """Parse the recipe from the OpenAI response text"""
        try:
            # Extract JSON from the response
            json_start = recipe_text.find("{")
            json_end = recipe_text.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("Could not find JSON in response")
                return None
                
            recipe_json = recipe_text[json_start:json_end]
            recipe_data = json.loads(recipe_json)
            
            # Create RecipeInDB object
            recipe = RecipeInDB(
                id=None,  # ID will be assigned when saved to database
                title=recipe_data.get("title", "Generated Recipe"),
                description=recipe_data.get("description", ""),
                cuisine_type=recipe_data.get("cuisine_type", request.cuisine_type or "General"),
                meal_type=recipe_data.get("meal_type", request.meal_type or "Main Course"),
                prep_time=recipe_data.get("prep_time", request.max_prep_time or 30),
                cook_time=recipe_data.get("cook_time", request.max_cook_time or 30),
                difficulty=recipe_data.get("difficulty", request.difficulty or "medium"),
                vegetarian=recipe_data.get("vegetarian", request.vegetarian or False),
                vegan=recipe_data.get("vegan", request.vegan or False),
                gluten_free=recipe_data.get("gluten_free", request.gluten_free or False),
                dairy_free=recipe_data.get("dairy_free", request.dairy_free or False),
                nut_free=recipe_data.get("nut_free", request.nut_free or False),
                spicy_level=recipe_data.get("spicy_level", request.spicy_level or 0),
                ingredients=recipe_data.get("ingredients", []),
                instructions=recipe_data.get("instructions", [])
            )
            
            return recipe
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse recipe JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing recipe: {e}")
            return None 