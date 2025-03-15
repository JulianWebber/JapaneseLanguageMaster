import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')

# Create database engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class GrammarCheck(Base):
    __tablename__ = "grammar_checks"

    id = Column(Integer, primary_key=True, index=True)
    input_text = Column(Text, nullable=False)
    grammar_issues = Column(JSON)
    particle_usage = Column(JSON)
    verb_conjugations = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def create(cls, db, input_text, analysis_results):
        grammar_check = cls(
            input_text=input_text,
            grammar_issues=analysis_results.get('grammar_issues', []),
            particle_usage=analysis_results.get('particle_usage', []),
            verb_conjugations=analysis_results.get('verb_conjugations', [])
        )
        db.add(grammar_check)
        db.commit()
        db.refresh(grammar_check)
        return grammar_check

    @classmethod
    def get_recent_checks(cls, db, limit=10):
        return db.query(cls).order_by(cls.created_at.desc()).limit(limit).all()

# Create all tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
