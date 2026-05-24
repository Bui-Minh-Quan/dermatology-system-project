import httpx 

# Load AI_INFERENCE_URL from environment variables
import os
AI_INFERENCE_URL = os.getenv("AI_INFERENCE_URL", "http://localhost:8001")

async def request_ai_diagnosis(
    image_bytes,
    filename,
    symptoms,
    body_vector
):

    async with httpx.AsyncClient(
        timeout=60.0
    ) as client:

        files = {
            "image": (
                filename,
                image_bytes,
                "image/jpeg"
            )
        }

        data = {
            "symptoms": symptoms,
            "body_vector": str(body_vector)
        }

        response = await client.post(
            f"{AI_INFERENCE_URL}/diagnosis/infer",
            files=files,
            data=data
        )

        response.raise_for_status()

        return response.json()