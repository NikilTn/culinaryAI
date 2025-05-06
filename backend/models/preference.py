from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, ARRAY, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base
import json

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Store as comma-separated strings to be parsed as lists in the API
    dietary_restrictions = Column(String, default="")
    favorite_cuisines = Column(String, default="")
    cooking_skill_level = Column(String, default="beginner")
    health_goals = Column(String, default="")
    allergies = Column(String, default="")
    
    # Cuisine preferences
    disliked_cuisines = Column(Text)  # Comma-separated values
    
    # Dietary restrictions
    vegetarian = Column(Boolean, default=False)
    vegan = Column(Boolean, default=False)
    gluten_free = Column(Boolean, default=False)
    dairy_free = Column(Boolean, default=False)
    nut_free = Column(Boolean, default=False)
    
    # Flavor preferences (1-5 scale)
    spicy_level = Column(Integer, default=3)
    sweet_level = Column(Integer, default=3)
    savory_level = Column(Integer, default=3)
    bitter_level = Column(Integer, default=3)
    sour_level = Column(Integer, default=3)
    
    # Meal types
    breakfast = Column(Boolean, default=True)
    lunch = Column(Boolean, default=True)
    dinner = Column(Boolean, default=True)
    snacks = Column(Boolean, default=True)
    desserts = Column(Boolean, default=True)
    
    # Additional preferences
    cooking_time_max = Column(Integer, default=60)  # Max cooking time in minutes
    additional_notes = Column(Text, nullable=True)
    
    # Relationship with User model
    user = relationship("User", back_populates="preferences")
    
    def __init__(self, user_id, dietary_restrictions=None, favorite_cuisines=None, 
                cooking_skill_level="beginner", health_goals=None, allergies=None):
        self.user_id = user_id
        
        if isinstance(dietary_restrictions, list):
            self.dietary_restrictions = ",".join(dietary_restrictions or [])
        else:
            self.dietary_restrictions = dietary_restrictions or ""
            
        if isinstance(favorite_cuisines, list):
            self.favorite_cuisines = ",".join(favorite_cuisines or [])
        else:
            self.favorite_cuisines = favorite_cuisines or ""
            
        self.cooking_skill_level = cooking_skill_level
        
        if isinstance(health_goals, list):
            self.health_goals = ",".join(health_goals or [])
        else:
            self.health_goals = health_goals or ""
            
        if isinstance(allergies, list):
            self.allergies = ",".join(allergies or [])
        else:
            self.allergies = allergies or ""
        
    # Property methods to convert between string and list
    @property
    def dietary_restrictions_list(self):
        if not self.dietary_restrictions:
            return []
        return self.dietary_restrictions.split(',') if self.dietary_restrictions else []
    
    @property
    def favorite_cuisines_list(self):
        if not self.favorite_cuisines:
            return []
        return self.favorite_cuisines.split(',') if self.favorite_cuisines else []
    
    @property
    def health_goals_list(self):
        if not self.health_goals:
            return []
        return self.health_goals.split(',') if self.health_goals else []
    
    @property
    def allergies_list(self):
        if not self.allergies:
            return []
        return self.allergies.split(',') if self.allergies else [] 