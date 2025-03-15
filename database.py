import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

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
    user_progress_id = Column(Integer, ForeignKey('user_progress.id'), nullable=True)

    user_progress = relationship("UserProgress", back_populates="grammar_checks")

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

class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False)
    total_checks = Column(Integer, default=0)
    total_correct = Column(Integer, default=0)
    particle_mastery = Column(JSON, default=dict)
    verb_mastery = Column(JSON, default=dict)
    pattern_mastery = Column(JSON, default=dict)
    average_accuracy = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

    grammar_checks = relationship("GrammarCheck", back_populates="user_progress")

    @classmethod
    def get_or_create(cls, db, session_id):
        progress = db.query(cls).filter(cls.session_id == session_id).first()
        if not progress:
            progress = cls(session_id=session_id)
            db.add(progress)
            db.commit()
            db.refresh(progress)
        return progress

    def update_progress(self, db, analysis_results):
        # Update check counts
        self.total_checks += 1
        correct_count = (
            len(analysis_results.get('particle_usage', [])) +
            len(analysis_results.get('verb_conjugations', [])) -
            len(analysis_results.get('grammar_issues', []))
        )
        self.total_correct += max(0, correct_count)

        # Update mastery levels
        self._update_particle_mastery(analysis_results.get('particle_usage', []))
        self._update_verb_mastery(analysis_results.get('verb_conjugations', []))
        self._update_pattern_mastery(analysis_results.get('advanced_patterns', []))

        # Update accuracy
        self.average_accuracy = (self.total_correct / self.total_checks) if self.total_checks > 0 else 0.0
        self.last_activity = datetime.utcnow()

        db.commit()

    def _update_particle_mastery(self, particles):
        if not self.particle_mastery:
            self.particle_mastery = {}

        for particle in particles:
            particle_name = particle['particle']
            if particle_name not in self.particle_mastery:
                self.particle_mastery[particle_name] = {'count': 0, 'correct': 0}
            self.particle_mastery[particle_name]['count'] += 1
            self.particle_mastery[particle_name]['correct'] += 1

    def _update_verb_mastery(self, verbs):
        if not self.verb_mastery:
            self.verb_mastery = {}

        for verb in verbs:
            conjugation = verb['conjugation']
            if conjugation not in self.verb_mastery:
                self.verb_mastery[conjugation] = {'count': 0, 'correct': 0}
            self.verb_mastery[conjugation]['count'] += 1
            self.verb_mastery[conjugation]['correct'] += 1

    def _update_pattern_mastery(self, patterns):
        if not self.pattern_mastery:
            self.pattern_mastery = {}

        for pattern in patterns:
            pattern_name = pattern['pattern']
            if pattern_name not in self.pattern_mastery:
                self.pattern_mastery[pattern_name] = {'count': 0, 'correct': 0}
            self.pattern_mastery[pattern_name]['count'] += 1
            self.pattern_mastery[pattern_name]['correct'] += 1

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