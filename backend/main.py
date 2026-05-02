from fastapi import FastAPI 
from config.database import postgres_engine, Base 
from models import users 
from modules.auth import router as auth_router 

# Create tables
Base.metadata.create_all(bind=postgres_engine)

app = FastAPI(title="Dermatology AI System")

# Plug in the Auth endpoints
app.include_router(auth_router.router)

@app.get("/")
def read_root():
    return {"message": "System is Online"}