import sqlite3

conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(recipes);')
columns = cursor.fetchall()

print("All columns in recipes table:")
for col in columns:
    print(f"- {col[1]} ({col[2]})")

conn.close()
print("Database schema check complete.") 