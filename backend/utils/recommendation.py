import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
from typing import List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecipeRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.recipe_matrix = None
        self.recipes = []
    
    def fit(self, recipes: List[Dict[str, Any]]):
        """
        Process recipes and build the TF-IDF matrix
        """
        self.recipes = recipes
        
        # Create text documents from recipes for vectorization
        documents = []
        for recipe in recipes:
            # Create a document combining relevant recipe information
            doc = f"{recipe['title']} {recipe['description']} {recipe['cuisine_type']} "
            
            # Add ingredients
            ingredients = json.loads(recipe['ingredients']) if isinstance(recipe['ingredients'], str) else recipe['ingredients']
            doc += " ".join(ingredients)
            
            # Add instructions
            doc += " " + recipe['instructions']
            
            documents.append(doc)
        
        # Compute TF-IDF matrix
        self.recipe_matrix = self.vectorizer.fit_transform(documents)
        
        logger.info(f"Recommendation engine fitted with {len(recipes)} recipes")
        return self
    
    def get_similar_recipes(self, query: str, top_n: int = 5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Find recipes similar to the query text
        """
        if self.recipe_matrix is None or self.recipe_matrix.shape[0] == 0:
            raise ValueError("Recommender not fitted. Call fit() first")
        
        # Transform the query into TF-IDF space
        query_vector = self.vectorizer.transform([query])
        
        # Calculate cosine similarity against all recipes
        similarities = cosine_similarity(query_vector, self.recipe_matrix).flatten()
        
        # Get the indices of top-N similar recipes
        similar_indices = similarities.argsort()[::-1]
        
        # Apply filters if provided
        if filters:
            filtered_indices = []
            for idx in similar_indices:
                recipe = self.recipes[idx]
                if self._match_filters(recipe, filters):
                    filtered_indices.append(idx)
                
                if len(filtered_indices) >= top_n:
                    break
            
            similar_indices = filtered_indices[:top_n]
        else:
            similar_indices = similar_indices[:top_n]
        
        # Return top similar recipes
        similar_recipes = [self.recipes[idx] for idx in similar_indices]
        
        return similar_recipes
    
    def get_user_recommendations(self, user_preferences: Dict[str, Any], top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on user preferences
        """
        if self.recipe_matrix is None or self.recipe_matrix.shape[0] == 0:
            raise ValueError("Recommender not fitted. Call fit() first")
        
        # Construct a query from user preferences
        query = self._construct_preference_query(user_preferences)
        
        # Create filters based on dietary restrictions
        filters = self._create_preference_filters(user_preferences)
        
        # Get recommendations
        recommendations = self.get_similar_recipes(query, top_n, filters)
        
        return recommendations
    
    def _construct_preference_query(self, preferences: Dict[str, Any]) -> str:
        """
        Construct a search query based on user preferences
        """
        query_parts = []
        
        # Add cuisine preferences - handle both list and string formats
        if preferences.get('favorite_cuisines'):
            if isinstance(preferences['favorite_cuisines'], list):
                query_parts.extend(preferences['favorite_cuisines'])
            else:
                # Fallback to handling string format with split
                cuisines = preferences['favorite_cuisines'].split(',')
                query_parts.extend(cuisines)
        
        # Add meal types
        meal_types = []
        for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks', 'desserts']:
            if preferences.get(meal_type, False):
                meal_types.append(meal_type)
        
        if meal_types:
            query_parts.extend(meal_types)
        
        # Add flavor preferences
        flavors = []
        for flavor in ['spicy', 'sweet', 'savory', 'bitter', 'sour']:
            level = preferences.get(f"{flavor}_level", 3)
            if level > 3:  # Only add flavors with high preference
                flavors.append(flavor)
        
        if flavors:
            query_parts.extend(flavors)
        
        return " ".join(query_parts)
    
    def _create_preference_filters(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create filters based on user dietary restrictions
        """
        filters = {}
        
        # Check for dietary restrictions in the preferences list
        dietary_restrictions = preferences.get('dietary_restrictions', [])
        if dietary_restrictions:
            # Handle both list and string formats
            if not isinstance(dietary_restrictions, list):
                dietary_restrictions = dietary_restrictions.split(',')
            
            # Set specific dietary restriction filters based on the list
            if 'vegetarian' in dietary_restrictions:
                filters['vegetarian'] = True
            
            if 'vegan' in dietary_restrictions:
                filters['vegan'] = True
            
            if 'gluten-free' in dietary_restrictions:
                filters['gluten_free'] = True
            
            if 'dairy-free' in dietary_restrictions:
                filters['dairy_free'] = True
            
            if 'nut-free' in dietary_restrictions:
                filters['nut_free'] = True
        
        # Also check for explicit boolean settings
        if preferences.get('vegetarian', False):
            filters['vegetarian'] = True
        
        if preferences.get('vegan', False):
            filters['vegan'] = True
        
        if preferences.get('gluten_free', False):
            filters['gluten_free'] = True
        
        if preferences.get('dairy_free', False):
            filters['dairy_free'] = True
        
        if preferences.get('nut_free', False):
            filters['nut_free'] = True
        
        # Add cooking time filter
        if preferences.get('cooking_time_max'):
            filters['cooking_time_max'] = preferences['cooking_time_max']
        
        # Add skill level filter
        if preferences.get('cooking_skill_level'):
            skill_level = preferences['cooking_skill_level']
            # Map skill level to difficulty
            skill_level_map = {
                'beginner': 'Easy',
                'intermediate': 'Medium',
                'advanced': 'Hard'
            }
            filters['difficulty'] = skill_level_map.get(skill_level.lower(), skill_level)
        
        return filters
    
    def _match_filters(self, recipe: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Check if a recipe matches the given filters
        """
        for key, value in filters.items():
            if key == 'cooking_time_max':
                # Sum of prep and cook time should be less than max cooking time
                total_time = recipe.get('prep_time', 0) + recipe.get('cook_time', 0)
                if total_time > value:
                    return False
            elif key == 'difficulty':
                # Map skill level to difficulty
                skill_level_map = {
                    'beginner': 'easy',
                    'intermediate': 'medium',
                    'advanced': 'hard'
                }
                difficulty = skill_level_map.get(value, value)
                if recipe.get(key) != difficulty:
                    return False
            elif recipe.get(key) != value:
                return False
        
        return True 