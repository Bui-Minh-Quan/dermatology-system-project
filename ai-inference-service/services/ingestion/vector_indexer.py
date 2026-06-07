import os
import sys
from config.database import SessionLocal
from models.knowledge_chunk import KnowledgeChunk
from services.ingestion.rag_data_loader import RAGDataLoader
from services.rag.embeddings import EmbeddingClient

# Ensure the root directory is in the path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

def main():
    print("Reading and chunking data from JSON files...")
    loader = RAGDataLoader(chunk_size=500, chunk_overlap=50)
    chunks = loader.load_all_data()
    
    print(f"Starting embedding and storage of {len(chunks)} chunks into PostgreSQL...")
    db = SessionLocal()
    embedder = EmbeddingClient()
    
    try:
        for i, chunk in enumerate(chunks):
            # Generate vector embedding via Ollama
            vector = embedder.embed(chunk['content'])
            
            # Prepare database record
            db_chunk = KnowledgeChunk(
                chunk_id=chunk.get('chunk_id'),
                source_file=chunk.get('source_file'),
                entity_type=chunk['entity_type'],
                entity_name=chunk['entity_name'],
                section_type=chunk.get('section_type'),
                content=chunk['content'],
                embedding=vector
            )
            db.add(db_chunk)
            
            # Batch commit every 50 chunks for performance
            if (i + 1) % 50 == 0:
                db.commit()
                print(f"Processed {i + 1}/{len(chunks)} chunks...")
                
        # Final commit for remaining records
        db.commit()
        print("Successfully ingested all RAG data into PostgreSQL.")
        
    except Exception as e:
        db.rollback()
        print(f"Error during data ingestion: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()