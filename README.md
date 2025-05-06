# CulinaryAI Development Roadmap

## Phase 1: Project Initialization

- Set up the project repository.
- Initialize the React frontend and FastAPI backend.
- Configure PostgreSQL database and environment variables.

## Phase 2: User Authentication

- Implement signup and login functionalities.
- Secure endpoints using JWT authentication.
- Create user profile models and database schemas.

## Phase 3: Questionnaire and Preferences

- Develop the questionnaire component to capture user preferences.
- Store preferences in the database linked to user profiles.
- Ensure the frontend communicates correctly with the backend APIs.

## Phase 4: Recommendation Engine

- Integrate OpenAI's API to generate culinary recommendations.
- Develop algorithms using TF-IDF and cosine similarity.
- Display personalized recommendations on the frontend.

## Phase 5: Search and Filters

- Implement search functionality with filters for cuisine, dish type, and dietary restrictions.
- Optimize database queries for performance.
- Enhance the UI/UX for better user interaction with minimalistic styles and smooth animations.

## Phase 6: Deployment

- Prepare the application for deployment on AWS EC2 instances.
- Set up CI/CD pipelines for automated testing and deployment.
- Monitor application performance and handle scaling.

## Setup Instructions

### Prerequisites

- Node.js and npm
- Python 3.8+
- PostgreSQL

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Copy the environment variables example file and update with your values:
   ```
   copy .env.example .env  # Windows
   cp .env.example .env  # Linux/Mac
   ```

5. Run the development server:
   ```
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm start
   ```

### Database Setup

1. Create a PostgreSQL database:
   ```
   CREATE DATABASE culinaryai;
   ```

2. Configure the database connection in the `.env` file.

### Adding Featured Recipes

To add the 20 featured recipes that will be shown to all users regardless of their preferences:

1. Make sure your backend server is running
2. Navigate to the backend directory:
   ```
   cd backend
   ```
3. Run the featured recipes script:
   ```
   python add_featured_recipes.py
   ```

This will add 20 diverse recipes to the database that will be shown in the "Featured Recipes" section of the recommendations page.
