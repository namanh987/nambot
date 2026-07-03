import os, httpx
from typing import List, Dict, Optional

# ─────────────────────────────────────────────
#  BOT DEFINITIONS
#  nambot → Groq / llama-4-scout (vision, free)
#  anhbot → GitHub Models / gpt-4o (vision, free)
# ─────────────────────────────────────────────

BOT_CONFIG = {

    "nambot": {
        "api_url": "https://api.groq.com/openai/v1/chat/completions",
        "headers": lambda: {
            "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
            "Content-Type":  "application/json",
        },
        "system": (
            "You are Nambot, a brilliant math tutor powered by Llama 4 Scout on Groq. "
            "If the user sends an image of a math problem, read it carefully and solve it. "
            "Show clear numbered steps, use plain text notation, "
            "label the final result as 'Answer:' and add a brief tip."
        ),
        "build_body": lambda messages, system: {
            "model":      "meta-llama/llama-4-scout-17b-16e-instruct",
            "max_tokens": 1500,
            "messages":   [{"role": "system", "content": system}] + messages,
        },
        "parse_reply":  lambda data: data["choices"][0]["message"]["content"],
        "parse_tokens": lambda data: data["usage"]["total_tokens"],
    },

    "anhbot": {
        "api_url": "https://models.inference.ai.azure.com/chat/completions",
        "headers": lambda: {
            "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
            "Content-Type":  "application/json",
        },
        "system": (
            "You are AnhBot, a rigorous math solver powered by GPT-4o via GitHub Models. "
            "If the user sends an image of a math problem, read it carefully and solve it. "
            "Think step by step. Show clear numbered derivations, note edge cases, "
            "and label the final result as 'Answer:' clearly."
        ),
        "build_body": lambda messages, system: {
            "model":      "gpt-4o",
            "max_tokens": 1500,
            "messages":   [{"role": "system", "content": system}] + messages,
        },
        "parse_reply":  lambda data: data["choices"][0]["message"]["content"],
        "parse_tokens": lambda data: data["usage"]["total_tokens"],
    },
}

# ─────────────────────────────────────────────
#  ACCESS RULES
# ─────────────────────────────────────────────

GUEST_PROMPT_LIMIT = 10

PLAN_LIMITS = {
    "free":      50_000,
    "pro":       500_000,
    "unlimited": 999_999_999,
}

PLAN_BOTS  = { plan: ["nambot", "anhbot"] for plan in PLAN_LIMITS }
GUEST_BOTS = ["nambot"]


# ─────────────────────────────────────────────
#  HELPERS — build vision-aware message content
# ─────────────────────────────────────────────

def build_user_content(text: str, image_b64: Optional[str] = None, image_mime: str = "image/jpeg"):
    """Return OpenAI-compatible content — plain text or [text + image] list."""
    if not image_b64:
        return text
    return [
        {"type": "text", "text": text or "Please solve the math problem in this image."},
        {"type": "image_url", "image_url": {"url": f"data:{image_mime};base64,{image_b64}"}},
    ]


# ─────────────────────────────────────────────
#  CALLER
# ─────────────────────────────────────────────

async def call_bot(bot: str, messages: List[Dict]) -> Dict:
    cfg  = BOT_CONFIG[bot]
    url  = cfg["api_url"]() if callable(cfg["api_url"]) else cfg["api_url"]
    body = cfg["build_body"](messages, cfg["system"])

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers=cfg["headers"](), json=body)
        response.raise_for_status()
        data = response.json()

    return {
        "reply":  cfg["parse_reply"](data),
        "tokens": cfg["parse_tokens"](data),
    }