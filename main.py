from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, solve, users
from database import create_tables
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(title="Nambot API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,  prefix="/auth",  tags=["Auth"])
app.include_router(solve.router, prefix="/solve", tags=["Solve"])
app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/")
def root():
    return {"status": "Nambot API running"}

@app.get("/app")
def serve_frontend():
    return FileResponse("nambot.html")

@app.get("/favicon.png")
def favicon():
    return FileResponse("favicon.png")

@app.get("/logo_anhbot.png")
def anhbot_logo():
    return FileResponse("logo_anhbot.png")