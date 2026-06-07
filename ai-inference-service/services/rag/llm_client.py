import os
import requests
import json  # Bắt buộc phải có để parse luồng stream

class LLMClient:
    def __init__(self):
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("LLM_MODEL", "qwen2.5:1.5b")

    def generate(self, prompt: str, temperature: float = 0.1) -> str:
        """Hàm sinh text thông thường (Không stream)"""
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature
                    }
                }
            )
            response.raise_for_status()
            return response.json().get("response", "Error: No response generated.")
        except Exception as e:
            return f"LLM Connection Error: {e}"

    def generate_stream(self, prompt: str, temperature: float = 0.1):
        """Hàm stream từng từ một (Yield) dùng cho API thời gian thực"""
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,  # Bật stream của Ollama
                    "options": {"temperature": temperature}
                },
                stream=True  # Ép thư viện requests đọc theo luồng
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "response" in chunk:
                        yield chunk["response"] # Đẩy từng chữ ra ngoài
        except Exception as e:
            yield f"\n[LLM Connection Error: {e}]"

    def rewrite_query(self, chat_history: str, query: str) -> str:
        """Nhờ LLM làm rõ đại từ nhân xưng dựa vào lịch sử chat"""
        if not chat_history:
            return query

        prompt = f"""Given the conversation history, rewrite the user's follow-up question to be a standalone query that includes the specific medical names. Do NOT answer the question, just rewrite it.

History:
{chat_history}

Follow-up Question: {query}

Standalone Query (just the question):"""
        
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0} # Bắt buộc là 0 để không sáng tạo
                }
            )
            response.raise_for_status()
            return response.json().get("response", query).strip()
        except Exception as e:
            print(f"[LLM Error - Rewriting]: {e}")
            return query