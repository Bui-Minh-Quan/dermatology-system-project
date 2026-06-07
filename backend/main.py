import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI 
from fastapi.staticfiles import StaticFiles

from config.database import postgres_engine, Base 

from models import users 
from modules.auth import router as auth_router 
from modules.auth import admin_router
from modules.profiles import router as profiles_router
from modules.ai_diagnosis import router as diagnosis_router
from modules.tracking import router as tracking_router
from modules.chatbot_rag import router as chatbot_router
from modules.recommendation import router as recommendation_router
from modules.appointments import router as appointments_router


# Create tables
Base.metadata.create_all(bind=postgres_engine)

# Inject the lifespan into the FastAPI application instance
app = FastAPI(title="Dermatology AI System")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Plug in the Auth endpoints
app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(profiles_router.router)
app.include_router(diagnosis_router.router)
app.include_router(tracking_router.router)
app.include_router(chatbot_router.router)
app.include_router(recommendation_router.router)
app.include_router(appointments_router.router)

@app.get("/")
def read_root():
    return {"message": "System is Online"}