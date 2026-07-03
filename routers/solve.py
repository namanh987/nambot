from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
from database import get_db, User, UsageLog
from model_router import call_bot, PLAN_BOTS, GUEST_BOTS, GUEST_PROMPT_LIMIT, build_user_content

router = APIRouter()


class SolveRequest(BaseModel):
    bot:         str
    messages:    List[Dict]
    guest_count: Optional[int] = 0
    image_b64:   Optional[str] = None    # base64 encoded image
    image_mime:  Optional[str] = "image/jpeg"


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
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

    # ── BUILD MESSAGES WITH OPTIONAL IMAGE ───────────────────────────────
    messages = list(body.messages)

    if body.image_b64 and messages:
        last = dict(messages[-1])
        if last.get("role") == "user":
            last["content"] = build_user_content(
                last.get("content", ""),
                body.image_b64,
                body.image_mime or "image/jpeg",
            )
            messages[-1] = last
    elif body.image_b64:
        messages = [{
            "role": "user",
            "content": build_user_content(
                "Please solve the math problem in this image.",
                body.image_b64,
                body.image_mime or "image/jpeg",
            )
        }]

    # ── CALL AI ──────────────────────────────────────────────────────────
    try:
        result = await call_bot(body.bot, messages)
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
                (m["content"] if isinstance(m["content"], str) else "[image]"
                 for m in reversed(body.messages) if m["role"] == "user"), ""
            )[:300],
            tokens_used=tokens_used,
        )
        db.add(log)
        db.commit()
        db.refresh(user)

    return {
        "reply":              result["reply"],
        "tokens_used":        tokens_used,
        "token_balance":      user.token_balance if user else None,
        "guest_prompt_limit": GUEST_PROMPT_LIMIT if not user else None,
    }