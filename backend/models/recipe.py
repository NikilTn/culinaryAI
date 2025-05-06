from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY, JSON

from database.database import Base
import json

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    
    # Store as JSON strings
    ingredients = Column(Text)  # JSON string of ingredients list
    instructions = Column(Text)  # JSON string of instructions list
    
    # Basic recipe info
    prep_time = Column(Integer, default=0)      # Preparation time in minutes
    cooking_time = Column(Integer)              # Cooking time in minutes
    total_time = Column(Integer, default=0)     # Total time (prep + cooking)
    difficulty = Column(String)
    cuisine = Column(String)
    dietary_restrictions = Column(Text)  # JSON string of dietary restrictions list
    tags = Column(Text, default='[]')    # JSON string of tags list
    
    # AI generation info
    is_ai_generated = Column(Boolean, default=False)
    generated_for_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationship with User model
    user = relationship("User", back_populates="generated_recipes")
    
    # Property methods for lists stored as JSON
    @property
    def ingredients_list(self):
        try:
            return json.loads(self.ingredients) if self.ingredients else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    @property
    def instructions_list(self):
        try:
            return json.loads(self.instructions) if self.instructions else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    @property
    def dietary_restrictions_list(self):
        try:
            return json.loads(self.dietary_restrictions) if self.dietary_restrictions else []
        except (json.JSONDecodeError, TypeError):
            return []
            
    @property
    def tags_list(self):
        try:
            return json.loads(self.tags) if self.tags else []
        except (json.JSONDecodeError, TypeError):
            return [] 