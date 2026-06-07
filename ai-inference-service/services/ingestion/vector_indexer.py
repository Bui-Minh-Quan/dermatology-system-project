from config.database import SessionLocal
from models.knowledge_chunk import KnowledgeChunk
from services.ingestion.rag_data_loader import RAGDataLoader
from services.rag.embeddings import EmbeddingClient

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

def main():
    print("Đang đọc và chunking dữ liệu từ JSON...")
    loader = RAGDataLoader(chunk_size=500, chunk_overlap=50)
    chunks = loader.load_all_data()
    
    print(f"\nBắt đầu nhúng (embedding) và lưu {len(chunks)} chunks vào PostgreSQL...")
    db = SessionLocal()
    embedder = EmbeddingClient()  
    try:
        for i, chunk in enumerate(chunks):
            print(f"  -> Đang xử lý ({i+1}/{len(chunks)}): [{chunk['entity_type']}] {chunk['entity_name']}...")
            
            # 1. Lấy vector từ Ollama
            vector = embedder.embed(chunk['content'])
            
            # 2. Tạo record
            db_chunk = KnowledgeChunk(
                chunk_id=chunk.get('chunk_id'),          # Get chunk_id
                source_file=chunk.get('source_file'),    # Get source_file
                entity_type=chunk['entity_type'],
                entity_name=chunk['entity_name'],
                section_type=chunk.get('section_type'),  # Get section_type
                content=chunk['content'],
                embedding=vector
            )
            db.add(db_chunk)
            
            # Commit theo batch để tối ưu
            if (i + 1) % 50 == 0:
                db.commit()
                
        # Commit phần còn lại
        db.commit()
        print("\n🎉 HOÀN TẤT! Toàn bộ dữ liệu RAG đã được lưu vào PostgreSQL.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Lỗi trong quá trình lưu dữ liệu: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()