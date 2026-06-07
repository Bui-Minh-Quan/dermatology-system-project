from services.rag.embeddings import EmbeddingClient
from services.rag.vector_retriever import VectorRetriever
from services.rag.graph_retriever import GraphRetriever

class ContextBuilder:
    def __init__(self):
        self.embedding_client = EmbeddingClient()
        self.vector_retriever = VectorRetriever()
        self.graph_retriever = GraphRetriever()

    def _format_vector_results(self, results: list) -> str:
        """Format vector database results into a clean text block."""
        if not results:
            return ""
        
        formatted_chunks = []
        for r in results:
            header = f"[{r['entity_type']} - {r['entity_name']}] (Section: {r['section'].capitalize()})"
            formatted_chunks.append(f"{header}\n{r['content']}")
            
        return "\n\n".join(formatted_chunks)

    def _format_graph_results(self, results: list) -> str:
        """Format graph relationships into a clean list of triples."""
        if not results:
            return ""
            
        formatted_relations = []
        for r in results:
            rel_str = f"{r['source']} -[{r['relationship']}]-> {r['target']}"
            formatted_relations.append(rel_str)
            
        return "\n".join(list(set(formatted_relations)))

    def build_context(self, query: str):
        """Retrieve and synthesize vector and graph context for the LLM."""
        # Retrieve vector context
        query_emb = self.embedding_client.embed(query)
        vector_raw = self.vector_retriever.retrieve(query_emb, top_k=6)
        vector_context = self._format_vector_results(vector_raw)

        # Retrieve graph context
        graph_raw = self.graph_retriever.retrieve(query, limit=15)
        graph_context = self._format_graph_results(graph_raw)

        return vector_context, graph_context