from services.rag.context_builder import ContextBuilder
from services.rag.prompts import build_hybrid_prompt
from services.rag.llm_client import LLMClient
from services.rag.memory_manager import MemoryManager # <-- Import mới

class HybridRAGService:
    def __init__(self):
        self.context_builder = ContextBuilder()
        self.llm_client = LLMClient()
        self.memory = MemoryManager() # <-- Khởi tạo Memory

    def generate_answer(self, query: str, session_id: str = "default_session") -> str:
        try:
            # 1. Lưu câu hỏi của User vào Database ngay lập tức
            self.memory.save_message(session_id, role="user", content=query)

            # 2. Lấy lịch sử trò chuyện (Sliding Window)
            print(f"[RAG] Đang tải bộ nhớ cho session: {session_id}...")
            chat_history = self.memory.get_sliding_window_history(session_id, window_size=6)

            # 3. Lấy Vector và Graph Context
            print("[RAG] Đang truy xuất Vector và Graph Database...")
            vector_ctx, graph_ctx = self.context_builder.build_context(query)

            # 4. Lắp ghép Prompt
            print("[RAG] Đang xây dựng Prompt y khoa...")
            final_prompt = build_hybrid_prompt(query, chat_history, vector_ctx, graph_ctx)
            
            print(f"\n[Final Prompt to LLM]:\n{final_prompt}\n")

            # 5. Gọi LLM
            print("[RAG] Đang gọi LLM (Qwen) suy luận...")
            answer = self.llm_client.generate(final_prompt, temperature=0.1)



            # 6. Lưu câu trả lời của AI vào Database
            self.memory.save_message(session_id, role="assistant", content=answer)

            return answer

        except Exception as e:
            print(f"❌ RAG Service Error: {e}")
            return "We are experiencing technical difficulties. Please try again later."
        
    
    def generate_answer_stream(self, query: str, session_id: str = "default_session"):
        try:
            # 1. Lưu câu hỏi User
            self.memory.save_message(session_id, role="user", content=query)

            # 2. Lấy lịch sử chat
            chat_history = self.memory.get_sliding_window_history(session_id, window_size=4)
            
            # --- BƯỚC MỚI: QUERY REWRITING ---
            standalone_query = query
            if chat_history:
                print("[RAG] Đang làm rõ câu hỏi (Query Rewriting)...")
                standalone_query = self.llm_client.rewrite_query(chat_history, query)
                print(f"[RAG] Câu hỏi mang đi tìm kiếm: {standalone_query}")
            # ----------------------------------

            # 3. Lấy Context BẰNG CÂU HỎI ĐÃ LÀM RÕ (standalone_query)
            print("[RAG] Đang truy xuất Vector và Graph Database...")
            vector_ctx, graph_ctx = self.context_builder.build_context(standalone_query)

            # 4. Lắp ghép Prompt BẰNG CÂU HỎI GỐC (để chat tự nhiên)
            final_prompt = build_hybrid_prompt(query, chat_history, vector_ctx, graph_ctx)

            # 5. Stream chữ từ LLM và gom lại
            full_response = ""
            for text_chunk in self.llm_client.generate_stream(final_prompt, temperature=0.1):
                full_response += text_chunk
                yield text_chunk 

            # 6. Lưu Database
            if full_response.strip():
                self.memory.save_message(session_id, role="assistant", content=full_response)

        except Exception as e:
            yield f"Error: {str(e)}"
# ================= TEST NHANH =================
if __name__ == "__main__":
    service = HybridRAGService()
    test_session = "user_quan_126" # ID giả lập của user
    
    # Lần hỏi 1
    q1 = "I have red, itchy skin on my feet and toes. Could it be Tinea Pedis?"
    print(f"User: {q1}")
    print(f"AI: {service.generate_answer(q1, test_session)}\n")
    
    # Lần hỏi 2 (Chỉ dùng đại từ "it", AI sẽ phải lấy history để hiểu "it" là Tinea Pedis)
    q2 = "What medications should I use to treat it?"
    print(f"User: {q2}")
    print(f"AI: {service.generate_answer(q2, test_session)}\n")