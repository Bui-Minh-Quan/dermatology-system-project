from contextlib import asynccontextmanager
import torch
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware # <-- 1. Import CORS
from transformers import AutoTokenizer

from services.diagnosis.router import router as diagnosis_router
from services.diagnosis.state import diagnosis_state
from services.diagnosis.models import Gatekeeper, DiseaseClassifier

# <-- 2. Import thêm router của Chatbot
from services.rag.router import router as chat_router


# =========================================================
# LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("🤖 Loading AI diagnosis models...")

    diagnosis_state.device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    # =====================================================
    # TOKENIZER
    # =====================================================

    diagnosis_state.tokenizer = (
        AutoTokenizer.from_pretrained(
            "vinai/phobert-base-v2"
        )
    )

    # =====================================================
    # MODELS
    # =====================================================

    diagnosis_state.gatekeeper = (
        Gatekeeper()
        .to(diagnosis_state.device)
    )

    diagnosis_state.disease_classifier = (
        DiseaseClassifier()
        .to(diagnosis_state.device)
    )

    # =====================================================
    # LOAD WEIGHTS
    # =====================================================

    diagnosis_state.gatekeeper.load_state_dict(
        torch.load(
            "weights/gatekeeper.pth",
            map_location=diagnosis_state.device,
            weights_only=True
        )
    )

    diagnosis_state.disease_classifier.load_state_dict(
        torch.load(
            "weights/disease_classifier.pt",
            map_location=diagnosis_state.device,
            weights_only=True
        )
    )

    # =====================================================
    # EVAL MODE
    # =====================================================

    diagnosis_state.gatekeeper.eval()

    diagnosis_state.disease_classifier.eval()

    print("✅ AI diagnosis service ready.")

    yield

    # =====================================================
    # SHUTDOWN
    # =====================================================

    print("🛑 Releasing GPU memory...")

    diagnosis_state.gatekeeper = None

    diagnosis_state.disease_classifier = None

    diagnosis_state.tokenizer = None

    if torch.cuda.is_available():

        torch.cuda.empty_cache()


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="AI Services",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Trong môi trường dev để "*" cho tiện
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

app.include_router(diagnosis_router)
app.include_router(chat_router)


@app.get("/")
def health_check():

    return {
        "status": "online"
    }