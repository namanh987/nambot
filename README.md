# Nambot — AI Math Assistant

A free AI-powered math solver with two bots, JWT authentication, and per-user usage tracking. Built with FastAPI.

**Live demo:** open `nambot.html` in any browser.

---

## Bots

| Bot | Model | Provider | Access |
|---|---|---|---|
| 🟢 **Nambot** | Llama 3.3 70B | Groq | Free — guests get 10 prompts, registered users unlimited |
| 🔴 **AnhBot** | GPT-4o | GitHub Models | Registered users only |

Both APIs are **completely free** — no credit card needed.

---

## Project structure

```
nambot-project/
├── main.py              # FastAPI app entry point
├── database.py          # SQLAlchemy models (User, UsageLog)
├── auth_utils.py        # JWT + bcrypt password hashing
├── model_router.py      # Bot definitions and API routing
├── routers/
│   ├── auth.py          # POST /auth/register  POST /auth/login
│   ├── solve.py         # POST /solve  (main chat endpoint)
│   └── users.py         # GET /users/me  GET /users/history
├── nambot.html          # Frontend (single file, no framework)
├── test_api.py          # API key tester — run before starting server
├── requirements.txt
└── .env.example
```

---

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/nambot.git
cd nambot
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Set up environment

```bash
cp .env.example .env
```

Fill in your `.env`:

```env
DATABASE_URL=sqlite:///./nambot.db
SECRET_KEY=your-long-random-string

GROQ_API_KEY=gsk_...        # console.groq.com — free, no credit card
GITHUB_TOKEN=ghp_...        # github.com/settings/tokens — classic token, no scopes needed
```

### 3. Test your API keys

```bash
python test_api.py
```

Both bots should show ✓ before you start the server.

### 4. Run

```bash
uvicorn main:app --reload
```

API docs: http://localhost:8000/docs

---

## API endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | None | Create account, returns JWT |
| `POST` | `/auth/login` | None | Login, returns JWT |
| `POST` | `/solve` | Optional | Send message, get AI response |
| `GET` | `/users/me` | Required | Profile + token balance |
| `GET` | `/users/history` | Required | Last 20 solved problems |

### `/solve` request body

```json
{
  "bot": "nambot",
  "messages": [{ "role": "user", "content": "Solve x² - 5x + 6 = 0" }],
  "guest_count": 3
}
```

- `bot` — `"nambot"` or `"anhbot"`
- `messages` — full conversation history
- `guest_count` — how many prompts the guest has already used (send `0` for registered users)

### `/solve` response

```json
{
  "reply": "Step 1: ...\nAnswer: x = 2 or x = 3",
  "tokens_used": 312,
  "token_balance": 49688,
  "guest_prompt_limit": null
}
```

---

## Access rules

| User type | Bots available | Limit |
|---|---|---|
| Guest (no login) | Nambot only | 10 prompts total |
| Registered — free plan | Nambot + AnhBot | 50,000 tokens |
| Registered — pro plan | Nambot + AnhBot | 500,000 tokens |
| Registered — unlimited | Nambot + AnhBot | Unlimited |

---

## Sharing / deployment

**Quick share (local PC, temporary URL):**
```bash
# Terminal 1
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2
ngrok http 8000
```

Update the `API` constant in `nambot.html` to the ngrok URL, then share the HTML file with anyone.

**Permanent hosting (free):**
- Backend → [Railway](https://railway.app) — add env vars in dashboard, add a `Procfile`:
  ```
  web: uvicorn main:app --host 0.0.0.0 --port $PORT
  ```
- Frontend → [Netlify](https://netlify.com) — drag and drop `nambot.html`
- Custom domain → buy at [Porkbun](https://porkbun.com) (~$8/yr), connect in Netlify DNS settings

---

## Get your free API keys

- **GROQ_API_KEY** → [console.groq.com](https://console.groq.com) — sign up, no credit card
- **GITHUB_TOKEN** → [github.com/settings/tokens/new](https://github.com/settings/tokens/new) — classic token, no scopes needed

## Deployment

Recommended: Railway.app or Render.com
- Set all environment variables in the dashboard
- For production use PostgreSQL (not SQLite)
- Set SECRET_KEY to a long random string
