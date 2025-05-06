from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import routes
from routes import auth, users, preferences, recommendations

# Import models to ensure they are registered with SQLAlchemy
from models.user import User
from models.recipe import Recipe
from models.preference import UserPreference

app = FastAPI(title="CulinaryAI API", description="API for culinary recommendations")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(preferences.router)
app.include_router(recommendations.router)

# Make the '/recipes' endpoint available at the root level
@app.get("/recipes")
async def get_recipes_root(*args, **kwargs):
    """Proxy for /recommendations/recipes"""
    return await recommendations.get_recipes(*args, **kwargs)

@app.get("/")
async def root():
    return {"message": "Welcome to CulinaryAI API"} 