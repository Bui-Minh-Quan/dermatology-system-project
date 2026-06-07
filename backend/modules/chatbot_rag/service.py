import httpx
import os
from dotenv import load_dotenv
from models.users import User

load_dotenv()

AI_SERVICE_URL = os.getenv("AI_INFERENCE_URL", "http://localhost:8001") + "/api/chat/stream"

class ChatbotProxyService:
    
    @staticmethod
    async def stream_to_ai_service(query: str, user: User):
        """
        Open an asynchronous connection to the AI inference service 
        and stream the response chunks back to the client.
        """
        session_id = f"user_{user.user_id}"
        payload = {
            "session_id": session_id,
            "query": query
        }

        async with httpx.AsyncClient() as client:
            try:
                async with client.stream("POST", AI_SERVICE_URL, json=payload, timeout=60.0) as response:
                    if response.status_code != 200:
                        yield f"[AI System Error: HTTP {response.status_code}]".encode("utf-8")
                        return

                    async for chunk in response.aiter_bytes():
                        yield chunk
                        
            except httpx.ConnectError:
                yield "\n[Error: Unable to connect to the AI Inference Service (Port 8001).]".encode("utf-8")
            except httpx.ReadTimeout:
                yield "\n[Error: AI Service response timed out.]".encode("utf-8")
            except Exception as e:
                yield f"\n[Unexpected system error: {str(e)}]".encode("utf-8")