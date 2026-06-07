import os
from dotenv import load_dotenv
from sqlalchemy import text

# Import engine and Base from your database configuration
from config.database import postgres_engine as engine, Base

# Import models to ensure they are registered for table creation
from models.knowledge_chunk import KnowledgeChunk
from models.chat_history import ChatMessage

# Load environment variables
load_dotenv()

def main():
    print("Initializing database...")
    
    # 1. Enable pgvector extension
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        print("Verified and enabled pgvector extension.")

    # 2. Create tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    main()