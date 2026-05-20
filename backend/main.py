import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI 
from fastapi.staticfiles import StaticFiles
from transformers import AutoTokenizer

from config.database import postgres_engine, Base 
from config.ml_state import ml_state  # Import our new global container!

from models import users 
from modules.auth import router as auth_router 
from modules.auth import admin_router
from modules.profiles import router as profiles_router
from modules.ai_diagnosis import router as diagnosis_router
from modules.tracking import router as tracking_router
from modules.chatbot_rag import router as chatbot_router
from modules.recommendation import router as recommendation_router
from modules.appointments import router as appointments_router

# Import the model blueprints from the ml_engine
from modules.ai_diagnosis.ml_engine import build_skin_detector, ProductionTrimodalModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ==========================================
    # 1. STARTUP LOGIC: Load Models Once
    # ==========================================
    print("🤖 STARTUP: Loading ML Models into GPU...")
    
    # Define device and attach to global state
    ml_state.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    try:
        # Load the tokenizer
        ml_state.tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base-v2")
        
        # Build the architectures and move them to the device
        ml_state.gatekeeper = build_skin_detector().to(ml_state.device)
        ml_state.trimodal_classifier = ProductionTrimodalModel(num_classes=9).to(ml_state.device)
        
        # Load the trained weights
        ml_state.gatekeeper.load_state_dict(
            torch.load("ml_weights/skin_detector.pth", map_location=ml_state.device, weights_only=True)
        )
        ml_state.trimodal_classifier.load_state_dict(
            torch.load("ml_weights/production_trimodal_model.pt", map_location=ml_state.device, weights_only=True)
        )
        
        # Switch to evaluation mode
        ml_state.gatekeeper.eval()
        ml_state.trimodal_classifier.eval()
        
        print("✅ Models successfully locked in GPU RAM! Ready for sub-second inference.")
        
    except Exception as e:
        print(f"❌ Critical error loading model weights: {e}")

    # Yield control back to FastAPI to start accepting HTTP requests
    yield 

    # ==========================================
    # 2. SHUTDOWN LOGIC: Cleanup Memory
    # ==========================================
    print("🛑 SHUTDOWN: Clearing GPU memory...")
    ml_state.gatekeeper = None
    ml_state.trimodal_classifier = None
    ml_state.tokenizer = None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# Create tables
Base.metadata.create_all(bind=postgres_engine)

# Inject the lifespan into the FastAPI application instance
app = FastAPI(title="Dermatology AI System", lifespan=lifespan)

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