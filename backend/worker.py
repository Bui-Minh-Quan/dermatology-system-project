import torch
from redis import Redis
from rq import SimpleWorker
from transformers import AutoTokenizer

from config.ml_state import ml_state

from modules.ai_diagnosis.ml_engine import (
    build_skin_detector,
    ProductionTrimodalModel
)

print("🤖 Loading AI models into worker...")

ml_state.device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

ml_state.tokenizer = AutoTokenizer.from_pretrained(
    "vinai/phobert-base-v2"
)

ml_state.gatekeeper = build_skin_detector().to(
    ml_state.device
)

ml_state.trimodal_classifier = (
    ProductionTrimodalModel(num_classes=9).to(
        ml_state.device
    )
)

ml_state.gatekeeper.load_state_dict(
    torch.load(
        "ml_weights/skin_detector.pth",
        map_location=ml_state.device,
        weights_only=True
    )
)

ml_state.trimodal_classifier.load_state_dict(
    torch.load(
        "ml_weights/production_trimodal_model.pt",
        map_location=ml_state.device,
        weights_only=True
    )
)

ml_state.gatekeeper.eval()

ml_state.trimodal_classifier.eval()

print("✅ Worker models loaded.")

redis_conn = Redis(
    host="localhost",
    port=6379
)


worker = SimpleWorker(
    ["diagnosis"],
    connection=redis_conn
)
print("🚀 Worker listening on diagnosis queue...")

worker.work()