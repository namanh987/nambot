from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, solve, users
from database import create_tables

app = FastAPI(title="Nambot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # in production: replace with your frontend domain
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    create_tables()

app.include_router(auth.router,   prefix="/auth",  tags=["Auth"])
app.include_router(solve.router,  prefix="/solve", tags=["Solve"])
app.include_router(users.router,  prefix="/users", tags=["Users"])

@app.get("/")
def root():
    return {"status": "Nambot API running"}
