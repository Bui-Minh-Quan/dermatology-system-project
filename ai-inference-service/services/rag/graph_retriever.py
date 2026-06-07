import os
import re
from neo4j import GraphDatabase

class GraphRetriever:
    def __init__(self):
        uri = "bolt://localhost:7687"
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def _build_lucene_query(self, query: str) -> str:
        clean_query = re.sub(r'[^\w\s]', '', query)
        words = [w for w in clean_query.split() if len(w) > 2]
        if not words:
            return ""
        return " OR ".join([f"{w}~" for w in words])

    def retrieve(self, query: str, limit: int = 15) -> list:
        lucene_query = self._build_lucene_query(query)
        if not lucene_query:
            return []

        results = []
        try:
            with self.driver.session() as session:
                cypher_query = """
                CALL {
                    CALL db.index.fulltext.queryNodes("diseaseFulltext", $lucene_q) YIELD node, score RETURN node, score
                    UNION
                    CALL db.index.fulltext.queryNodes("drugFulltext", $lucene_q) YIELD node, score RETURN node, score
                    UNION
                    CALL db.index.fulltext.queryNodes("symptomFulltext", $lucene_q) YIELD node, score RETURN node, score
                }
                WITH node, score ORDER BY score DESC LIMIT $limit
                
                MATCH (node)-[r]-(neighbor)
                RETURN labels(node)[0] AS src_type, node.name AS src_name, 
                       type(r) AS rel, 
                       labels(neighbor)[0] AS tgt_type, neighbor.name AS tgt_name,
                       score
                // Mẹo Cypher: Ép các relationship về Thuốc và Triệu chứng lên trên cùng
                ORDER BY type(r) = 'TREATED_BY' DESC, type(r) = 'HAS_SYMPTOM' DESC, score DESC
                LIMIT 25
                """
                records = session.run(cypher_query, lucene_q=lucene_query, limit=limit)
                
                for record in records:
                    results.append({
                        "source": f"[{record['src_type']}] {record['src_name']}",
                        "relationship": record['rel'],
                        "target": f"[{record['tgt_type']}] {record['tgt_name']}",
                        "score": round(record['score'], 4)
                    })
        except Exception as e:
            print(f"❌ Graph Retrieval Error: {e}")
            
        return results