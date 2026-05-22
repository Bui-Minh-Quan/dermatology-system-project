import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from neo4j import GraphDatabase
from dotenv import load_dotenv

# -----------------------------
# Load environment variables
# -----------------------------
# Resolves to 'backend/' folder
base_dir = Path(__file__).resolve().parent.parent

# Load .env first. 
load_dotenv(base_dir / ".env")
# Only use .env.docker if the first file didn't provide values
load_dotenv(base_dir / ".env.docker")

# -----------------------------
# PostgreSQL Configuration
# -----------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@db:5432/dermatology_system_db"
)

postgres_engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=postgres_engine
)

Base = declarative_base()

# Dependency 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# Neo4j Configuration
# -----------------------------
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "StrongPassword123")

class Neo4jHandler:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    # INDENTED THESE METHODS CORRECTLY
    def close(self):
        self.driver.close()

    def get_session(self):
        return self.driver.session()

# Global instance
neo4j_connector = Neo4jHandler()
