import os
import json
import openai
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any, Optional
import re
import ast  # Add ast module for literal_eval
import random

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_recipe(
    cuisine_preferences: List[str],
    dietary_restrictions: List[str],
    flavor_preferences: Dict[str, int],
    meal_type: str,
    skill_level: str,
    max_cooking_time: int,
    ingredients_to_include: Optional[List[str]] = None,
    ingredients_to_avoid: Optional[List[str]] = None,
    allergies: Optional[List[str]] = None,
    health_goals: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a recipe using OpenAI based on user preferences
    """
    try:
        logger.info(f"Generating recipe with OpenAI - cuisine={cuisine_preferences}, meal_type={meal_type}, restrictions={dietary_restrictions}, allergies={allergies}, health_goals={health_goals}")
        
        # Construct the prompt based on user preferences
        prompt = construct_recipe_prompt(
            cuisine_preferences,
            dietary_restrictions,
            flavor_preferences,
            meal_type,
            skill_level,
            max_cooking_time,
            ingredients_to_include,
            ingredients_to_avoid,
            allergies,
            health_goals
        )
        
        # Log the full prompt being sent to OpenAI
        logger.debug(f"--- OpenAI Recipe Prompt ---\n{prompt}\n--- End Prompt ---")
        
        # Call OpenAI API asynchronously
        logger.debug(f"Calling OpenAI API with temperature=0.8, meal_type={meal_type}")
        response = await openai.ChatCompletion.acreate(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional chef who specializes in creating personalized recipes based on user preferences. Your responses should be structured as valid JSON objects."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.8  # Increased from 0.7 to encourage more variety
        )
        
        # Process response
        recipe_json = extract_json_from_response(response.choices[0].message.content)
        
        logger.debug(f"OpenAI generated recipe: '{recipe_json.get('title', 'Untitled')}'")
        
        # Validate recipe title to ensure it's not a repetition
        original_title = recipe_json.get("title", "")
        
        # Check for common repeated recipes
        common_repeats = ["mushroom risotto", "margherita pizza", "tomato spaghetti", "chicken curry"]
        if original_title.lower() in common_repeats or any(repeat in original_title.lower() for repeat in common_repeats):
            logger.warning(f"Detected common repeated recipe: '{original_title}'")
            
            # If we get a common dish again, add a random suffix to introduce some variety
            import random
            cuisine_type = cuisine_preferences[0] if cuisine_preferences else "Fusion"
            variations = [
                f"{cuisine_type} Inspired Dish", 
                "Seasonal Special", 
                "Chef's Creation", 
                "Flavor Fusion", 
                "Signature Dish",
                f"{cuisine_type} Twist",
                "House Special",
                "Premium Version",
                "Gourmet Edition"
            ]
            new_title = f"{random.choice(variations)} - {original_title}"
            recipe_json["title"] = new_title
            logger.info(f"Modified repetitive recipe title: '{original_title}' → '{new_title}'")
        
        return recipe_json
        
    except Exception as e:
        logger.error(f"Error generating recipe: {str(e)}")
        logger.warning("Falling back to local recipe generation")
        # Provide a fallback recipe instead of throwing an exception
        return generate_fallback_recipe(cuisine_preferences, meal_type)

def construct_recipe_prompt(
    cuisine_preferences: List[str],
    dietary_restrictions: List[str],
    flavor_preferences: Dict[str, int],
    meal_type: str,
    skill_level: str,
    max_cooking_time: int,
    ingredients_to_include: Optional[List[str]] = None,
    ingredients_to_avoid: Optional[List[str]] = None,
    allergies: Optional[List[str]] = None,
    health_goals: Optional[List[str]] = None
) -> str:
    """
    Construct the prompt for recipe generation
    """
    prompt = "Create a detailed recipe with the following specifications:\n\n"
    
    # Add cuisine preferences with emphasis
    if cuisine_preferences:
        prompt += f"CUISINE PREFERENCES (VERY IMPORTANT): {', '.join(cuisine_preferences)}\n"
        prompt += "Please ensure the recipe strongly reflects these cuisines in both ingredients and preparation.\n\n"
    
    # Add dietary restrictions with emphasis
    if dietary_restrictions:
        prompt += f"DIETARY RESTRICTIONS (STRICTLY FOLLOW): {', '.join(dietary_restrictions)}\n"
        prompt += "These restrictions must be strictly followed - do not include any prohibited ingredients.\n\n"
    
    # Add allergies with emphasis
    if allergies:
        prompt += f"ALLERGIES (STRICTLY AVOID - CRITICAL): {', '.join(allergies)}\n"
        prompt += "The user is allergic to these items. Ensure they are completely absent from the recipe.\n\n"
    
    # Add health goals
    if health_goals:
        prompt += f"HEALTH GOALS (Consider): {', '.join(health_goals)}\n"
        prompt += "Please try to align the recipe with these health goals (e.g., high protein for muscle gain, low carb for weight loss).\n\n"
    
    # Add flavor preferences
    # if flavor_preferences:
    #     prompt += "Flavor preferences:\n"
    #     for flavor, level in flavor_preferences.items():
    #         prompt += f"- {flavor.capitalize()}: {level}/5\n"
    #     prompt += "\n"
    
    # Add meal type
    prompt += f"Meal type: {meal_type}\n"
    
    # Add skill level
    prompt += f"Cooking skill level: {skill_level}\n"
    
    # Add cooking time
    prompt += f"Maximum cooking time: {max_cooking_time} minutes\n\n"
    
    # Add ingredients to include/avoid
    if ingredients_to_include:
        prompt += f"Ingredients to include: {', '.join(ingredients_to_include)}\n"
    
    if ingredients_to_avoid:
        prompt += f"Ingredients to avoid: {', '.join(ingredients_to_avoid)}\n"
    
    # Request JSON format
    prompt += "\nReturn ONLY a valid JSON object with the following format. Do not include any additional text, explanation or markdown:\n"
    prompt += """
    {
        "title": "Recipe Title",
        "description": "Brief description of the dish",
        "ingredients": ["Ingredient 1 with quantity", "Ingredient 2 with quantity", ...],
        "instructions": ["Step 1", "Step 2", ...],
        "cuisine_type": "Cuisine type",
        "meal_type": "Meal type",
        "prep_time": prep_time_in_minutes,
        "cook_time": cooking_time_in_minutes,
        "total_time": total_time_in_minutes,
        "vegetarian": boolean,
        "vegan": boolean,
        "gluten_free": boolean,
        "dairy_free": boolean,
        "nut_free": boolean,
        "spicy_level": spicy_level_1_to_5,
        "difficulty": "easy/medium/hard",
        "tags": ["tag1", "tag2", ...]
    }
    """
    print(prompt)
    return prompt

def extract_json_from_response(response_text: str) -> Dict[str, Any]:
    """
    Extract JSON from OpenAI response text
    """
    try:
        logger.debug(f"Extracting JSON from response of length: {len(response_text)}")
        
        # Remove any markdown code block indicators
        if "```" in response_text:
            logger.debug("Detected code blocks in response, extracting content")
            # Extract content between ```json and ``` markers
            import re
            pattern = r"```(?:json)?(.*?)```"
            matches = re.findall(pattern, response_text, re.DOTALL)
            if matches and len(matches) > 0:
                # Use the first block found
                json_str = matches[0].strip()
                logger.debug(f"Extracted JSON from code block, length: {len(json_str)}")
            else:
                # If regex didn't find anything, try simple string manipulation
                start_marker = "```json" if "```json" in response_text else "```"
                end_marker = "```"
                start_idx = response_text.find(start_marker) + len(start_marker)
                end_idx = response_text.rfind(end_marker)
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx].strip()
                    logger.debug(f"Extracted JSON with string manipulation, length: {len(json_str)}")
                else:
                    # Just use the whole response if we can't find the markers
                    json_str = response_text
                    logger.debug("Could not find code blocks, using entire response")
        else:
            json_str = response_text
            logger.debug("No code blocks detected, using entire response")
            
        # Basic cleanup of common JSON issues
        json_str = json_str.strip()
        
        # Try to parse the JSON directly first
        try:
            result = json.loads(json_str)
            logger.info("Successfully parsed JSON directly")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parsing failed: {str(e)}. Attempting more aggressive fixes...")
            logger.debug(f"Failed JSON snippet (first 100 chars): {json_str[:100]}...")

            # Clean up any BOM or Unicode control characters
            import re
            json_str = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', json_str)
            
            # If the opening and closing brackets are missing, add them
            json_str = json_str.strip()
            if not json_str.startswith('[') and not json_str.startswith('{'):
                if "name" in json_str and "description" in json_str:
                    # Looks like a single object, wrap in array
                    json_str = f"[{json_str}]"
                    logger.debug("Added array brackets around object-like content")
                
            # Fix common JSON issues
            json_str = fix_json_formatting(json_str)
            logger.debug("Applied common JSON formatting fixes")
            
            # Try again after cleaning
            try:
                result = json.loads(json_str)
                logger.info("Successfully parsed JSON after cleaning")
                return result
            except json.JSONDecodeError as clean_e:
                logger.warning(f"JSON parsing after cleaning still failed: {str(clean_e)}")
                logger.debug(f"Cleaned JSON (first 100 chars): {json_str[:100]}...")
                
                # Last resort: try to manually extract valid portions
                if "[" in json_str and "]" in json_str:
                    # Get everything between the first [ and last ]
                    start = json_str.find('[')
                    end = json_str.rfind(']') + 1
                    if start != -1 and end != 0 and start < end:
                        json_str = json_str[start:end]
                        logger.debug(f"Extracted content between brackets: [{start}:{end}]")
                        try:
                            result = json.loads(json_str)
                            logger.info("Successfully parsed JSON using bracket extraction")
                            return result
                        except json.JSONDecodeError:
                            logger.warning("Bracket extraction method failed")
                            
                # As a last resort, try to parse it line by line to extract objects
                logger.debug("Attempting line-by-line object extraction")
                objects = []
                in_object = False
                current_object = ""
                brace_count = 0
                
                for line in json_str.split('\n'):
                    if '{' in line:
                        brace_count += line.count('{')
                        in_object = True
                    if '}' in line:
                        brace_count -= line.count('}')
                    
                    if in_object:
                        current_object += line + "\n"
                    
                    if in_object and brace_count == 0:
                        in_object = False
                        try:
                            obj = json.loads(current_object.strip())
                            objects.append(obj)
                            current_object = ""
                            logger.debug(f"Extracted valid object of length: {len(current_object)}")
                        except:
                            logger.warning(f"Failed to parse extracted object: {current_object[:50]}...")
                
                if objects:
                    logger.info(f"Manually extracted {len(objects)} objects")
                    return objects
                
                # Everything failed, log the raw response for debugging
                logger.error(f"All JSON parsing attempts failed. Raw response: {response_text[:300]}...")
        
        # All parsing failed, return an empty list as fallback
        logger.error("Returning empty dict/list as fallback after all parsing attempts failed")
        return {}
        
    except Exception as e:
        logger.error(f"Error extracting JSON from response: {str(e)}")
        # Don't include full response text as it could be very large
        logger.error(f"First 200 chars of response: {response_text[:200]}")
        return {}

def fix_json_formatting(json_str: str) -> str:
    """
    Fix common JSON formatting issues
    """
    # Fix trailing commas in arrays and objects
    json_str = re.sub(r',\s*]', ']', json_str)
    json_str = re.sub(r',\s*}', '}', json_str)
    
    # Fix missing quotes around string values in arrays
    # This regex looks for array patterns with missing quotes
    # For example: ["item1", value2, "item3"] -> ["item1", "value2", "item3"]
    json_str = re.sub(r'\[([^\]]*)\]', lambda m: fix_array_quotes(m.group(0)), json_str)
    
    # Fix missing commas between array elements
    json_str = re.sub(r'"\s+("|\[|\{)', '", \1', json_str)
    
    return json_str

def fix_array_quotes(array_str: str) -> str:
    """
    Fix missing quotes in array elements
    """
    # Skip if this doesn't look like an array
    if not (array_str.startswith('[') and array_str.endswith(']')):
        return array_str
    
    # Get the content inside the brackets
    content = array_str[1:-1].strip()
    
    # If empty array, return as is
    if not content:
        return array_str
    
    # Split by commas, but be careful with nested structures
    elements = []
    current = ""
    in_quotes = False
    brace_level = 0
    bracket_level = 0
    
    for char in content:
        if char == '"' and (content[content.find(char)-1:content.find(char)] != '\\'):
            in_quotes = not in_quotes
        elif char == '{' and not in_quotes:
            brace_level += 1
        elif char == '}' and not in_quotes:
            brace_level -= 1
        elif char == '[' and not in_quotes:
            bracket_level += 1
        elif char == ']' and not in_quotes:
            bracket_level -= 1
        elif char == ',' and not in_quotes and brace_level == 0 and bracket_level == 0:
            elements.append(current.strip())
            current = ""
            continue
        
        current += char
    
    if current.strip():
        elements.append(current.strip())
    
    # Fix each element
    fixed_elements = []
    for element in elements:
        element = element.strip()
        # If element is not already quoted and not a number, boolean or null, add quotes
        if not (element.startswith('"') and element.endswith('"')) and \
           not re.match(r'^-?\d+(\.\d+)?$', element) and \
           element not in ('true', 'false', 'null') and \
           not (element.startswith('{') and element.endswith('}')) and \
           not (element.startswith('[') and element.endswith(']')):
            element = f'"{element}"'
        fixed_elements.append(element)
    
    return '[' + ', '.join(fixed_elements) + ']'

def fix_trailing_commas(json_str: str) -> str:
    """
    Fix trailing commas in JSON
    """
    # Fix trailing commas in arrays
    json_str = re.sub(r',\s*]', ']', json_str)
    # Fix trailing commas in objects
    json_str = re.sub(r',\s*}', '}', json_str)
    return json_str

def generate_fallback_recipe(cuisine_preferences: List[str], meal_type: str) -> Dict[str, Any]:
    """
    Generate a fallback recipe when OpenAI API fails
    """
    import random
    
    logger.info(f"Generating fallback recipe with cuisine={cuisine_preferences}, meal_type={meal_type}")
    
    # Default cuisine if none provided
    if not cuisine_preferences or len(cuisine_preferences) == 0:
        cuisine = random.choice(["Mediterranean", "Asian", "Mexican", "Italian", "Indian", "Thai", "Vietnamese"])
        logger.debug(f"No cuisine preference provided, using random cuisine: {cuisine}")
    else:
        cuisine = cuisine_preferences[0]
        logger.debug(f"Using cuisine from preferences: {cuisine}")
    
    # Normalize meal type to match our templates
    original_meal_type = meal_type
    if not meal_type or meal_type.lower() not in ["breakfast", "lunch", "dinner", "snack", "dessert"]:
        meal_type = random.choice(["breakfast", "lunch", "dinner", "snack", "dessert"])
        logger.debug(f"Invalid meal type '{original_meal_type}', using random meal type: {meal_type}")
    else:
        meal_type = meal_type.lower()
        # Map similar terms
        if meal_type == "brunch":
            logger.debug("Mapping 'brunch' to 'breakfast'")
            meal_type = "breakfast"
        elif meal_type == "appetizer":
            logger.debug("Mapping 'appetizer' to 'snack'")
            meal_type = "snack"
        elif meal_type == "main" or meal_type == "main course":
            logger.debug(f"Mapping '{original_meal_type}' to 'dinner'")
            meal_type = "dinner"
        elif meal_type == "sweet" or meal_type == "sweets":
            logger.debug(f"Mapping '{original_meal_type}' to 'dessert'")
            meal_type = "dessert"
        else:
            logger.debug(f"Using meal type as is: {meal_type}")
    
    logger.debug(f"Final normalized values: cuisine={cuisine}, meal_type={meal_type}")
    
    # Map of diverse recipe templates by meal type
    fallback_recipes = {
        "breakfast": [
            {
                "title": f"{cuisine} Vegetable Frittata",
                "description": f"A light and fluffy egg dish with fresh vegetables and herbs in {cuisine} style.",
                "ingredients": ["Eggs", "Bell peppers", "Onion", "Spinach", "Herbs", "Olive oil", "Salt", "Pepper"],
                "instructions": ["Sauté vegetables", "Beat eggs", "Combine and cook until set", "Finish under broiler"],
                "cuisine_type": cuisine,
                "meal_type": "breakfast",
                "prep_time": 10,
                "cook_time": 15,
                "total_time": 25,
                "vegetarian": True,
                "vegan": False,
                "gluten_free": True,
                "dairy_free": True,
                "nut_free": True,
                "spicy_level": 1,
                "difficulty": "easy",
                "tags": ["breakfast", "egg", "healthy"]
            },
            {
                "title": f"{cuisine} Breakfast Bowl",
                "description": f"A nutritious grain bowl with protein and vegetables inspired by {cuisine} flavors.",
                "ingredients": ["Quinoa", "Avocado", "Cherry tomatoes", "Poached egg", "Fresh herbs", "Lemon juice"],
                "instructions": ["Cook quinoa", "Prepare vegetables", "Poach egg", "Assemble bowl", "Add dressing"],
                "cuisine_type": cuisine,
                "meal_type": "breakfast",
                "prep_time": 15,
                "cook_time": 20,
                "total_time": 35,
                "vegetarian": True,
                "vegan": False,
                "gluten_free": True,
                "dairy_free": True,
                "nut_free": True,
                "spicy_level": 1,
                "difficulty": "medium",
                "tags": ["breakfast", "bowl", "healthy"]
            },
            {
                "title": f"{cuisine} Savory Porridge",
                "description": f"A comforting savory porridge with {cuisine}-inspired toppings and seasonings.",
                "ingredients": ["Steel-cut oats", "Vegetable broth", "Scallions", "Ginger", "Garlic", "Soy sauce", "Sesame oil"],
                "instructions": ["Cook oats in broth", "Prepare toppings", "Season to taste", "Assemble and serve hot"],
                "cuisine_type": cuisine,
                "meal_type": "breakfast",
                "prep_time": 5,
                "cook_time": 25,
                "total_time": 30,
                "vegetarian": True,
                "vegan": True,
                "gluten_free": True,
                "dairy_free": True,
                "nut_free": True,
                "spicy_level": 2,
                "difficulty": "easy",
                "tags": ["breakfast", "porridge", "savory"]
            }
        ],
        "lunch": [
            {
                "title": f"{cuisine} Grain Salad",
                "description": f"A refreshing salad combining grains, vegetables, and herbs with {cuisine} dressing.",
                "ingredients": ["Farro", "Cucumber", "Cherry tomatoes", "Red onion", "Feta cheese", "Olive oil", "Lemon juice"],
                "instructions": ["Cook grain", "Chop vegetables", "Make dressing", "Combine ingredients", "Serve chilled"],
                "cuisine_type": cuisine,
                "meal_type": "lunch",
                "prep_time": 15,
                "cook_time": 20,
                "total_time": 35,
                "vegetarian": True,
                "vegan": False,
                "gluten_free": False,
                "dairy_free": False,
                "nut_free": True,
                "spicy_level": 1,
                "difficulty": "easy",
                "tags": ["lunch", "salad", "healthy"]
            },
            {
                "title": f"{cuisine} Vegetable Wrap",
                "description": f"A flavorful wrap filled with roasted vegetables and sauce inspired by {cuisine}.",
                "ingredients": ["Tortilla", "Roasted vegetables", "Hummus", "Fresh herbs", "Lemon juice"],
                "instructions": ["Roast vegetables", "Warm tortilla", "Spread hummus", "Add vegetables", "Roll and serve"],
                "cuisine_type": cuisine,
                "meal_type": "lunch",
                "prep_time": 10,
                "cook_time": 15,
                "total_time": 25,
                "vegetarian": True,
                "vegan": True,
                "gluten_free": False,
                "dairy_free": True,
                "nut_free": True,
                "spicy_level": 2,
                "difficulty": "easy",
                "tags": ["lunch", "wrap", "vegetarian"]
            },
            {
                "title": f"{cuisine} Noodle Bowl",
                "description": f"A satisfying bowl of noodles with vegetables and protein in a {cuisine}-inspired sauce.",
                "ingredients": ["Rice noodles", "Mixed vegetables", "Tofu", "Herbs", "Lime", "Soy sauce"],
                "instructions": ["Cook noodles", "Prepare vegetables and protein", "Make sauce", "Combine in bowl", "Garnish and serve"],
                "cuisine_type": cuisine,
                "meal_type": "lunch",
                "prep_time": 15,
                "cook_time": 15,
                "total_time": 30,
                "vegetarian": True,
                "vegan": True,
                "gluten_free": True,
                "dairy_free": True,
                "nut_free": True,
                "spicy_level": 2,
                "difficulty": "medium",
                "tags": ["lunch", "noodles", "bowl"]
            }
        ],
        "dinner": [
            {
                "title": f"{cuisine} Roasted Vegetable Bowl",
                "description": f"A hearty bowl of roasted seasonal vegetables with grains in {cuisine} style.",
                "ingredients": ["Mixed vegetables", "Quinoa", "Olive oil", "Herbs", "Lemon", "Garlic"],
                "instructions": ["Roast vegetables", "Cook quinoa", "Prepare sauce", "Combine in bowl", "Garnish and serve"],
                "cuisine_type": cuisine,
                "meal_type": "dinner",
                "prep_time": 15,
                "cook_time": 30,
                "total_time": 45,
                "vegetarian": True,
                "vegan": True,
                "gluten_free": True,
                "dairy_free": True,
                "nut_free": True,
                "spicy_level": 2,
                "difficulty": "medium",
                "tags": ["dinner", "vegetable", "healthy"]
            },
            {
                "title": f"{cuisine} Herb-Crusted Fish",
                "description": f"A delicate fish fillet with a flavorful herb crust inspired by {cuisine}.",
                "ingredients": ["White fish", "Fresh herbs", "Breadcrumbs", "Lemon", "Olive oil", "Garlic"],
                "instructions": ["Prepare herb crust", "Season fish", "Apply crust", "Bake", "Serve with lemon"],
                "cuisine_type": cuisine,
                "meal_type": "dinner",
                "prep_time": 15,
                "cook_time": 20,
                "total_time": 35,
                "vegetarian": False,
                "vegan": False,
                "gluten_free": False,
                "dairy_free": True,
                "nut_free": True,
                "spicy_level": 1,
                "difficulty": "medium",
                "tags": ["dinner", "fish", "seafood"]
            },
            {
                "title": f"{cuisine} Stuffed Bell Peppers",
                "description": f"Colorful bell peppers stuffed with a flavorful mixture of grains, vegetables, and spices in {cuisine} style.",
                "ingredients": ["Bell peppers", "Rice", "Onions", "Garlic", "Tomatoes", "Herbs", "Spices"],
                "instructions": ["Prepare peppers", "Cook filling", "Stuff peppers", "Bake until tender", "Garnish and serve"],
                "cuisine_type": cuisine,
                "meal_type": "dinner",
                "prep_time": 20,
                "cook_time": 40,
                "total_time": 60,
                "vegetarian": True,
                "vegan": True,
                "gluten_free": True,
                "dairy_free": True,
                "nut_free": True,
                "spicy_level": 2,
                "difficulty": "medium",
                "tags": ["dinner", "stuffed", "baked"]
            }
        ],
        "snack": [
            {
                "title": f"{cuisine} Vegetable Dip",
                "description": f"A flavorful dip made with vegetables and herbs in {cuisine} style.",
                "ingredients": ["Yogurt", "Cucumber", "Garlic", "Fresh herbs", "Lemon juice", "Olive oil"],
                "instructions": ["Grate cucumber", "Mix with yogurt", "Add herbs and seasonings", "Chill", "Serve with vegetables"],
                "cuisine_type": cuisine,
                "meal_type": "snack",
                "prep_time": 10,
                "cook_time": 0,
                "total_time": 10,
                "vegetarian": True,
                "vegan": False,
                "gluten_free": True,
                "dairy_free": False,
                "nut_free": True,
                "spicy_level": 1,
                "difficulty": "easy",
                "tags": ["snack", "dip", "vegetable"]
            },
            {
                "title": f"{cuisine} Spiced Chickpeas",
                "description": f"Crispy roasted chickpeas seasoned with {cuisine} spices for a protein-rich snack.",
                "ingredients": ["Chickpeas", "Olive oil", "Spice blend", "Salt"],
                "instructions": ["Dry chickpeas", "Toss with oil and spices", "Roast until crispy", "Cool and store"],
                "cuisine_type": cuisine,
                "meal_type": "snack",
                "prep_time": 5,
                "cook_time": 30,
                "total_time": 35,
                "vegetarian": True,
                "vegan": True,
                "gluten_free": True,
                "dairy_free": True,
                "nut_free": True,
                "spicy_level": 3,
                "difficulty": "easy",
                "tags": ["snack", "chickpeas", "crunchy"]
            },
            {
                "title": f"{cuisine} Vegetable Fritters",
                "description": f"Light and crispy vegetable fritters with {cuisine} seasonings, perfect for snacking.",
                "ingredients": ["Grated vegetables", "Flour", "Eggs", "Herbs", "Spices", "Oil for frying"],
                "instructions": ["Grate vegetables", "Mix batter", "Form patties", "Fry until golden", "Drain and serve"],
                "cuisine_type": cuisine,
                "meal_type": "snack",
                "prep_time": 15,
                "cook_time": 10,
                "total_time": 25,
                "vegetarian": True,
                "vegan": False,
                "gluten_free": False,
                "dairy_free": True,
                "nut_free": True,
                "spicy_level": 2,
                "difficulty": "medium",
                "tags": ["snack", "fritters", "fried"]
            }
        ],
        "dessert": [
            {
                "title": f"{cuisine} Fruit Compote",
                "description": f"A lightly sweetened fruit dessert with spices inspired by {cuisine}.",
                "ingredients": ["Seasonal fruits", "Honey", "Lemon", "Cinnamon", "Vanilla"],
                "instructions": ["Prepare fruits", "Add sweetener and spices", "Simmer", "Cool", "Serve with yogurt"],
                "cuisine_type": cuisine,
                "meal_type": "dessert",
                "prep_time": 10,
                "cook_time": 15,
                "total_time": 25,
                "vegetarian": True,
                "vegan": True,
                "gluten_free": True,
                "dairy_free": True,
                "nut_free": True,
                "spicy_level": 0,
                "difficulty": "easy",
                "tags": ["dessert", "fruit", "light"]
            },
            {
                "title": f"{cuisine} Spiced Cake",
                "description": f"A moist cake flavored with aromatic spices common in {cuisine}.",
                "ingredients": ["Flour", "Sugar", "Eggs", "Butter", "Spices", "Vanilla"],
                "instructions": ["Mix dry ingredients", "Cream butter and sugar", "Add eggs", "Combine mixtures", "Bake"],
                "cuisine_type": cuisine,
                "meal_type": "dessert",
                "prep_time": 20,
                "cook_time": 30,
                "total_time": 50,
                "vegetarian": True,
                "vegan": False,
                "gluten_free": False,
                "dairy_free": False,
                "nut_free": True,
                "spicy_level": 1,
                "difficulty": "medium",
                "tags": ["dessert", "cake", "baked"]
            },
            {
                "title": f"{cuisine} Rice Pudding",
                "description": f"A creamy rice pudding infused with {cuisine} flavors and spices.",
                "ingredients": ["Rice", "Milk", "Sugar", "Cinnamon", "Cardamom", "Rose water"],
                "instructions": ["Cook rice", "Add milk and spices", "Simmer until creamy", "Add sweeteners", "Chill and serve"],
                "cuisine_type": cuisine,
                "meal_type": "dessert",
                "prep_time": 5,
                "cook_time": 35,
                "total_time": 40,
                "vegetarian": True,
                "vegan": False,
                "gluten_free": True,
                "dairy_free": False,
                "nut_free": True,
                "spicy_level": 0,
                "difficulty": "easy",
                "tags": ["dessert", "pudding", "creamy"]
            }
        ]
    }
    
    # Create a more specific title based on cuisine to ensure uniqueness
    suffixes = [
        "with a Twist", 
        "Special", 
        "Chef's Style", 
        "Home-style", 
        "Traditional", 
        "Modern",
        "Signature",
        "Express",
        "Deluxe",
        "Classic"
    ]
    
    # Pick a random recipe from the fallback options
    recipe = random.choice(fallback_recipes[meal_type])
    logger.debug(f"Selected base recipe: {recipe['title']}")
    
    # Add variation to title to avoid duplicates
    original_title = recipe["title"]
    suffix = random.choice(suffixes)
    recipe["title"] = f"{recipe['title']} - {suffix}"
    logger.info(f"Created unique recipe title: '{original_title}' → '{recipe['title']}'")
    
    # Add dietary_restrictions field which might be needed by the API
    recipe["dietary_restrictions"] = []
    
    return recipe

async def get_cuisine_recommendations(
    query: str, 
    limit: int = 5,
    # Add preference parameters
    dietary_restrictions: Optional[List[str]] = None,
    allergies: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Generate cuisine recommendations based on a natural language query
    using OpenAI to find similar culinary profiles.
    
    Args:
        query: Natural language input like "I want to eat biryani"
        limit: Maximum number of recommendations to return
        
    Returns:
        List of cuisine recommendations with details
    """
    import asyncio
    
    try:
        # Set a reasonable limit range
        if limit < 3:
            limit = 5
        elif limit > 10:
            limit = 10
            
        # Shorter, more direct prompt optimized for speed, now including preferences
        prompt = f'''Give exactly {limit} cuisine recommendations similar to "{query}" as a JSON array.
        Each item must have: name, description, key_ingredients (array), flavor_profile, similarity_reason.
Consider the following user preferences:
'''
        if dietary_restrictions:
            prompt += f"- Dietary Restrictions (Strictly Follow): {', '.join(dietary_restrictions)}\n"
        if allergies:
            prompt += f"- Allergies (Strictly Avoid - Critical): {', '.join(allergies)}\n"
        if not dietary_restrictions and not allergies:
             prompt += "- No specific dietary restrictions or allergies provided.\n"
             
        prompt += "\nReturn ONLY valid JSON, no other text."
        
        logger.info(f"Starting cuisine recommendation for query: '{query}', limit: {limit}, restrictions: {dietary_restrictions}, allergies: {allergies}")
        
        # Create a timeout coroutine for the main API call - 8 second timeout
        try:
            # Call OpenAI API asynchronously with timeout
            response = await asyncio.wait_for(
                openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",  # Faster than using more complex models
                    messages=[
                        {"role": "system", "content": "You are a culinary expert. Respond with a JSON array of cuisine recommendations."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.8
                ),
                timeout=10  # 3 second timeout   
            )
            
            # Log raw response for debugging
            response_content = response.choices[0].message.content
            logger.info(f"Received response in first attempt")
            
            # Extract and parse the JSON response
            result = extract_json_from_response(response_content)
            logger.info(f"Extracted {len(result) if isinstance(result, list) else 'non-list'} result")
            
            # If we got a valid response with at least one item, process it
            if isinstance(result, list) and len(result) > 0:
                # Handle single result returned as dict
                if isinstance(result, dict) and "name" in result and "key_ingredients" in result:
                    logger.info("Found single result, converting to list")
                    result = [result]
                
                # Quick validate results
                validated_results = []
                for item in result:
                    if not isinstance(item, dict):
                        logger.warning(f"Skipping non-dictionary item: {type(item)}")
                        continue
                        
                    # Check for required name field
                    if "name" not in item:
                        logger.warning("Skipping item without name field")
                        continue
                        
                    # Ensure minimal required fields are present
                    valid_item = item.copy()  # Create a copy to avoid modifying the original
                    
                    for field in ["description", "similarity_reason"]:
                        if field not in valid_item or not valid_item[field]:
                            valid_item[field] = f"Information about {field} for {valid_item['name']}"
                    
                    # Handle flavor_profile field
                    if "flavor_profile" not in valid_item or not valid_item["flavor_profile"]:
                        valid_item["flavor_profile"] = "Rich and flavorful"
                    # Handle array flavor profiles
                    elif isinstance(valid_item["flavor_profile"], list):
                        valid_item["flavor_profile"] = ", ".join(valid_item["flavor_profile"])
                    
                    # Ensure key_ingredients is always an array
                    if "key_ingredients" not in valid_item or not valid_item["key_ingredients"]:
                        valid_item["key_ingredients"] = ["Various ingredients"]
                    elif not isinstance(valid_item["key_ingredients"], list):
                        try:
                            # If it's a string, try to parse it as a list
                            if isinstance(valid_item["key_ingredients"], str):
                                if "[" in valid_item["key_ingredients"] and "]" in valid_item["key_ingredients"]:
                                    # Try to parse JSON string
                                    import ast
                                    valid_item["key_ingredients"] = ast.literal_eval(valid_item["key_ingredients"])
                                else:
                                    # Split by commas
                                    valid_item["key_ingredients"] = [i.strip() for i in valid_item["key_ingredients"].split(",")]
                            else:
                                valid_item["key_ingredients"] = [str(valid_item["key_ingredients"])]
                        except Exception as e:
                            logger.warning(f"Error parsing key_ingredients: {e}")
                            valid_item["key_ingredients"] = ["Various ingredients"]
                    
                    validated_results.append(valid_item)
                
                # If we have valid results from the API, return them
                if validated_results:
                    logger.info(f"Returning {len(validated_results)} validated cuisine recommendations from API")
                    return validated_results[:limit]
                    
            # If we reached here, the API didn't return usable results
            logger.warning("No valid cuisine recommendations from API, using fallback")
                
        except asyncio.TimeoutError:
            logger.warning("API call timed out after 3 seconds")
            
        # If we get here, either the API call failed, timed out, or returned invalid data
        # Fall back to generating recommendations directly
        return generate_fallback_recommendations(query, limit)
            
    except Exception as e:
        logger.error(f"Error generating cuisine recommendations: {str(e)}")
        logger.error(f"Query: {query}")
        # Return fallback recommendations
        return generate_fallback_recommendations(query, limit)

def generate_fallback_recommendations(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Generate fallback recommendations without API calls"""
    logger.info(f"Generating fallback recommendations for: {query}")
    
    # Extract the actual food item from query like "I want to eat idli"
    food_terms = query.lower().split()
    if "eat" in food_terms and food_terms.index("eat") < len(food_terms) - 1:
        food_item = food_terms[food_terms.index("eat") + 1].strip('.,?!')
    else:
        # Take the last word as the food item if "eat" not found
        food_item = food_terms[-1].strip('.,?!')
    
    logger.info(f"Extracted food item: {food_item}")
    
    # Database of popular dishes by cuisine for authentic recommendations
    cuisine_dishes = {
        "Indian": [
            {
                "name": "Dosa",
                "description": "A thin crispy pancake made from fermented rice and lentil batter, often served with chutneys and sambar.",
                "key_ingredients": ["Rice flour", "Lentils", "Fenugreek seeds", "Ghee"],
                "flavor_profile": "Savory with tangy notes from fermentation"
            },
            {
                "name": "Vada",
                "description": "Crispy savory doughnut-shaped fritters made from lentil or gram flour, often served as a breakfast item or snack.",
                "key_ingredients": ["Urad dal", "Rice flour", "Ginger", "Green chilies", "Curry leaves"],
                "flavor_profile": "Savory and spicy with a crispy exterior and soft interior"
            },
            {
                "name": "Uttapam",
                "description": "A thick pancake made with a fermented rice and lentil batter, topped with vegetables and herbs.",
                "key_ingredients": ["Rice", "Urad dal", "Onions", "Tomatoes", "Green chilies"],
                "flavor_profile": "Savory and slightly tangy with fresh vegetable flavors"
            }
        ],
        "Thai": [
            {
                "name": "Pad Thai",
                "description": "Stir-fried rice noodles with a sweet, savory and slightly sour sauce, typically with tofu, bean sprouts, peanuts and egg.",
                "key_ingredients": ["Rice noodles", "Tamarind paste", "Fish sauce", "Palm sugar", "Bean sprouts", "Peanuts"],
                "flavor_profile": "Sweet, sour, and savory with umami notes"
            },
            {
                "name": "Tom Kha Gai",
                "description": "A creamy coconut soup with chicken, galangal, lemongrass and lime, known for its aromatic and spicy flavor.",
                "key_ingredients": ["Coconut milk", "Galangal", "Lemongrass", "Kaffir lime leaves", "Chicken"],
                "flavor_profile": "Creamy, aromatic with a balance of sour, spicy and sweet notes"
            },
            {
                "name": "Green Curry",
                "description": "A rich, aromatic curry made with fresh green chili paste, coconut milk and Thai basil.",
                "key_ingredients": ["Green curry paste", "Coconut milk", "Thai basil", "Kaffir lime leaves", "Fish sauce"],
                "flavor_profile": "Spicy, aromatic and herbaceous with a creamy texture"
            }
        ],
        "Mexican": [
            {
                "name": "Tacos al Pastor",
                "description": "Marinated pork tacos cooked on a vertical spit, served on small corn tortillas with pineapple, onion and cilantro.",
                "key_ingredients": ["Marinated pork", "Corn tortillas", "Pineapple", "Onion", "Cilantro"],
                "flavor_profile": "Savory and spicy with sweet notes from the pineapple"
            },
            {
                "name": "Chiles Rellenos",
                "description": "Poblano peppers stuffed with cheese, battered and fried, typically served with a tomato-based sauce.",
                "key_ingredients": ["Poblano peppers", "Cheese", "Eggs", "Tomato sauce"],
                "flavor_profile": "Mild spice with rich, cheesy interior and slight smokiness"
            },
            {
                "name": "Mole Poblano",
                "description": "A rich sauce made with chocolate, chili peppers, and numerous spices, typically served over chicken or turkey.",
                "key_ingredients": ["Chocolate", "Dried chilies", "Nuts", "Seeds", "Spices"],
                "flavor_profile": "Complex mix of spicy, sweet, and savory with earthy notes"
            }
        ],
        "Italian": [
            {
                "name": "Risotto ai Funghi",
                "description": "Creamy rice dish cooked slowly with mushrooms, white wine, and Parmesan cheese.",
                "key_ingredients": ["Arborio rice", "Mushrooms", "White wine", "Parmesan cheese", "Onion"],
                "flavor_profile": "Rich, creamy with earthy mushroom flavors"
            },
            {
                "name": "Osso Buco",
                "description": "Veal shanks braised with vegetables, white wine and broth, traditionally served with gremolata.",
                "key_ingredients": ["Veal shanks", "Mirepoix", "White wine", "Tomatoes", "Gremolata"],
                "flavor_profile": "Rich, savory with bright citrus notes from the gremolata"
            },
            {
                "name": "Spaghetti alla Carbonara",
                "description": "Pasta dish with eggs, hard cheese, cured pork, and black pepper.",
                "key_ingredients": ["Spaghetti", "Eggs", "Pecorino Romano", "Guanciale or pancetta", "Black pepper"],
                "flavor_profile": "Rich, savory with a silky texture and peppery finish"
            }
        ],
        "Japanese": [
            {
                "name": "Ramen",
                "description": "Wheat noodles served in a meat or fish-based broth, often flavored with soy sauce or miso, and topped with ingredients such as sliced pork, dried seaweed, and green onions.",
                "key_ingredients": ["Wheat noodles", "Pork or chicken broth", "Soy sauce", "Chashu pork", "Nori"],
                "flavor_profile": "Rich, savory with complex umami depth"
            },
            {
                "name": "Okonomiyaki",
                "description": "Savory pancake containing a variety of ingredients like cabbage, meat or seafood, topped with Japanese mayonnaise and okonomiyaki sauce.",
                "key_ingredients": ["Cabbage", "Flour batter", "Eggs", "Pork belly", "Okonomiyaki sauce"],
                "flavor_profile": "Savory with sweet and tangy sauce notes"
            },
            {
                "name": "Katsu Curry",
                "description": "Breaded, deep-fried cutlet of meat served with Japanese curry sauce over rice.",
                "key_ingredients": ["Pork or chicken cutlet", "Japanese curry roux", "Rice", "Vegetables"],
                "flavor_profile": "Savory, mildly spiced curry with crispy meat texture"
            }
        ]
    }
    
    # Find similar cuisines based on food item
    # This is a simplistic matching - in a real app you would use a real recommendation system
    cuisine_similarity = {}
    found_exact_match = False
    
    # Check if we have an exact match for the food item
    for cuisine, dishes in cuisine_dishes.items():
        for dish in dishes:
            if food_item.lower() in dish["name"].lower():
                # Direct match to a dish, prioritize that cuisine
                cuisine_similarity[cuisine] = 0.9
                found_exact_match = True
            elif food_item.lower() in [ingredient.lower() for ingredient in dish["key_ingredients"]]:
                # Ingredient match
                cuisine_similarity[cuisine] = 0.7
                
    # If no exact match, assign default similarities
    if not found_exact_match:
        if "rice" in food_item or "curry" in food_item or "dosa" in food_item or "idli" in food_item:
            cuisine_similarity = {"Indian": 0.9, "Thai": 0.7, "Japanese": 0.5}
        elif "pasta" in food_item or "pizza" in food_item:
            cuisine_similarity = {"Italian": 0.9, "Mexican": 0.4, "Indian": 0.2}
        elif "taco" in food_item or "burrito" in food_item:
            cuisine_similarity = {"Mexican": 0.9, "Indian": 0.4, "Thai": 0.3}
        elif "sushi" in food_item or "ramen" in food_item:
            cuisine_similarity = {"Japanese": 0.9, "Thai": 0.5, "Indian": 0.2}
        else:
            # Default similarities
            cuisine_similarity = {"Indian": 0.3, "Thai": 0.3, "Mexican": 0.3, "Italian": 0.3, "Japanese": 0.3}
    
    # Sort cuisines by similarity
    sorted_cuisines = sorted(cuisine_similarity.items(), key=lambda x: x[1], reverse=True)
    
    # Generate recommendations
    recommendations = []
    used_dishes = set()
    
    for cuisine, _ in sorted_cuisines:
        if len(recommendations) >= limit:
            break
            
        # Get available dishes for this cuisine
        available_dishes = [dish for dish in cuisine_dishes.get(cuisine, []) 
                          if dish["name"] not in used_dishes]
        
        if not available_dishes:
            continue
            
        # Add dishes from this cuisine
        for dish in available_dishes:
            if len(recommendations) >= limit:
                break
                
            # Create a copy to avoid modifying the original
            recommendation = dish.copy()
            
            # Add similarity reason based on query
            if food_item.lower() in dish["name"].lower():
                recommendation["similarity_reason"] = f"This is a variation of {food_item} from {cuisine} cuisine."
            else:
                recommendation["similarity_reason"] = f"This {cuisine} dish has a similar texture and flavor profile to {food_item}."
            
            recommendations.append(recommendation)
            used_dishes.add(dish["name"])
    
    # If we still need more recommendations
    if len(recommendations) < limit:
        # Fill with generic recommendations
        for i in range(len(recommendations), limit):
            idx = i % len(sorted_cuisines)
            cuisine = sorted_cuisines[idx][0]
            
            # Make a generic recommendation
            rec = {
                "name": f"{cuisine} {['Specialty', 'Delicacy', 'Classic', 'Favorite'][i % 4]}",
                "description": f"A traditional {cuisine} dish with flavors that complement {food_item}.",
                "key_ingredients": [
                    f"{['Fresh', 'Aromatic', 'Traditional', 'Local'][i % 4]} ingredients",
                    f"{cuisine} spices and herbs",
                    "Regional vegetables",
                    "Authentic seasonings"
                ],
                "flavor_profile": f"{['Rich and aromatic', 'Perfectly balanced', 'Bold and flavorful', 'Delicate and nuanced'][i % 4]}",
                "similarity_reason": f"Uses cooking techniques and flavor combinations that would appeal to fans of {food_item}."
            }
            recommendations.append(rec)
    
    logger.info(f"Created {len(recommendations)} authentic fallback recommendations")
    return recommendations[:limit] 