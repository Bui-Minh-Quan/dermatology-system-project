import os
import requests
import json

class LLMClient:
    def __init__(self):
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("LLM_MODEL", "qwen2.5:1.5b")

    def generate(self, prompt: str, temperature: float = 0.1) -> str:
        """Generate a text response without streaming."""
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature}
                }
            )
            response.raise_for_status()
            return response.json().get("response", "Error: No response generated.")
        except Exception as e:
            return f"LLM Connection Error: {e}"

    def generate_stream(self, prompt: str, temperature: float = 0.1):
        """Stream the LLM response chunk by chunk."""
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {"temperature": temperature}
                },
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "response" in chunk:
                        yield chunk["response"]
        except Exception as e:
            yield f"\n[LLM Connection Error: {e}]"

    def rewrite_query(self, chat_history: str, query: str) -> str:
        """Rewrite a follow-up question to be standalone based on chat history."""
        if not chat_history:
            return query

        prompt = f"""Given the conversation history, rewrite the user's follow-up question 
        to be a standalone query that includes the specific medical names. 
        Do NOT answer the question, just rewrite it.

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
                    "options": {"temperature": 0.0}
                }
            )
            response.raise_for_status()
            return response.json().get("response", query).strip()
        except Exception:
            return query