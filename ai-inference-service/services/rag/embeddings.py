import os
import requests

class EmbeddingClient:
    def __init__(self):
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

    def embed(self, text: str) -> list:
        try:
            response = requests.post(
                f"{self.url}/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []