"""
Database Schemas for the Gaming Website

Each Pydantic model corresponds to a MongoDB collection. Collection name is the
lowercased class name (e.g., Game -> "game").
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal

class User(BaseModel):
    username: str = Field(..., min_length=2, max_length=30, description="Unique username")
    avatar_url: Optional[HttpUrl] = Field(None, description="Avatar image URL")

class Game(BaseModel):
    title: str = Field(..., min_length=2, max_length=80)
    description: str = Field(..., min_length=10, max_length=240)
    category: Literal["Puzzle", "Adventure", "Action", "Kids Learning"]
    thumbnail: Optional[HttpUrl] = Field(None, description="Preview image URL")
    plays: int = Field(0, ge=0)

class Leaderboardentry(BaseModel):
    game_id: str = Field(..., description="Related game _id as string")
    user_id: str = Field(..., description="Related user _id as string")
    username: str = Field(..., description="Username snapshot at time of score")
    score: int = Field(..., ge=0)
