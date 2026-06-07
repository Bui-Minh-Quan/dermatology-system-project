import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from transformers import AutoTokenizer

from services.diagnosis.router import router as diagnosis_router
from services.diagnosis.state import diagnosis_state
from services.diagnosis.models import Gatekeeper, DiseaseClassifier
from services.rag.router import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize device
    diagnosis_state.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Initialize tokenizer and models
    diagnosis_state.tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base-v2")
    diagnosis_state.gatekeeper = Gatekeeper().to(diagnosis_state.device)
    diagnosis_state.disease_classifier = DiseaseClassifier().to(diagnosis_state.device)

    # Load model weights
    diagnosis_state.gatekeeper.load_state_dict(
        torch.load("weights/gatekeeper.pth", map_location=diagnosis_state.device, weights_only=True)
    )
    diagnosis_state.disease_classifier.load_state_dict(
        torch.load("weights/disease_classifier.pt", map_location=diagnosis_state.device, weights_only=True)
    )

    # Set to evaluation mode
    diagnosis_state.gatekeeper.eval()
    diagnosis_state.disease_classifier.eval()

    yield

    # Clean up resources
    diagnosis_state.gatekeeper = None
    diagnosis_state.disease_classifier = None
    diagnosis_state.tokenizer = None
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

app = FastAPI(title="AI Services", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Register routers
app.include_router(diagnosis_router)
app.include_router(chat_router)

@app.get("/")
def health_check():
    return {"status": "online"}