import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import logging
from typing import List, Dict, Any, Optional

from backend.db.models import Recipe, UserPreference
from backend.schemas.recipe import RecipeBrief

logger = logging.getLogger(__name__)

class RecipeRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        self.recipe_data = None
        self.recipe_ids = None
        self.fitted = False
        
    def fit(self, recipes: List[Recipe]):
        if not recipes:
            logger.warning("No recipes provided to fit the recommender")
            return self
            
        try:
            # Extract recipe features
            texts = []
            self.recipe_data = []
            self.recipe_ids = []
            
            for recipe in recipes:
                # Create document for TF-IDF
                doc = (f"{recipe.title} {recipe.description} {recipe.cuisine_type} "
                      f"{recipe.meal_type} {' '.join(recipe.ingredients)}")
                texts.append(doc)
                
                # Store recipe data
                self.recipe_data.append({
                    'id': recipe.id,
                    'title': recipe.title,
                    'description': recipe.description,
                    'cuisine_type': recipe.cuisine_type,
                    'meal_type': recipe.meal_type,
                    'prep_time': recipe.prep_time,
                    'cook_time': recipe.cook_time,
                    'difficulty': recipe.difficulty,
                    'vegetarian': recipe.vegetarian,
                    'vegan': recipe.vegan,
                    'gluten_free': recipe.gluten_free,
                    'dairy_free': recipe.dairy_free,
                    'nut_free': recipe.nut_free,
                    'spicy_level': recipe.spicy_level or 0
                })
                self.recipe_ids.append(recipe.id)
                
            # Convert to DataFrame for easier filtering
            self.recipe_df = pd.DataFrame(self.recipe_data)
            
            # Compute TF-IDF
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            logger.info(f"Fitted recipe recommender with {len(recipes)} recipes")
            self.fitted = True
            return self
        except Exception as e:
            logger.error(f"Error fitting recipe recommender: {str(e)}")
            self.fitted = False
            return self
    
    def find_similar_recipes(self, query: str, max_results: int = 5, **filters) -> List[RecipeBrief]:
        """Find recipes similar to a query text"""
        if not self.fitted:
            logger.warning("Recommender not fitted yet, returning empty list")
            return []
            
        try:
            # Transform query using same vectorizer
            query_vec = self.vectorizer.transform([query])
            
            # Compute similarity
            cosine_similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            
            # Create DataFrame with similarities
            results_df = self.recipe_df.copy()
            results_df['similarity'] = cosine_similarities
            
            # Apply filters
            filtered_df = self._apply_filters(results_df, **filters)
            
            # Sort by similarity and take top n
            top_recipes = filtered_df.sort_values('similarity', ascending=False).head(max_results)
            
            # Convert to RecipeBrief objects
            recommendations = []
            for _, row in top_recipes.iterrows():
                recommendations.append(RecipeBrief(
                    id=row['id'],
                    title=row['title'],
                    description=row['description'],
                    cuisine_type=row['cuisine_type'],
                    meal_type=row['meal_type'],
                    prep_time=row['prep_time'],
                    cook_time=row['cook_time'],
                    difficulty=row['difficulty'],
                    vegetarian=row['vegetarian'],
                    vegan=row['vegan'],
                    gluten_free=row['gluten_free'],
                    dairy_free=row['dairy_free'],
                    nut_free=row['nut_free'],
                    spicy_level=row['spicy_level']
                ))
            
            return recommendations
        except Exception as e:
            logger.error(f"Error finding similar recipes: {str(e)}")
            return []
    
    def get_recommendations_for_user(self, user_preferences: UserPreference, 
                                    max_results: int = 5) -> List[RecipeBrief]:
        """Get personalized recommendations for a user based on their preferences"""
        if not self.fitted:
            logger.warning("Recommender not fitted yet, returning empty list")
            return []
            
        try:
            # Create preference-based filters
            filters = {
                'vegetarian': user_preferences.vegetarian,
                'vegan': user_preferences.vegan,
                'gluten_free': user_preferences.gluten_free,
                'dairy_free': user_preferences.dairy_free,
                'nut_free': user_preferences.nut_free
            }
            
            # Create query from user preferences
            cuisine_prefs = " ".join(user_preferences.cuisine_preferences) if user_preferences.cuisine_preferences else ""
            meal_types = " ".join(user_preferences.favorite_meal_types) if user_preferences.favorite_meal_types else ""
            flavor_prefs = " ".join([k for k, v in user_preferences.flavor_preferences.items() if v > 3]) if user_preferences.flavor_preferences else ""
            
            query = f"{cuisine_prefs} {meal_types} {flavor_prefs}"
            
            if query.strip() == "":
                query = "food recipe"  # Default query if no preferences
            
            # Get recommendations
            recommendations = self.find_similar_recipes(query, max_results, **filters)
            return recommendations
        except Exception as e:
            logger.error(f"Error getting recommendations for user: {str(e)}")
            return []
    
    def _apply_filters(self, df: pd.DataFrame, **filters) -> pd.DataFrame:
        """Apply filters to recipe dataframe"""
        filtered_df = df.copy()
        
        # Apply dietary filters
        for dietary_filter in ['vegetarian', 'vegan', 'gluten_free', 'dairy_free', 'nut_free']:
            if dietary_filter in filters and filters[dietary_filter]:
                filtered_df = filtered_df[filtered_df[dietary_filter] == True]
        
        # Apply cooking time filter
        if 'max_cooking_time' in filters and filters['max_cooking_time']:
            filtered_df = filtered_df[filtered_df['cook_time'] <= filters['max_cooking_time']]
            
        # Apply cuisine filter
        if 'cuisine_type' in filters and filters['cuisine_type']:
            filtered_df = filtered_df[filtered_df['cuisine_type'] == filters['cuisine_type']]
            
        # Apply meal type filter
        if 'meal_type' in filters and filters['meal_type']:
            filtered_df = filtered_df[filtered_df['meal_type'] == filters['meal_type']]
            
        # If no results after filtering, return original
        if filtered_df.empty:
            logger.warning("No recipes match all filters, returning unfiltered results")
            return df
            
        return filtered_df 