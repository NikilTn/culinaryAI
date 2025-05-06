from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from database.database import Base, engine
from models.user import User  
from models.recipe import Recipe
from models.preference import UserPreference

def create_tables():
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    create_tables() 