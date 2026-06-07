import os
from dotenv import load_dotenv
from sqlalchemy import text

# Import engine và Base từ config của bạn
from config.database import engine, Base

# RẤT QUAN TRỌNG: Phải import KnowledgeChunk thì SQLAlchemy mới biết mà tạo bảng!
from models.knowledge_chunk import KnowledgeChunk
from models.chat_history import ChatMessage

# Load .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

def main():
    print("Đang khởi tạo database...")
    
    # 1. Bật extension vector
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        print("Đã kiểm tra và bật extension pgvector.")

    # 2. Tạo tất cả các bảng đã được import
    Base.metadata.create_all(bind=engine)
    print("Tables created. (Đã tạo bảng thành công!)")

if __name__ == "__main__":
    main()