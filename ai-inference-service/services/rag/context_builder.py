from services.rag.embeddings import EmbeddingClient
from services.rag.vector_retriever import VectorRetriever
from services.rag.graph_retriever import GraphRetriever

class ContextBuilder:
    def __init__(self):
        self.embedding_client = EmbeddingClient()
        self.vector_retriever = VectorRetriever()
        self.graph_retriever = GraphRetriever()

    def _format_vector_results(self, results: list) -> str:
        if not results:
            return ""
        
        formatted_chunks = []
        for r in results:
            # Đã xóa Relevance Score cho sạch sẽ
            header = f"[{r['entity_type']} - {r['entity_name']}] (Section: {r['section'].capitalize()})"
            formatted_chunks.append(f"{header}\n{r['content']}")
            
        return "\n\n".join(formatted_chunks)

    def _format_graph_results(self, results: list) -> str:
        if not results:
            return ""
            
        formatted_relations = []
        for r in results:
            # Đã xóa Match Score
            rel_str = f"{r['source']} -[{r['relationship']}]-> {r['target']}"
            formatted_relations.append(rel_str)
            
        return "\n".join(list(set(formatted_relations)))

    def build_context(self, query: str):
        print("[ContextBuilder] Đang tổng hợp ngữ cảnh...")
        
        # Tăng top_k lên 6 để mở rộng lưới, tránh bị sót phần Thuốc (Medications)
        query_emb = self.embedding_client.embed(query)
        vector_raw = self.vector_retriever.retrieve(query_emb, top_k=6)
        vector_context = self._format_vector_results(vector_raw)

        # Lấy Graph Context
        graph_raw = self.graph_retriever.retrieve(query, limit=15)
        graph_context = self._format_graph_results(graph_raw)

        return vector_context, graph_context