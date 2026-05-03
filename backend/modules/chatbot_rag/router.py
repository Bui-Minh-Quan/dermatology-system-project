from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from config.database import get_db
from modules.auth.security import get_current_user
from .service import GraphRAGService
from pydantic import BaseModel

router = APIRouter(prefix="/chatbot", tags=["Graph RAG Chatbot"])

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Extract Entities
    entities = GraphRAGService.extract_entities(request.message)

    # 2. Get Graph Context
    graph_context = GraphRAGService.get_graph_context(entities)

    # 3. Generate Response
    answer = GraphRAGService.generate_response(request.message, current_user, graph_context)

    return {"answer": answer}