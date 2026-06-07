from sqlalchemy import text
from config.database import engine

class VectorRetriever:
    def __init__(self):
        self.engine = engine

    def retrieve(self, query_embedding: list, top_k: int = 5, distance_threshold: float = 0.6) -> list:
        """
        Tìm kiếm Vector sử dụng Cosine Distance (<=>).
        distance_threshold: Lọc bỏ các chunk không liên quan (ngưỡng 0.6 thường là tốt nhất cho y khoa).
        """
        if not query_embedding:
            return []

        results = []
        try:
            with self.engine.connect() as conn:
                # pgvector tính distance: 0 là giống hệt nhau, 1 là vuông góc (khác biệt)
                # Dùng thuộc tính section_type mà bạn vừa thiết kế
                stmt = text("""
                    SELECT entity_type, entity_name, section_type, content, (embedding <=> :q_emb) as distance
                    FROM knowledge_chunks 
                    WHERE (embedding <=> :q_emb) < :threshold
                    ORDER BY distance ASC
                    LIMIT :top_k
                """)
                
                rows = conn.execute(stmt, {
                    "q_emb": str(query_embedding), 
                    "top_k": top_k,
                    "threshold": distance_threshold
                }).fetchall()
                
                for row in rows:
                    results.append({
                        "entity_type": row[0],
                        "entity_name": row[1],
                        "section": row[2],
                        "content": row[3],
                        # Chuyển distance thành similarity score (1 - distance) cho dễ hiểu
                        "score": round(1.0 - row[4], 4) 
                    })
        except Exception as e:
            print(f"❌ Vector Retrieval Error: {e}")
        
        return results