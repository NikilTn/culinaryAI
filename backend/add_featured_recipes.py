import sys
import json
from sqlalchemy.orm import Session
from models.recipe import Recipe
from database.database import SessionLocal

# Featured recipes that will be shown to all users
FEATURED_RECIPES = [
    {
        "title": "Classic Margherita Pizza",
        "description": "A simple yet delicious traditional Italian pizza with fresh mozzarella and basil.",
        "ingredients": json.dumps(["Pizza dough", "San Marzano tomatoes", "Fresh mozzarella", "Fresh basil", "Olive oil", "Salt"]),
        "instructions": json.dumps(["Preheat oven to 500°F (260°C) with pizza stone if available.", "Roll out dough into a 12-inch circle.", "Top with crushed tomatoes, torn mozzarella, and a drizzle of olive oil.", "Bake for 8-10 minutes until crust is golden.", "Add fresh basil leaves and a pinch of salt after baking."]),
        "cooking_time": 20,
        "difficulty": "Medium",
        "cuisine": "Italian",
        "dietary_restrictions": json.dumps(["vegetarian"]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Beef Wellington",
        "description": "A classic gourmet dish featuring beef tenderloin wrapped in puff pastry with mushroom duxelles.",
        "ingredients": json.dumps(["Beef tenderloin", "Puff pastry", "Mushrooms", "Prosciutto", "Dijon mustard", "Egg wash", "Shallots", "Garlic", "Thyme", "Olive oil", "Salt", "Pepper"]),
        "instructions": json.dumps(["Sear beef tenderloin on all sides.", "Chill beef completely.", "Make mushroom duxelles by finely chopping and cooking mushrooms with herbs.", "Lay out prosciutto, spread with duxelles, place beef in center.", "Wrap beef in prosciutto mixture, then in puff pastry.", "Brush with egg wash, score decoratively.", "Bake at 400°F (200°C) for 35-40 minutes for medium-rare."]),
        "cooking_time": 120,
        "difficulty": "Hard",
        "cuisine": "British",
        "dietary_restrictions": json.dumps([]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Thai Green Curry",
        "description": "A fragrant and spicy Thai curry with coconut milk and fresh vegetables.",
        "ingredients": json.dumps(["Green curry paste", "Coconut milk", "Chicken or tofu", "Thai eggplants", "Bell peppers", "Bamboo shoots", "Thai basil", "Fish sauce", "Palm sugar", "Kaffir lime leaves", "Thai chilis"]),
        "instructions": json.dumps(["Heat coconut milk in a pot until it begins to separate.", "Add green curry paste and stir for 2 minutes.", "Add protein (chicken or tofu) and cook until nearly done.", "Add vegetables and simmer until tender.", "Season with fish sauce and palm sugar.", "Garnish with Thai basil and sliced chilis."]),
        "cooking_time": 30,
        "difficulty": "Medium",
        "cuisine": "Thai",
        "dietary_restrictions": json.dumps(["dairy-free"]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Quinoa Buddha Bowl",
        "description": "A nutritious and colorful bowl packed with plant-based protein and vegetables.",
        "ingredients": json.dumps(["Quinoa", "Avocado", "Chickpeas", "Sweet potato", "Kale", "Red cabbage", "Tahini", "Lemon juice", "Maple syrup", "Cumin", "Salt", "Pepper"]),
        "instructions": json.dumps(["Cook quinoa according to package instructions.", "Roast diced sweet potatoes with cumin, salt, and pepper.", "Massage kale with olive oil and salt.", "Arrange all ingredients in sections in a bowl.", "Whisk together tahini, lemon juice, maple syrup, and water for dressing.", "Drizzle dressing over the bowl."]),
        "cooking_time": 40,
        "difficulty": "Easy",
        "cuisine": "International",
        "dietary_restrictions": json.dumps(["vegan", "gluten-free", "dairy-free"]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Classic French Onion Soup",
        "description": "A rich and savory soup topped with melted Gruyère cheese and crunchy bread.",
        "ingredients": json.dumps(["Yellow onions", "Beef broth", "White wine", "Baguette", "Gruyère cheese", "Butter", "Olive oil", "Thyme", "Bay leaf", "Flour", "Salt", "Pepper"]),
        "instructions": json.dumps(["Slice onions thinly.", "Caramelize onions in butter and oil for 45 minutes, stirring occasionally.", "Add flour and cook for 1 minute.", "Add wine to deglaze, then add broth, thyme, and bay leaf.", "Simmer for 30 minutes.", "Top with toasted baguette slices and Gruyère, then broil until cheese is bubbly."]),
        "cooking_time": 90,
        "difficulty": "Medium",
        "cuisine": "French",
        "dietary_restrictions": json.dumps([]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Miso Glazed Salmon",
        "description": "Tender salmon fillets with a sweet and savory miso glaze.",
        "ingredients": json.dumps(["Salmon fillets", "White miso paste", "Mirin", "Sake", "Soy sauce", "Brown sugar", "Ginger", "Green onions"]),
        "instructions": json.dumps(["Mix miso paste, mirin, sake, soy sauce, and brown sugar for glaze.", "Marinate salmon in glaze for at least 30 minutes.", "Preheat broiler.", "Broil salmon for 8-10 minutes until caramelized on top.", "Garnish with sliced green onions."]),
        "cooking_time": 25,
        "difficulty": "Easy",
        "cuisine": "Japanese",
        "dietary_restrictions": json.dumps(["gluten-free", "dairy-free"]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Chocolate Lava Cake",
        "description": "Decadent individual chocolate cakes with a molten chocolate center.",
        "ingredients": json.dumps(["Dark chocolate", "Butter", "Eggs", "Sugar", "Vanilla extract", "All-purpose flour", "Salt", "Powdered sugar for dusting"]),
        "instructions": json.dumps(["Preheat oven to 425°F (220°C).", "Melt chocolate and butter together.", "Whisk eggs, sugar, and vanilla in a separate bowl.", "Combine chocolate mixture with egg mixture.", "Fold in flour and salt.", "Pour into buttered ramekins.", "Bake for 12 minutes until edges are set but center is soft.", "Dust with powdered sugar and serve immediately."]),
        "cooking_time": 20,
        "difficulty": "Medium",
        "cuisine": "French",
        "dietary_restrictions": json.dumps(["vegetarian"]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Chicken Tikka Masala",
        "description": "Tender chicken in a creamy, aromatic tomato sauce with Indian spices.",
        "ingredients": json.dumps(["Chicken thighs", "Yogurt", "Lemon juice", "Garam masala", "Turmeric", "Cumin", "Coriander", "Ginger", "Garlic", "Tomato sauce", "Heavy cream", "Butter", "Cilantro"]),
        "instructions": json.dumps(["Marinate chicken in yogurt, lemon juice, and spices for at least 2 hours.", "Grill or broil chicken until charred and cooked through.", "In a separate pan, sauté garlic and ginger in butter.", "Add tomato sauce and spices, simmer for 10 minutes.", "Add cooked chicken and cream, simmer for 5 more minutes.", "Garnish with cilantro."]),
        "cooking_time": 60,
        "difficulty": "Medium",
        "cuisine": "Indian",
        "dietary_restrictions": json.dumps([]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Mediterranean Stuffed Bell Peppers",
        "description": "Colorful bell peppers stuffed with quinoa, vegetables, and feta cheese.",
        "ingredients": json.dumps(["Bell peppers", "Quinoa", "Zucchini", "Cherry tomatoes", "Red onion", "Garlic", "Feta cheese", "Kalamata olives", "Fresh herbs", "Olive oil", "Lemon juice", "Salt", "Pepper"]),
        "instructions": json.dumps(["Cook quinoa according to package instructions.", "Sauté diced zucchini, tomatoes, onion, and garlic.", "Mix vegetables with quinoa, crumbled feta, olives, and herbs.", "Season with olive oil, lemon juice, salt, and pepper.", "Cut tops off peppers and remove seeds.", "Fill peppers with quinoa mixture.", "Bake at 375°F (190°C) for 25-30 minutes."]),
        "cooking_time": 45,
        "difficulty": "Easy",
        "cuisine": "Mediterranean",
        "dietary_restrictions": json.dumps(["vegetarian", "gluten-free"]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Classic Beef Tacos",
        "description": "Traditional Mexican-style tacos with seasoned ground beef and fresh toppings.",
        "ingredients": json.dumps(["Ground beef", "Corn tortillas", "Onion", "Garlic", "Tomatoes", "Lettuce", "Cheese", "Sour cream", "Avocado", "Lime", "Cilantro", "Taco seasoning"]),
        "instructions": json.dumps(["Brown ground beef with diced onion and garlic.", "Add taco seasoning and water, simmer until thickened.", "Warm corn tortillas in a dry skillet.", "Assemble tacos with beef and toppings of choice."]),
        "cooking_time": 25,
        "difficulty": "Easy",
        "cuisine": "Mexican",
        "dietary_restrictions": json.dumps([]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Mushroom Risotto",
        "description": "Creamy Italian rice dish with mushrooms and Parmesan cheese.",
        "ingredients": json.dumps(["Arborio rice", "Mixed mushrooms", "Vegetable or chicken broth", "White wine", "Shallots", "Garlic", "Butter", "Parmesan cheese", "Thyme", "Olive oil", "Salt", "Pepper"]),
        "instructions": json.dumps(["Sauté mushrooms in olive oil until golden, set aside.", "In the same pan, sauté shallots and garlic in butter.", "Add rice and toast for 2 minutes.", "Add wine and stir until absorbed.", "Add hot broth one ladle at a time, stirring constantly.", "Continue adding broth until rice is creamy and al dente.", "Stir in mushrooms, Parmesan, and remaining butter.", "Season with salt and pepper."]),
        "cooking_time": 40,
        "difficulty": "Medium",
        "cuisine": "Italian",
        "dietary_restrictions": json.dumps(["vegetarian"]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Lemon Garlic Roast Chicken",
        "description": "Juicy roast chicken with bright lemon and garlic flavors.",
        "ingredients": json.dumps(["Whole chicken", "Lemons", "Garlic", "Fresh herbs", "Butter", "Olive oil", "Salt", "Pepper", "Chicken broth"]),
        "instructions": json.dumps(["Preheat oven to 425°F (220°C).", "Mix softened butter with lemon zest, garlic, and herbs.", "Rub butter mixture under and over chicken skin.", "Stuff cavity with lemon halves and garlic cloves.", "Tie legs together and tuck wings.", "Roast for 1 hour and 15 minutes, basting occasionally.", "Let rest for 15 minutes before carving."]),
        "cooking_time": 90,
        "difficulty": "Medium",
        "cuisine": "American",
        "dietary_restrictions": json.dumps(["gluten-free", "dairy-free"]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Vietnamese Pho",
        "description": "Traditional Vietnamese noodle soup with aromatic broth and fresh herbs.",
        "ingredients": json.dumps(["Beef bones", "Beef brisket or sirloin", "Rice noodles", "Bean sprouts", "Thai basil", "Cilantro", "Lime", "Jalapeños", "Hoisin sauce", "Sriracha", "Star anise", "Cinnamon sticks", "Ginger", "Onion", "Fish sauce"]),
        "instructions": json.dumps(["Roast bones, ginger, and onion until charred.", "Simmer bones and meat with spices in water for 3-4 hours.", "Strain broth and adjust seasoning with fish sauce.", "Cook rice noodles according to package instructions.", "Slice meat thinly.", "Serve by placing noodles in bowl, topping with meat and pouring hot broth over.", "Garnish with herbs and condiments."]),
        "cooking_time": 240,
        "difficulty": "Hard",
        "cuisine": "Vietnamese",
        "dietary_restrictions": json.dumps([]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Spanish Paella",
        "description": "Iconic Spanish rice dish with saffron, seafood, and meats.",
        "ingredients": json.dumps(["Bomba rice", "Chicken thighs", "Chorizo", "Shrimp", "Mussels", "Bell peppers", "Tomatoes", "Onion", "Garlic", "Saffron", "Paprika", "Chicken broth", "White wine", "Olive oil", "Peas", "Lemon wedges"]),
        "instructions": json.dumps(["Heat olive oil in a paella pan.", "Brown chicken and chorizo, then remove.", "Sauté peppers, onion, and garlic.", "Add rice and toast for 2 minutes.", "Stir in saffron, paprika, and wine.", "Add broth and return chicken and chorizo to the pan.", "Simmer uncovered for 15 minutes.", "Arrange seafood on top and continue cooking until rice is done and seafood is cooked.", "Garnish with peas and lemon wedges."]),
        "cooking_time": 60,
        "difficulty": "Hard",
        "cuisine": "Spanish",
        "dietary_restrictions": json.dumps([]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Classic Caesar Salad",
        "description": "Crisp romaine lettuce with creamy dressing, Parmesan, and croutons.",
        "ingredients": json.dumps(["Romaine lettuce", "Parmesan cheese", "Croutons", "Anchovy fillets", "Garlic", "Egg yolks", "Dijon mustard", "Olive oil", "Lemon juice", "Worcestershire sauce", "Salt", "Black pepper"]),
        "instructions": json.dumps(["Whisk together minced anchovies, garlic, egg yolks, mustard, and Worcestershire sauce.", "Slowly whisk in olive oil to emulsify.", "Add lemon juice, salt, and pepper.", "Toss romaine lettuce with enough dressing to coat.", "Add shaved Parmesan and croutons.", "Toss gently and serve immediately."]),
        "cooking_time": 15,
        "difficulty": "Easy",
        "cuisine": "American",
        "dietary_restrictions": json.dumps(["vegetarian"]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Vegetable Biryani",
        "description": "Fragrant Indian rice dish layered with spiced vegetables.",
        "ingredients": json.dumps(["Basmati rice", "Mixed vegetables", "Onions", "Tomatoes", "Ginger", "Garlic", "Green chilis", "Yogurt", "Biryani masala", "Turmeric", "Cinnamon", "Cardamom", "Cloves", "Bay leaves", "Saffron", "Milk", "Ghee", "Cilantro", "Mint leaves"]),
        "instructions": json.dumps(["Soak rice for 30 minutes, then parboil with whole spices.", "Sauté onions until golden brown.", "Add ginger, garlic, and green chilis, then vegetables.", "Add tomatoes, spices, and yogurt, cook until vegetables are tender.", "Layer half-cooked rice and vegetable mixture in a pot.", "Top with saffron milk, mint, and cilantro.", "Cover tightly and cook on low heat for 20 minutes.", "Mix gently before serving."]),
        "cooking_time": 60,
        "difficulty": "Medium",
        "cuisine": "Indian",
        "dietary_restrictions": json.dumps(["vegetarian", "gluten-free"]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Homemade Pasta Carbonara",
        "description": "Traditional Italian pasta dish with eggs, cheese, pancetta, and black pepper.",
        "ingredients": json.dumps(["Spaghetti", "Pancetta or guanciale", "Eggs", "Pecorino Romano cheese", "Parmesan cheese", "Black pepper", "Salt"]),
        "instructions": json.dumps(["Cook pasta in salted water until al dente.", "While pasta cooks, sauté pancetta until crispy.", "In a bowl, whisk eggs, grated cheeses, and black pepper.", "Drain pasta, reserving some pasta water.", "While pasta is still hot, quickly mix with egg mixture off the heat.", "Add pancetta and enough pasta water to create a creamy sauce.", "Serve immediately with extra cheese and pepper."]),
        "cooking_time": 20,
        "difficulty": "Medium",
        "cuisine": "Italian",
        "dietary_restrictions": json.dumps([]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Black Bean Sweet Potato Chili",
        "description": "Hearty vegetarian chili with sweet potatoes, black beans, and warming spices.",
        "ingredients": json.dumps(["Black beans", "Sweet potatoes", "Onion", "Bell peppers", "Garlic", "Diced tomatoes", "Vegetable broth", "Chili powder", "Cumin", "Smoked paprika", "Oregano", "Olive oil", "Salt", "Pepper", "Lime", "Avocado", "Cilantro"]),
        "instructions": json.dumps(["Sauté onions, peppers, and garlic in olive oil.", "Add spices and cook until fragrant.", "Add diced sweet potatoes, tomatoes, and vegetable broth.", "Simmer for 15 minutes until sweet potatoes start to soften.", "Add black beans and simmer for another 15 minutes.", "Adjust seasoning with salt and pepper.", "Serve with lime wedges, diced avocado, and cilantro."]),
        "cooking_time": 45,
        "difficulty": "Easy",
        "cuisine": "American",
        "dietary_restrictions": json.dumps(["vegan", "gluten-free", "dairy-free"]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Crispy Baked Falafel",
        "description": "Baked chickpea patties with herbs and spices, perfect in pita or salad.",
        "ingredients": json.dumps(["Dried chickpeas", "Onion", "Garlic", "Parsley", "Cilantro", "Cumin", "Coriander", "Paprika", "Baking powder", "Flour", "Salt", "Pepper", "Olive oil"]),
        "instructions": json.dumps(["Soak dried chickpeas overnight, do not use canned chickpeas.", "Drain chickpeas and process with herbs, spices, and aromatics.", "Add baking powder and just enough flour to bind.", "Form into balls or patties.", "Brush with olive oil and bake at 375°F (190°C) for 25-30 minutes, flipping halfway.", "Serve in pita bread with tahini sauce and fresh vegetables."]),
        "cooking_time": 40,
        "difficulty": "Medium",
        "cuisine": "Middle Eastern",
        "dietary_restrictions": json.dumps(["vegan", "dairy-free"]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    },
    {
        "title": "Korean Bibimbap",
        "description": "Colorful rice bowl topped with vegetables, protein, and gochujang sauce.",
        "ingredients": json.dumps(["Rice", "Spinach", "Bean sprouts", "Carrots", "Zucchini", "Mushrooms", "Beef or tofu", "Eggs", "Gochujang paste", "Soy sauce", "Sesame oil", "Garlic", "Sugar", "Sesame seeds", "Vegetable oil"]),
        "instructions": json.dumps(["Cook rice and set aside.", "Season beef or tofu with soy sauce, garlic, and sesame oil, then cook.", "Separately sauté each vegetable with salt and garlic.", "Fry eggs sunny-side up.", "Mix gochujang with sesame oil, soy sauce, and sugar for sauce.", "Arrange rice in bowls topped with vegetables, protein, and egg.", "Serve with gochujang sauce on the side."]),
        "cooking_time": 50,
        "difficulty": "Medium",
        "cuisine": "Korean",
        "dietary_restrictions": json.dumps([]),
        "is_ai_generated": False,
        "generated_for_user_id": None
    }
]

def add_featured_recipes():
    db = SessionLocal()
    try:
        # Check if these recipes already exist by title
        existing_titles = [r.title for r in db.query(Recipe.title).all()]
        recipes_to_add = [r for r in FEATURED_RECIPES if r["title"] not in existing_titles]
        
        if not recipes_to_add:
            print("All featured recipes already exist in the database.")
            return
        
        # Add new featured recipes
        for recipe_data in recipes_to_add:
            recipe = Recipe(**recipe_data)
            db.add(recipe)
        
        db.commit()
        print(f"Successfully added {len(recipes_to_add)} featured recipes to the database.")
    except Exception as e:
        db.rollback()
        print(f"Error adding featured recipes: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    add_featured_recipes() 