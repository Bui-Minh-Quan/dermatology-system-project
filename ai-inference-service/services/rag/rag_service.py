from services.rag.context_builder import ContextBuilder
from services.rag.prompts import build_hybrid_prompt
from services.rag.llm_client import LLMClient
from services.rag.memory_manager import MemoryManager

class HybridRAGService:
    def __init__(self):
        self.context_builder = ContextBuilder()
        self.llm_client = LLMClient()
        self.memory = MemoryManager()

    def generate_answer(self, query: str, session_id: str = "default_session") -> str:
        """Generate a complete text response and store it in memory."""
        try:
            self.memory.save_message(session_id, role="user", content=query)
            chat_history = self.memory.get_sliding_window_history(session_id, window_size=6)
            
            vector_ctx, graph_ctx = self.context_builder.build_context(query)
            final_prompt = build_hybrid_prompt(query, chat_history, vector_ctx, graph_ctx)
            
            answer = self.llm_client.generate(final_prompt, temperature=0.1)
            
            self.memory.save_message(session_id, role="assistant", content=answer)
            return answer

        except Exception as e:
            return f"Service Error: {str(e)}"
        
    def generate_answer_stream(self, query: str, session_id: str = "default_session"):
        """Stream the response chunk by chunk and store the full result in memory."""
        try:
            self.memory.save_message(session_id, role="user", content=query)
            chat_history = self.memory.get_sliding_window_history(session_id, window_size=4)
            
            # Rewrite query to be standalone if chat history exists
            standalone_query = query
            if chat_history:
                standalone_query = self.llm_client.rewrite_query(chat_history, query)
            
            # Retrieve context using the rewritten query
            vector_ctx, graph_ctx = self.context_builder.build_context(standalone_query)
            final_prompt = build_hybrid_prompt(query, chat_history, vector_ctx, graph_ctx)
            
            full_response = ""
            for text_chunk in self.llm_client.generate_stream(final_prompt, temperature=0.1):
                full_response += text_chunk
                yield text_chunk 
            
            if full_response.strip():
                self.memory.save_message(session_id, role="assistant", content=full_response)

        except Exception as e:
            yield f"Error: {str(e)}"