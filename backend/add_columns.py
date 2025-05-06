import sqlite3

def add_column(cursor, table, column, type_with_default):
    try:
        cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {type_with_default}')
        print(f"Added column {column} to {table}")
        return True
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Column {column} already exists in {table}")
            return True
        else:
            print(f"Error adding column {column}: {e}")
            return False

conn = sqlite3.connect('test.db')
cursor = conn.cursor()

# Check current columns
cursor.execute('PRAGMA table_info(recipes);')
existing_columns = [col[1] for col in cursor.fetchall()]
print(f"Existing columns: {existing_columns}")

# Define all required columns
required_columns = {
    'id': 'INTEGER PRIMARY KEY',
    'title': 'VARCHAR',
    'description': 'TEXT',
    'ingredients': 'TEXT', 
    'instructions': 'TEXT',
    'prep_time': 'INTEGER DEFAULT 0',
    'cooking_time': 'INTEGER',
    'total_time': 'INTEGER DEFAULT 0',
    'difficulty': 'VARCHAR',
    'cuisine': 'VARCHAR',
    'dietary_restrictions': 'TEXT',
    'tags': 'TEXT DEFAULT "[]"',
    'is_ai_generated': 'BOOLEAN DEFAULT 0',
    'generated_for_user_id': 'INTEGER',
    'vegetarian': 'BOOLEAN DEFAULT 0',
    'vegan': 'BOOLEAN DEFAULT 0',
    'gluten_free': 'BOOLEAN DEFAULT 0',
    'dairy_free': 'BOOLEAN DEFAULT 0',
    'nut_free': 'BOOLEAN DEFAULT 0',
    'spicy_level': 'INTEGER DEFAULT 0',
    'image_url': 'TEXT'
}

# Add any missing columns
success = True
for column, type_def in required_columns.items():
    if column not in existing_columns:
        if not add_column(cursor, 'recipes', column, type_def):
            success = False

# Commit changes and close
if success:
    conn.commit()
    print("All columns added successfully")
else:
    print("Some columns failed to add")
conn.close()

# Check final schema
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(recipes);')
final_columns = [col[1] for col in cursor.fetchall()]
print(f"Final columns: {final_columns}")
conn.close() 