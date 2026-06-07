from sqlalchemy import select, desc
from config.database import SessionLocal
from models.chat_history import ChatMessage

class MemoryManager:
    def save_message(self, session_id: str, role: str, content: str):
        """Lưu một tin nhắn mới vào database"""
        with SessionLocal() as db:
            msg = ChatMessage(
                session_id=session_id,
                role=role,
                content=content
            )
            db.add(msg)
            db.commit()

    def get_sliding_window_history(self, session_id: str, window_size: int = 6) -> str:
        """
        Lấy N tin nhắn gần nhất (Sliding Window).
        window_size = 6 nghĩa là lấy 3 câu hỏi của User + 3 câu trả lời của AI.
        """
        with SessionLocal() as db:
            # Lấy N tin nhắn mới nhất, sắp xếp giảm dần theo thời gian (mới nhất lên đầu)
            stmt = select(ChatMessage)\
                .where(ChatMessage.session_id == session_id)\
                .order_by(desc(ChatMessage.created_at))\
                .limit(window_size)
            
            recent_messages = db.execute(stmt).scalars().all()

        if not recent_messages:
            return ""

        # Vì đang sắp xếp mới nhất lên đầu, ta phải đảo ngược lại (reverse) 
        # để tin nhắn cũ hiển thị trước, mới hiển thị sau cho đúng ngữ cảnh đọc
        recent_messages = reversed(recent_messages)
        
        history_str = ""
        for msg in recent_messages:
            role_name = "Patient" if msg.role == "user" else "Assistant"
            history_str += f"{role_name}: {msg.content}\n\n"
            
        return history_str.strip()