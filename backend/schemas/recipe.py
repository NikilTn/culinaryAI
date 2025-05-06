from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

class RecipeBase(BaseModel):
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    prep_time: int = 0
    cooking_time: int
    total_time: int = 0
    difficulty: str
    cuisine: str
    dietary_restrictions: List[str]
    tags: Optional[List[str]] = []

class RecipeCreate(RecipeBase):
    is_ai_generated: bool = True
    generated_for_user_id: Optional[int] = None

class RecipeUpdate(RecipeBase):
    pass

class RecipeBrief(BaseModel):
    id: int
    title: str
    description: str
    prep_time: int = 0
    cooking_time: int
    total_time: int = 0
    difficulty: str
    cuisine: str
    dietary_restrictions: List[str]
    tags: List[str] = []

    class Config:
        orm_mode = True
        from_attributes = True

class RecipeResponse(RecipeBrief):
    ingredients: List[str]
    instructions: List[str]

    class Config:
        orm_mode = True
        from_attributes = True

class RecipeInDB(RecipeBase):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True

# Schema for OpenAI recipe generation request
class RecipeGenerationRequest(BaseModel):
    # Frontend fields
    cuisine_preferences: Optional[List[str]] = None
    meal_type: Optional[str] = None
    skill_level: Optional[str] = None
    max_cooking_time: Optional[int] = None
    flavor_preferences: Optional[Dict[str, int]] = None
    ingredients_to_include: Optional[List[str]] = None
    ingredients_to_avoid: Optional[List[str]] = None
    # Add specific fields for better prompt clarity
    allergies: Optional[List[str]] = None
    health_goals: Optional[List[str]] = None
    
    # Backend fields (for backward compatibility or internal calls)
    cuisine: Optional[str] = None
    ingredients: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    dish_type: Optional[str] = None
    cooking_time: Optional[int] = None
    difficulty: Optional[str] = None

# Schema for recipe similarity search
class RecipeSimilarityRequest(BaseModel):
    recipe_id: Optional[int] = None
    ingredients: Optional[List[str]] = None 