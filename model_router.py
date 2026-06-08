import os, httpx
from typing import List, Dict

# ─────────────────────────────────────────────
#  BOT DEFINITIONS
#  nambot → Groq  / llama-3.3-70b-versatile   (free, fast)
#  anhbot → GitHub Models / DeepSeek-R1        (free, deep reasoning)
# ─────────────────────────────────────────────

BOT_CONFIG = {

    "nambot": {
        "api_url": "https://api.groq.com/openai/v1/chat/completions",
        "headers": lambda: {
            "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
            "Content-Type":  "application/json",
        },
        "system": (
            "You are Nambot, a brilliant math tutor powered by Llama 3.3 70B. "
            "Show clear numbered steps, use plain text notation, "
            "label the final result as 'Answer:' and add a brief tip."
        ),
        "build_body": lambda messages, system: {
            "model":       "llama-3.3-70b-versatile",
            "max_tokens":  1500,
            "messages":    [{"role": "system", "content": system}] + messages,
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
            "You are AnhBot, a rigorous math solver powered by DeepSeek-R1. "
            "Think step by step with deep chain-of-thought reasoning. "
            "Show numbered derivations, note edge cases, "
            "and label the final result as 'Answer:' clearly."
        ),
        "build_body": lambda messages, system: {
            "model":       "DeepSeek-R1",
            "max_tokens":  1500,
            "messages":    [{"role": "system", "content": system}] + messages,
        },
        "parse_reply":  lambda data: data["choices"][0]["message"]["content"],
        "parse_tokens": lambda data: data["usage"]["total_tokens"],
    },
}

# ─────────────────────────────────────────────
#  ACCESS RULES
#  guest      → nambot only, max GUEST_PROMPT_LIMIT prompts (session-tracked on frontend)
#  registered → nambot + anhbot, token-balance based
# ─────────────────────────────────────────────

GUEST_PROMPT_LIMIT = 10          # unregistered users may send this many messages

PLAN_LIMITS = {
    "free":      50_000,
    "pro":       500_000,
    "unlimited": 999_999_999,
}

PLAN_BOTS = {
    "free":      ["nambot", "anhbot"],
    "pro":       ["nambot", "anhbot"],
    "unlimited": ["nambot", "anhbot"],
}

GUEST_BOTS = ["nambot"]          # guests can only use nambot


# ─────────────────────────────────────────────
#  CALLER
# ─────────────────────────────────────────────

async def call_bot(bot: str, messages: List[Dict]) -> Dict:
    cfg = BOT_CONFIG[bot]
    url = cfg["api_url"]() if callable(cfg["api_url"]) else cfg["api_url"]
    body = cfg["build_body"](messages, cfg["system"])

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers=cfg["headers"](), json=body)
        response.raise_for_status()
        data = response.json()

    return {
        "reply":  cfg["parse_reply"](data),
        "tokens": cfg["parse_tokens"](data),
    }
