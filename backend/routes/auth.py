from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from database.database import get_db
from models.user import User
from schemas.user import UserCreate, UserResponse, Token
from utils.security import verify_password, get_password_hash, create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    identifier: str  # Can be email or username
    password: str

@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user and return access token
    """
    # Check if email already exists
    db_user_email = db.query(User).filter(User.email == user.email).first()
    if db_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    db_user_username = db.query(User).filter(User.username == user.username).first()
    if db_user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Generate token for the new user
    access_token = create_access_token(data={"sub": db_user.username})
    
    # Return token with user info
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "username": db_user.username
        }
    }

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 compatible token login using username/email and password
    """
    logger.info(f"OAuth2 login attempt with username: {form_data.username}")
    
    # Find user by username
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # If user not found, try finding by email
    if not user:
        logger.info(f"User not found by username, trying email")
        user = db.query(User).filter(User.email == form_data.username).first()
    
    # Log user found status
    if user:
        logger.info(f"User found: {user.username}")
        valid_password = verify_password(form_data.password, user.hashed_password)
        logger.info(f"Password valid: {valid_password}")
    else:
        logger.info("No user found")
    
    # Validate credentials
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token
    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"Generated token for user: {user.username}")
    
    # Return token with user info
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    }

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Custom login endpoint that accepts either username or email
    """
    logger.info(f"Login attempt with identifier: {login_data.identifier}")
    
    # Try to find user by username
    user = db.query(User).filter(User.username == login_data.identifier).first()
    
    # If not found, try by email
    if not user:
        logger.info(f"User not found by username, trying email")
        user = db.query(User).filter(User.email == login_data.identifier).first()
    
    # Log user found status
    if user:
        logger.info(f"User found: {user.username}")
        valid_password = verify_password(login_data.password, user.hashed_password)
        logger.info(f"Password valid: {valid_password}")
    else:
        logger.info("No user found")
    
    # Validate credentials
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
        )
    
    # Generate JWT token
    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"Generated token for user: {user.username}")
    
    # Return token with user info
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    } 