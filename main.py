import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Game, User, Leaderboardentry

app = FastAPI(title="Gaming API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

def serialize_doc(doc: dict):
    if not doc:
        return doc
    doc["_id"] = str(doc.get("_id"))
    return doc

# Models for requests
class CreateUserRequest(BaseModel):
    username: str
    avatar_url: Optional[str] = None

class SubmitScoreRequest(BaseModel):
    user_id: str
    username: str
    score: int

# Routes
@app.get("/")
def root():
    return {"message": "Gaming API is running"}

@app.get("/api/games")
def list_games(category: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filt = {"category": category} if category else {}
    docs = get_documents("game", filt)
    return [serialize_doc(d) for d in docs]

@app.post("/api/games")
def create_game(game: Game):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    _id = create_document("game", game)
    return {"_id": _id}

@app.post("/api/users")
def create_user(payload: CreateUserRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Check if exists
    existing = db["user"].find_one({"username": payload.username})
    if existing:
        return serialize_doc(existing)
    _id = create_document("user", payload.model_dump())
    created = db["user"].find_one({"_id": ObjectId(_id)})
    return serialize_doc(created)

@app.get("/api/users/{user_id}")
def get_user(user_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    user = db["user"].find_one({"_id": PyObjectId.validate(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return serialize_doc(user)

@app.get("/api/leaderboard/{game_id}")
def get_leaderboard(game_id: str, limit: int = 10):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    entries = db["leaderboardentry"].find({"game_id": game_id}).sort("score", -1).limit(limit)
    return [serialize_doc(e) for e in entries]

@app.post("/api/leaderboard/{game_id}")
def submit_score(game_id: str, payload: SubmitScoreRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    if payload.score < 0:
        raise HTTPException(status_code=400, detail="Score must be non-negative")
    data = {
        "game_id": game_id,
        "user_id": payload.user_id,
        "username": payload.username,
        "score": payload.score,
    }
    _id = create_document("leaderboardentry", data)
    return {"_id": _id}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

@app.post("/api/seed")
def seed_games():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    if db["game"].count_documents({}) > 0:
        return {"status": "ok", "message": "Games already seeded"}
    samples = [
        {"title": "Neon Blocks", "description": "Stack and align glowing blocks in this chill puzzle.", "category": "Puzzle", "thumbnail": None, "plays": 0},
        {"title": "Cyber Runner", "description": "Dash through a synth city, dodge obstacles, collect cores.", "category": "Adventure", "thumbnail": None, "plays": 0},
        {"title": "Pulse Shooter", "description": "Arcade action with rhythmic enemy waves and power-ups.", "category": "Action", "thumbnail": None, "plays": 0},
        {"title": "ABC Quest", "description": "Learn letters and sounds with friendly characters.", "category": "Kids Learning", "thumbnail": None, "plays": 0},
    ]
    ids = []
    for s in samples:
        ids.append(create_document("game", s))
    return {"inserted": ids}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
