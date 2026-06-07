from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import Service mà chúng ta vừa tối ưu xong
from services.rag.rag_service import HybridRAGService

# Tạo Router với prefix gọn gàng
router = APIRouter(
    prefix="/api/chat",
    tags=["Chatbot RAG"]
)

# Khởi tạo service ở cấp global của router.
# (Vì nó gọi qua HTTP tới Ollama và dùng Connection Pool của DB nên không cần bỏ vào lifespan)
rag_service = HybridRAGService()

# Cấu trúc dữ liệu Frontend gửi lên
class ChatRequest(BaseModel):
    session_id: str
    query: str

@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Endpoint nhận câu hỏi và trả về Streaming Response.
    Frontend sẽ nhận từng chunk text ngay khi LLM sinh ra.
    """
    # Gọi hàm generate_answer_stream có chứa lệnh yield
    return StreamingResponse(
        rag_service.generate_answer_stream(request.query, request.session_id),
        media_type="text/plain" 
    )