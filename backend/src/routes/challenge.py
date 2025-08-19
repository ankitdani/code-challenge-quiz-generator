from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from ..ai_generator import generate_challenge_with_ai
from sqlalchemy.orm import Session
from ..database.db import (get_challenge_quota, create_challenge, create_challenge_quota, reset_quota_if_needed, get_user_challenges)
from ..utils import authenticate_get_user_request
from ..database.models import get_db
import json
from datetime import datetime

router = APIRouter()

# generate a challenge
class ChallengeRequest(BaseModel):
    difficulty: str

    class Config:
        json_schema_extra = {
            "example": {
                "difficulty": "easy"
            }
        }

@router.post("/generate-challenge")
async def generate_challenge(request: Request, challenge_request: ChallengeRequest, db: Session = Depends(get_db)):
    try:
        user_details = authenticate_get_user_request(request)
        user_id = user_details.get("user_id")

        quota = get_challenge_quota(db, user_id)
        if not quota:
            create_challenge_quota(db, user_id)
        quota = reset_quota_if_needed(db, quota)

        if quota.quota_remaining <= 0:
            raise HTTPException(status_code=429, detail="Quota exceeded")
        
        challenge_data = generate_challenge_with_ai(request.difficulty)
        new_challenge = create_challenge(
            db=db,
            difficulty=request.difficulty,
            created_by=user_id,
            **challenge_data
        )

        quota.quota_remaining -= 1
        db.commit()

        return {
            "id": new_challenge.id,
            "difficulty": new_challenge.difficulty,
            "title": new_challenge.title,
            "options": json.loads(new_challenge.options),
            "correct_answer_id": new_challenge.correct_answer_id,
            "explanation": new_challenge.explanation,
            "timestamp": new_challenge.date_created.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my_history")
async def my_history(request: Request, db: Session = Depends(get_db)):
    user_details = authenticate_get_user_request(request)
    user_id = user_details.get("user_id")
    challenges = get_user_challenges(db, user_id)
    return {"challenges": challenges}

@router.get("/quota")
async def get_quota(request: Request, db: Session = Depends(get_db)):
    user_details = authenticate_get_user_request(request)
    user_id = user_details.get("user_id")
    quota = get_challenge_quota(db, user_id)
    if not quota:
        return {"user_id": user_id, "quota": 0, "last_reset": datetime.now()}
    quota = reset_quota_if_needed(db, quota)
    return quota
    


