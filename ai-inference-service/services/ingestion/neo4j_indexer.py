import os
import json
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Set up paths and environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "services", "ingestion", "data")

load_dotenv()

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

class Neo4jIndexer:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def setup_database(self):
        """Create constraints and full-text search indexes."""
        queries = [
            "CREATE CONSTRAINT disease_name_unique IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT drug_name_unique IF NOT EXISTS FOR (d:Drug) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT symptom_name_unique IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT body_loc_unique IF NOT EXISTS FOR (b:BodyLocation) REQUIRE b.name IS UNIQUE",
            "CREATE CONSTRAINT risk_unique IF NOT EXISTS FOR (r:RiskFactor) REQUIRE r.name IS UNIQUE",
            "CREATE CONSTRAINT trigger_unique IF NOT EXISTS FOR (t:Trigger) REQUIRE t.name IS UNIQUE",
            "CREATE FULLTEXT INDEX diseaseFulltext IF NOT EXISTS FOR (d:Disease) ON EACH [d.name, d.synonyms]",
            "CREATE FULLTEXT INDEX drugFulltext IF NOT EXISTS FOR (d:Drug) ON EACH [d.name, d.synonyms]",
            "CREATE FULLTEXT INDEX symptomFulltext IF NOT EXISTS FOR (s:Symptom) ON EACH [s.name, s.synonyms]"
        ]
        with self.driver.session() as session:
            for q in queries:
                session.run(q)

    def clear_database(self):
        """Delete all nodes and relationships."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def process_diseases(self):
        folder = os.path.join(DATA_DIR, "diseases")
        if not os.path.exists(folder): return

        batch_data = []
        for filename in os.listdir(folder):
            if not filename.endswith('.json'): continue
            with open(os.path.join(folder, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            meta = data.get('metadata', {})
            props = {
                "canonical_name": meta.get('canonical_name', ''),
                "icd10": meta.get('icd10', ''),
                "category": meta.get('category', ''),
                "severity": str(meta.get('severity', '')),
                "chronic": meta.get('chronic', False),
                "contagious": meta.get('contagious', False),
                "synonyms": meta.get('synonyms', [])
            }

            batch_data.append({
                "name": meta.get('disease_name', 'Unknown'),
                "props": props,
                "symptoms": data.get('signs_symptoms', []),
                "drugs": data.get('management', {}).get('medications', []),
                "body_locations": data.get('body_locations', []),
                "risk_factors": data.get('risk_factors', []),
                "triggers": data.get('triggers', []),
                "complications": data.get('complications', []),
                "prevention": data.get('prevention', []),
                "differential": data.get('differential_diagnosis', [])
            })

        with self.driver.session() as session:
            session.run("""
                UNWIND $batch AS row
                MERGE (d:Disease {name: row.name})
                SET d += row.props
            """, batch=batch_data)

            session.run("""
                UNWIND $batch AS row
                MATCH (d:Disease {name: row.name})
                FOREACH (sym IN row.symptoms | MERGE (s:Symptom {name: sym}) MERGE (d)-[:HAS_SYMPTOM]->(s))
                FOREACH (drug IN row.drugs | MERGE (dr:Drug {name: drug}) MERGE (d)-[:TREATED_BY]->(dr))
                FOREACH (loc IN row.body_locations | MERGE (b:BodyLocation {name: loc}) MERGE (d)-[:AFFECTS]->(b))
                FOREACH (risk IN row.risk_factors | MERGE (r:RiskFactor {name: risk}) MERGE (d)-[:HAS_RISK_FACTOR]->(r))
                FOREACH (trig IN row.triggers | MERGE (t:Trigger {name: trig}) MERGE (d)-[:TRIGGERED_BY]->(t))
                FOREACH (comp IN row.complications | MERGE (c:Complication {name: comp}) MERGE (d)-[:COMPLICATES_TO]->(c))
                FOREACH (prev IN row.prevention | MERGE (p:Prevention {name: prev}) MERGE (d)-[:PREVENTED_BY]->(p))
                FOREACH (diff IN row.differential | MERGE (d2:Disease {name: diff}) MERGE (d)-[:DIFFERENTIAL_DIAGNOSIS]->(d2))
            """, batch=batch_data)

    def process_drugs(self):
        folder = os.path.join(DATA_DIR, "drugs")
        if not os.path.exists(folder): return

        batch_data = []
        for filename in os.listdir(folder):
            if not filename.endswith('.json'): continue
            with open(os.path.join(folder, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            meta = data.get('metadata', {})
            props = {
                "generic_name": meta.get('generic_name', ''),
                "drug_class": meta.get('drug_class', ''),
                "prescription_required": meta.get('prescription_required', False),
                "pregnancy_category": meta.get('pregnancy_category', ''),
                "synonyms": meta.get('brand_names', [])
            }

            batch_data.append({
                "name": meta.get('drug_name', 'Unknown'),
                "props": props,
                "indications": data.get('indications', [])
            })

        with self.driver.session() as session:
            session.run("""
                UNWIND $batch AS row
                MERGE (dr:Drug {name: row.name})
                SET dr += row.props
                WITH dr, row
                FOREACH (ind IN row.indications |
                    MERGE (d:Disease {name: ind})
                    MERGE (d)-[:TREATED_BY]->(dr)
                )
            """, batch=batch_data)

    def process_symptoms(self):
        folder = os.path.join(DATA_DIR, "symptoms")
        if not os.path.exists(folder): return

        batch_data = []
        for filename in os.listdir(folder):
            if not filename.endswith('.json'): continue
            with open(os.path.join(folder, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            meta = data.get('metadata', {})
            props = {
                "canonical_name": meta.get('canonical_name', ''),
                "category": meta.get('category', ''),
                "emergency_possible": meta.get('emergency_possible', False),
                "synonyms": meta.get('synonyms', [])
            }

            batch_data.append({"name": meta.get('symptom_name', 'Unknown'), "props": props})

        with self.driver.session() as session:
            session.run("""
                UNWIND $batch AS row
                MERGE (s:Symptom {name: row.name})
                SET s += row.props
            """, batch=batch_data)

def main():
    indexer = Neo4jIndexer()
    try:
        indexer.setup_database()
        indexer.clear_database()
        indexer.process_diseases()
        indexer.process_drugs()
        indexer.process_symptoms()
    finally:
        indexer.close()

if __name__ == "__main__":
    main()