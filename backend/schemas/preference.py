from typing import List, Optional
from pydantic import BaseModel

class PreferenceBase(BaseModel):
    dietary_restrictions: List[str] = []
    favorite_cuisines: List[str] = []
    cooking_skill_level: str = "beginner"
    health_goals: List[str] = []
    allergies: List[str] = []

class PreferenceCreate(PreferenceBase):
    pass

class PreferenceResponse(PreferenceBase):
    user_id: int

    class Config:
        orm_mode = True
        from_attributes = True 