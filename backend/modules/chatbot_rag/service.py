import os 
import json
from google import genai 
from config.database import neo4j_connector
from models.users import User 
from dotenv import load_dotenv

load_dotenv()

# Step 1: Initialize the New Client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
# In 2026, we'll use the latest stable flash model
MODEL_ID = "gemini-2.5-flash" 

class GraphRAGService:
    @staticmethod
    def extract_entities(query: str):
        prompt = f"Extract skin-related medical entities from this text as a JSON list of strings: {query}"
        try:
            # ✅ FIX: Pass the string MODEL_ID directly
            response = client.models.generate_content(
                model=MODEL_ID, 
                contents=prompt
            )
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            print(f"Entity extraction error: {e}")
            return []

    @staticmethod
    def get_graph_context(entities: list):
        """Step 3: Graph Query (Neo4j)"""
        try:
            with neo4j_connector.get_session() as session:
                context = ""
                for entity in entities:
                    # Use bracket notation ['name'] to bypass Neo4j's static schema warnings
                    result = session.run(
                        "MATCH (n)-[r]-(m) "
                        "WHERE n['name'] CONTAINS $entity OR m['name'] CONTAINS $entity "
                        "RETURN n['name'] AS n, type(r) AS rel, m['name'] AS m LIMIT 5",
                        entity=entity
                    )
                    for record in result:
                        context += f"{record['n']} -[{record['rel']}]-> {record['m']}\n"
                return context.strip()
        except Exception as e:
            print(f"Graph retrieval error: {e}")
            return ""
    
    @staticmethod
    def generate_response(query: str, user: User, graph_context: str):
        profile = user.patient_profile
        med = getattr(profile, 'medical_info', None)
        
        medical_context = f"""
        User Name: {profile.full_name}
        Gender: {profile.gender}
        Allergies: {med.allergies if med else 'Unknown'}
        Current Meds: {med.current_medications if med else 'None'}
        """

        full_prompt = f"""
        KNOWLEDGE CONTEXT (FROM NEO4J):
        {graph_context if graph_context else "No specific graph data found."}

        USER MEDICAL PROFILE:
        {medical_context}

        QUESTION:
        {query}

        INSTRUCTIONS:
        - Provide medical advice based ONLY on the context if possible.
        - Be professional.
        - ALWAYS include: 'Kết quả này chỉ mang tính tham khảo, vui lòng tham vấn bác sĩ.'
        """

        try:
            # ✅ FIX: Pass the string MODEL_ID directly
            response = client.models.generate_content(
                model=MODEL_ID, 
                contents=full_prompt
            )
            return response.text
        except Exception as e:
            print(f"Response generation error: {e}")
            return "Xin lỗi, hệ thống đang bận. Vui lòng thử lại sau."