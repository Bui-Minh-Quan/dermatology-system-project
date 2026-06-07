from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.rag.rag_service import HybridRAGService

# Router configuration
router = APIRouter(
    prefix="/api/chat",
    tags=["Chatbot RAG"]
)

# Initialize service globally
rag_service = HybridRAGService()

class ChatRequest(BaseModel):
    session_id: str
    query: str

@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Endpoint that accepts a user query and returns a streaming response.
    Frontend receives text chunks in real-time as the LLM generates them.
    """
    return StreamingResponse(
        rag_service.generate_answer_stream(request.query, request.session_id),
        media_type="text/plain"
    )