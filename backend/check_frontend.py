import sqlite3

# Database columns
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(recipes);')
columns = cursor.fetchall()
db_columns = [col[1] for col in columns]

# Frontend expected columns (from frontend/src/types/recipe.ts)
frontend_columns = [
    "id",
    "title",
    "description", 
    "ingredients",
    "instructions",
    "cuisine",
    "prep_time",
    "cook_time",  # Note: backend has cooking_time
    "total_time",
    "vegetarian",  # These boolean fields might be part of dietary_restrictions in backend
    "vegan",
    "gluten_free",
    "dairy_free",
    "nut_free",
    "spicy_level",
    "difficulty",
    "image_url",
    "is_ai_generated",
    "generated_for_user_id",
    "tags"
]

# Backend to frontend mappings
backend_to_frontend = {
    "cooking_time": "cook_time"
}

# Check for missing columns
print("Frontend columns not directly in database:")
for col in frontend_columns:
    # Check if column exists in database or has a mapped equivalent
    if col not in db_columns and not any(backend_to_frontend.get(db_col) == col for db_col in db_columns):
        print(f"- {col}")

print("\nDatabase columns not directly in frontend:")
for col in db_columns:
    # Check if column exists in frontend or has a mapped equivalent
    if col not in frontend_columns and col not in backend_to_frontend:
        print(f"- {col}")

conn.close() 