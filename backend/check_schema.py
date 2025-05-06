import sqlite3
import json
from models.recipe import Recipe
from sqlalchemy import inspect
from database.database import engine

# Check the database schema
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(recipes);')
columns = cursor.fetchall()

print("Database columns in recipes table:")
for col in columns:
    print(f"- {col[1]} ({col[2]})")

# Check the SQLAlchemy model
inspector = inspect(engine)
model_columns = []
if inspector.has_table("recipes"):
    model_columns = inspector.get_columns("recipes")
    print("\nSQLAlchemy model columns:")
    for column in model_columns:
        print(f"- {column['name']} ({column['type']})")

# List of model columns from Recipe class
recipe_columns = [c.name for c in Recipe.__table__.columns]
print("\nRecipe model columns from class:")
for col in recipe_columns:
    print(f"- {col}")

# Check for missing columns
db_columns = [col[1] for col in columns]
print("\nColumns in model but missing in database:")
for col in recipe_columns:
    if col not in db_columns:
        print(f"- {col}")

print("\nColumns in database but not in model:")
for col in db_columns:
    if col not in recipe_columns:
        print(f"- {col}")

conn.close() 