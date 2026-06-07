from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from config.database import get_db
from modules.auth.security import get_current_user
from models.users import User
from models.chat_messages import ChatMessage
from .service import ChatbotProxyService

router = APIRouter(prefix="/chatbot", tags=["AI Chatbot Proxy"])

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    stream_generator = ChatbotProxyService.stream_to_ai_service(
        query=request.message, 
        user=current_user
    )
    return StreamingResponse(stream_generator, media_type="text/event-stream")

@router.get("/history")
def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_id = f"user_{current_user.user_id}"
    
    # Retrieve messages sorted by creation time for UI rendering
    messages = db.query(ChatMessage)\
                 .filter(ChatMessage.session_id == session_id)\
                 .order_by(ChatMessage.created_at.asc())\
                 .limit(limit)\
                 .all()
                 
    return {
        "session_id": session_id,
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at
            } for msg in messages
        ]
    }

@router.delete("/history")
def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_id = f"user_{current_user.user_id}"
    
    try:
        # Clear all history for the specific user session
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        db.commit()
        return {"message": "Chat history cleared successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))