import os
import sys
import json
from sqlalchemy.orm import Session
from models import Recipe
from database.database import SessionLocal

# Sample recipes with diverse properties for testing filters
SAMPLE_RECIPES = [
    {
        "title": "Spaghetti Carbonara",
        "description": "A classic Italian pasta dish with eggs, cheese, pancetta, and black pepper.",
        "ingredients": json.dumps(["400g spaghetti", "200g pancetta", "3 large eggs", "75g Pecorino Romano", "50g Parmesan", "Freshly ground black pepper", "Sea salt"]),
        "instructions": "1. Cook pasta in salted water.\n2. Fry pancetta until crispy.\n3. Whisk eggs and cheese together.\n4. Add pasta to pancetta, remove from heat.\n5. Quickly stir in egg mixture to create creamy sauce.",
        "cuisine_type": "Italian",
        "meal_type": "Dinner",
        "prep_time": 15,
        "cook_time": 20,
        "vegetarian": False,
        "vegan": False,
        "gluten_free": False,
        "dairy_free": False,
        "nut_free": True,
        "spicy_level": 1,
        "difficulty": "Medium"
    },
    {
        "title": "Vegetable Stir Fry",
        "description": "Quick and healthy vegetable stir fry with a savory sauce.",
        "ingredients": json.dumps(["2 cups mixed vegetables", "2 tbsp soy sauce", "1 tbsp sesame oil", "2 cloves garlic", "1 inch ginger", "2 tbsp vegetable oil", "1 tbsp rice vinegar", "1 tsp sugar"]),
        "instructions": "1. Prep vegetables and mince garlic and ginger.\n2. Heat oil in wok over high heat.\n3. Add garlic and ginger, stir for 30 seconds.\n4. Add vegetables and stir fry for 5 minutes.\n5. Mix sauce ingredients and add to wok.\n6. Cook for another 2 minutes until sauce thickens.",
        "cuisine_type": "Chinese",
        "meal_type": "Lunch",
        "prep_time": 15,
        "cook_time": 10,
        "vegetarian": True,
        "vegan": True,
        "gluten_free": False,
        "dairy_free": True,
        "nut_free": True,
        "spicy_level": 2,
        "difficulty": "Easy"
    },
    {
        "title": "Chicken Tacos",
        "description": "Flavorful chicken tacos with fresh toppings.",
        "ingredients": json.dumps(["500g chicken breast", "8 corn tortillas", "1 onion", "2 bell peppers", "2 tbsp taco seasoning", "1 cup shredded lettuce", "1 cup diced tomatoes", "1/2 cup sour cream", "1 lime"]),
        "instructions": "1. Season chicken with taco seasoning.\n2. Cook chicken until done, then shred.\n3. Sauté onions and peppers.\n4. Heat tortillas.\n5. Assemble tacos with chicken, vegetables, and toppings.",
        "cuisine_type": "Mexican",
        "meal_type": "Dinner",
        "prep_time": 20,
        "cook_time": 25,
        "vegetarian": False,
        "vegan": False,
        "gluten_free": True,
        "dairy_free": False,
        "nut_free": True,
        "spicy_level": 3,
        "difficulty": "Easy"
    },
    {
        "title": "Vegan Chocolate Cake",
        "description": "Rich and moist vegan chocolate cake that everyone will love.",
        "ingredients": json.dumps(["300g all-purpose flour", "200g sugar", "60g cocoa powder", "1 tsp baking soda", "1/2 tsp salt", "350ml almond milk", "120ml vegetable oil", "2 tsp vanilla extract", "1 tbsp vinegar"]),
        "instructions": "1. Preheat oven to 350°F (175°C).\n2. Mix dry ingredients.\n3. Add wet ingredients and stir until combined.\n4. Pour into greased cake pan.\n5. Bake for 30-35 minutes or until toothpick comes out clean.",
        "cuisine_type": "American",
        "meal_type": "Dessert",
        "prep_time": 15,
        "cook_time": 35,
        "vegetarian": True,
        "vegan": True,
        "gluten_free": False,
        "dairy_free": True,
        "nut_free": False,
        "spicy_level": 1,
        "difficulty": "Medium"
    },
    {
        "title": "Greek Salad",
        "description": "Fresh and healthy traditional Greek salad with feta cheese and olives.",
        "ingredients": json.dumps(["2 large tomatoes", "1 cucumber", "1 red onion", "1 green bell pepper", "200g feta cheese", "100g Kalamata olives", "4 tbsp olive oil", "1 tbsp red wine vinegar", "1 tsp dried oregano", "Salt and pepper"]),
        "instructions": "1. Chop tomatoes, cucumber, onion, and bell pepper into chunks.\n2. Add olives and crumbled feta cheese.\n3. Mix olive oil, vinegar, oregano, salt, and pepper for dressing.\n4. Pour dressing over salad and toss gently.",
        "cuisine_type": "Mediterranean",
        "meal_type": "Lunch",
        "prep_time": 15,
        "cook_time": 0,
        "vegetarian": True,
        "vegan": False,
        "gluten_free": True,
        "dairy_free": False,
        "nut_free": True,
        "spicy_level": 1,
        "difficulty": "Easy"
    },
    {
        "title": "Gluten-Free Pancakes",
        "description": "Fluffy gluten-free pancakes perfect for a weekend breakfast.",
        "ingredients": json.dumps(["200g gluten-free flour blend", "2 tsp baking powder", "1/2 tsp salt", "1 tbsp sugar", "2 eggs", "240ml milk", "2 tbsp melted butter", "1 tsp vanilla extract", "Maple syrup for serving"]),
        "instructions": "1. Mix dry ingredients in a bowl.\n2. Whisk wet ingredients in another bowl.\n3. Combine wet and dry ingredients until just mixed.\n4. Heat a greased pan over medium heat.\n5. Pour 1/4 cup of batter for each pancake.\n6. Flip when bubbles appear on surface.\n7. Cook until golden brown on both sides.",
        "cuisine_type": "American",
        "meal_type": "Breakfast",
        "prep_time": 10,
        "cook_time": 15,
        "vegetarian": True,
        "vegan": False,
        "gluten_free": True,
        "dairy_free": False,
        "nut_free": True,
        "spicy_level": 1,
        "difficulty": "Easy"
    },
    {
        "title": "Spicy Thai Curry",
        "description": "Aromatic and spicy Thai red curry with vegetables.",
        "ingredients": json.dumps(["400ml coconut milk", "3 tbsp red curry paste", "1 cup mixed vegetables", "200g tofu", "2 kaffir lime leaves", "1 tbsp soy sauce", "1 tsp brown sugar", "Fresh Thai basil", "1 red chili", "1 tbsp vegetable oil"]),
        "instructions": "1. Heat oil in a pot over medium heat.\n2. Add curry paste and stir for 1 minute.\n3. Add coconut milk and bring to a simmer.\n4. Add vegetables, tofu, lime leaves, soy sauce, and sugar.\n5. Simmer for 10 minutes until vegetables are tender.\n6. Garnish with Thai basil and sliced chili.",
        "cuisine_type": "Thai",
        "meal_type": "Dinner",
        "prep_time": 15,
        "cook_time": 20,
        "vegetarian": True,
        "vegan": True,
        "gluten_free": True,
        "dairy_free": True,
        "nut_free": False,
        "spicy_level": 4,
        "difficulty": "Medium"
    },
    {
        "title": "Beef Bourguignon",
        "description": "Classic French beef stew with red wine, bacon, and mushrooms.",
        "ingredients": json.dumps(["800g beef chuck", "200g bacon", "2 onions", "2 carrots", "2 celery stalks", "4 garlic cloves", "2 cups red wine", "2 cups beef stock", "200g mushrooms", "2 tbsp tomato paste", "2 bay leaves", "Fresh thyme", "2 tbsp flour", "2 tbsp butter"]),
        "instructions": "1. Brown beef and bacon in a Dutch oven.\n2. Add onions, carrots, celery, and garlic.\n3. Add wine, stock, tomato paste, and herbs.\n4. Simmer covered for 2.5 hours.\n5. Sauté mushrooms separately.\n6. Mix butter and flour, add to stew.\n7. Add mushrooms and cook 30 more minutes.",
        "cuisine_type": "French",
        "meal_type": "Dinner",
        "prep_time": 30,
        "cook_time": 180,
        "vegetarian": False,
        "vegan": False,
        "gluten_free": False,
        "dairy_free": False,
        "nut_free": True,
        "spicy_level": 1,
        "difficulty": "Hard"
    },
    {
        "title": "Quick Avocado Toast",
        "description": "Simple yet delicious avocado toast with various toppings.",
        "ingredients": json.dumps(["2 slices whole grain bread", "1 ripe avocado", "1 tbsp lemon juice", "Salt and pepper", "Red pepper flakes", "Optional toppings: cherry tomatoes, feta cheese, microgreens"]),
        "instructions": "1. Toast bread until golden and crisp.\n2. Mash avocado with lemon juice, salt, and pepper.\n3. Spread avocado mixture on toast.\n4. Add toppings of choice.\n5. Sprinkle with red pepper flakes.",
        "cuisine_type": "American",
        "meal_type": "Breakfast",
        "prep_time": 5,
        "cook_time": 5,
        "vegetarian": True,
        "vegan": True,
        "gluten_free": False,
        "dairy_free": True,
        "nut_free": True,
        "spicy_level": 2,
        "difficulty": "Easy"
    },
    {
        "title": "Vegetarian Sushi Rolls",
        "description": "Colorful vegetarian sushi rolls with avocado, cucumber, and carrot.",
        "ingredients": json.dumps(["2 cups sushi rice", "1/4 cup rice vinegar", "1 tbsp sugar", "1 tsp salt", "5 nori sheets", "1 avocado", "1 cucumber", "2 carrots", "Soy sauce", "Wasabi", "Pickled ginger"]),
        "instructions": "1. Cook sushi rice according to package instructions.\n2. Mix rice vinegar, sugar, and salt; fold into cooked rice.\n3. Slice vegetables into thin strips.\n4. Place nori sheet on bamboo mat, cover with rice.\n5. Add vegetable strips in the center.\n6. Roll tightly and slice into pieces.\n7. Serve with soy sauce, wasabi, and pickled ginger.",
        "cuisine_type": "Japanese",
        "meal_type": "Lunch",
        "prep_time": 30,
        "cook_time": 20,
        "vegetarian": True,
        "vegan": True,
        "gluten_free": True,
        "dairy_free": True,
        "nut_free": True,
        "spicy_level": 1,
        "difficulty": "Medium"
    }
]

def seed_recipes():
    db = SessionLocal()
    try:
        # Check if we already have recipes
        existing_count = db.query(Recipe).count()
        if existing_count > 0:
            print(f"Database already has {existing_count} recipes. Skipping seed.")
            return
        
        # Add sample recipes
        for recipe_data in SAMPLE_RECIPES:
            recipe = Recipe(**recipe_data)
            db.add(recipe)
        
        db.commit()
        print(f"Successfully added {len(SAMPLE_RECIPES)} sample recipes to the database.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_recipes() 