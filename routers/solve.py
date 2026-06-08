from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
from database import get_db, User, UsageLog
from model_router import call_bot, PLAN_BOTS, GUEST_BOTS, GUEST_PROMPT_LIMIT

router = APIRouter()


class SolveRequest(BaseModel):
    bot:           str
    messages:      List[Dict]
    guest_count:   Optional[int] = 0   # frontend sends how many prompts guest has used


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Returns the User if a valid JWT is present, otherwise None (guest)."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    try:
        from auth_utils import SECRET_KEY, ALGORITHM
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return db.query(User).filter(User.id == user_id).first()
    except Exception:
        return None


@router.post("/")
async def solve(
    body:    SolveRequest,
    request: Request,
    db:      Session = Depends(get_db),
):
    user = get_optional_user(request, db)

    # ── GUEST ────────────────────────────────────────────────────────────
    if user is None:
        if body.bot not in GUEST_BOTS:
            raise HTTPException(
                status_code=401,
                detail=f"'{body.bot}' requires an account. Please register to continue."
            )
        if body.guest_count >= GUEST_PROMPT_LIMIT:
            raise HTTPException(
                status_code=403,
                detail=f"Guest limit reached ({GUEST_PROMPT_LIMIT} prompts). "
                       "Please register for unlimited access."
            )

    # ── REGISTERED ───────────────────────────────────────────────────────
    else:
        allowed = PLAN_BOTS.get(user.plan, GUEST_BOTS)
        if body.bot not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"'{body.bot}' is not available on your '{user.plan}' plan."
            )
        if user.token_balance <= 0:
            raise HTTPException(
                status_code=402,
                detail="Token balance exhausted. Please upgrade your plan."
            )

    # ── CALL AI ──────────────────────────────────────────────────────────
    try:
        result = await call_bot(body.bot, body.messages)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI API error: {str(e)}")

    tokens_used = result["tokens"]

    # ── LOG + DEDUCT (registered only) ───────────────────────────────────
    if user:
        user.token_balance = max(0, user.token_balance - tokens_used)
        log = UsageLog(
            user_id=user.id,
            bot=body.bot,
            question=next(
                (m["content"] for m in reversed(body.messages) if m["role"] == "user"), ""
            )[:300],
            tokens_used=tokens_used,
        )
        db.add(log)
        db.commit()
        db.refresh(user)

    return {
        "reply":             result["reply"],
        "tokens_used":       tokens_used,
        "token_balance":     user.token_balance if user else None,
        "guest_prompt_limit": GUEST_PROMPT_LIMIT if not user else None,
    }
