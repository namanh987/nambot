"""
test_api.py — run this BEFORE starting the FastAPI server to verify your API keys work.
Usage:  python test_api.py
"""

import os, asyncio, httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

TEST_MESSAGES = [{"role": "user", "content": "What is 2 + 2? One sentence only."}]


async def test_nambot():
    print("\n── NAMBOT (Groq / Llama 3.3 70B) ──────────────────────")
    if not GROQ_API_KEY:
        print("  ✗  GROQ_API_KEY not set in .env")
        return

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "max_tokens": 100,
                    "messages": TEST_MESSAGES,
                },
            )
        if res.status_code == 200:
            data = res.json()
            reply = data["choices"][0]["message"]["content"]
            tokens = data["usage"]["total_tokens"]
            print(f"  ✓  Reply : {reply.strip()}")
            print(f"  ✓  Tokens: {tokens}")
        else:
            print(f"  ✗  HTTP {res.status_code}: {res.text[:300]}")
    except Exception as e:
        print(f"  ✗  Exception: {e}")


async def test_anhbot():
    print("\n── ANHBOT (GitHub Models / GPT-4o) ────────────────")
    if not GITHUB_TOKEN:
        print("  ✗  GITHUB_TOKEN not set in .env")
        return

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                "https://models.inference.ai.azure.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o",
                    "max_tokens": 200,
                    "messages": TEST_MESSAGES,
                },
            )
        if res.status_code == 200:
            data = res.json()
            reply = data["choices"][0]["message"]["content"]
            tokens = data["usage"]["total_tokens"]
            print(f"  ✓  Reply : {reply.strip()[:120]}")
            print(f"  ✓  Tokens: {tokens}")
        else:
            print(f"  ✗  HTTP {res.status_code}: {res.text[:300]}")
    except Exception as e:
        print(f"  ✗  Exception: {e}")


async def main():
    print("=" * 55)
    print("  Nambot API Key Tester")
    print("=" * 55)
    print(f"  GROQ_API_KEY : {'set ✓' if GROQ_API_KEY else 'MISSING ✗'}")
    print(f"  GITHUB_TOKEN : {'set ✓' if GITHUB_TOKEN else 'MISSING ✗'}")

    await test_nambot()
    await test_anhbot()

    print("\n" + "=" * 55)
    print("  Done. Fix any ✗ above before starting the server.")
    print("=" * 55 + "\n")


asyncio.run(main())