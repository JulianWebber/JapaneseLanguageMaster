import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey
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

class CustomGrammarRule(Base):
    __tablename__ = "custom_grammar_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    pattern = Column(String(255), nullable=False)
    check_pattern = Column(String(255), nullable=False)
    correct_pattern = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    example = Column(Text, nullable=False)
    error_description = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    context_rules = Column(JSON, default=list)

    @classmethod
    def create(cls, db, rule_data):
        custom_rule = cls(**rule_data)
        db.add(custom_rule)
        db.commit()
        db.refresh(custom_rule)
        return custom_rule

    @classmethod
    def get_active_rules(cls, db):
        return db.query(cls).filter(cls.is_active == True).all()

    @classmethod
    def update_rule(cls, db, rule_id, rule_data):
        db.query(cls).filter(cls.id == rule_id).update(rule_data)
        db.commit()
        return db.query(cls).filter(cls.id == rule_id).first()

    @classmethod
    def delete_rule(cls, db, rule_id):
        rule = db.query(cls).filter(cls.id == rule_id).first()
        if rule:
            rule.is_active = False
            db.commit()
        return rule

# Create all tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()