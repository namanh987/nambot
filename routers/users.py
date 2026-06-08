from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, User, UsageLog
from auth_utils import get_current_user

router = APIRouter()


@router.get("/me")
def get_profile(user: User = Depends(get_current_user)):
    return {
        "email":         user.email,
        "plan":          user.plan,
        "token_balance": user.token_balance,
        "created_at":    user.created_at,
    }


@router.get("/history")
def get_history(
    limit:  int     = 20,
    user:   User    = Depends(get_current_user),
    db:     Session = Depends(get_db),
):
    logs = (
        db.query(UsageLog)
        .filter(UsageLog.user_id == user.id)
        .order_by(UsageLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "bot":         log.bot,
            "question":    log.question,
            "tokens_used": log.tokens_used,
            "timestamp":   log.timestamp,
        }
        for log in logs
    ]
