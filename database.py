import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')

# Create database engine with SSL configuration
try:
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "sslmode": "require"
        },
        pool_pre_ping=True,  # Enable connection health checks
        pool_recycle=3600    # Recycle connections every hour
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise

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
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_check_date = Column(DateTime, default=datetime.utcnow)
    achievements = Column(JSON, default=dict) # Added achievements column

    grammar_checks = relationship("GrammarCheck", back_populates="user_progress")
    assessments = relationship("LanguageAssessment", backref="user_progress", cascade="all, delete-orphan")

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

        # Update streak
        self._update_streak()

        # Check and award achievements
        self._check_achievements()

        # Update accuracy
        self.average_accuracy = (self.total_correct / self.total_checks) if self.total_checks > 0 else 0.0
        self.last_activity = datetime.utcnow()

        db.commit()

    def _update_streak(self):
        """Update the user's learning streak"""
        today = datetime.utcnow().date()
        last_check = self.last_check_date.date() if self.last_check_date else None

        if not last_check:
            # First check ever
            self.current_streak = 1
            self.longest_streak = 1
        elif last_check == today:
            # Already checked today, streak remains the same
            pass
        elif (today - last_check).days == 1:
            # Consecutive day, increase streak
            self.current_streak += 1
            self.longest_streak = max(self.longest_streak, self.current_streak)
        else:
            # Streak broken
            self.current_streak = 1

        self.last_check_date = datetime.utcnow()

    def _check_achievements(self):
        """Check and award achievements based on user progress"""
        if not self.achievements:
            self.achievements = {
                'streak': [],
                'accuracy': [],
                'mastery': [],
                'practice': []
            }

        # Streak achievements
        streak_milestones = [3, 7, 14, 30, 60, 90]
        for days in streak_milestones:
            achievement_id = f"streak_{days}"
            if self.current_streak >= days and achievement_id not in self.achievements['streak']:
                self.achievements['streak'].append(achievement_id)

        # Accuracy achievements
        accuracy_milestones = [0.6, 0.7, 0.8, 0.9, 0.95]
        for accuracy in accuracy_milestones:
            achievement_id = f"accuracy_{int(accuracy * 100)}"
            if self.average_accuracy >= accuracy and achievement_id not in self.achievements['accuracy']:
                self.achievements['accuracy'].append(achievement_id)

        # Practice count achievements
        practice_milestones = [10, 50, 100, 500, 1000]
        for count in practice_milestones:
            achievement_id = f"practice_{count}"
            if self.total_checks >= count and achievement_id not in self.achievements['practice']:
                self.achievements['practice'].append(achievement_id)

        # Mastery achievements (for particles and verbs)
        mastery_categories = [
            (self.particle_mastery, 'particle'),
            (self.verb_mastery, 'verb'),
            (self.pattern_mastery, 'pattern')
        ]

        for mastery_dict, category in mastery_categories:
            if mastery_dict:
                total_mastery = sum(
                    stats['correct'] / stats['count']
                    for stats in mastery_dict.values()
                    if stats['count'] > 0
                ) / len(mastery_dict)

                mastery_milestones = [0.5, 0.7, 0.9]
                for mastery in mastery_milestones:
                    achievement_id = f"{category}_mastery_{int(mastery * 100)}"
                    if total_mastery >= mastery and achievement_id not in self.achievements['mastery']:
                        self.achievements['mastery'].append(achievement_id)

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

class LanguageAssessment(Base):
    __tablename__ = "language_assessments"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey('user_progress.session_id'), nullable=False)
    assessment_date = Column(DateTime, default=datetime.utcnow)
    self_rated_level = Column(String(20))  # beginner, intermediate, advanced
    grammar_comfort = Column(JSON)  # Comfort levels with different grammar patterns
    test_results = Column(JSON)  # Results from the quick assessment test
    recommended_level = Column(String(20))
    weak_areas = Column(JSON)  # Areas that need more practice
    strong_areas = Column(JSON)  # Areas of strength


    @classmethod
    def create(cls, db, session_id, assessment_data):
        assessment = cls(
            session_id=session_id,
            self_rated_level=assessment_data['self_rated_level'],
            grammar_comfort=assessment_data['grammar_comfort'],
            test_results=assessment_data['test_results'],
            recommended_level=assessment_data['recommended_level'],
            weak_areas=assessment_data['weak_areas'],
            strong_areas=assessment_data['strong_areas']
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment

    @classmethod
    def get_latest_assessment(cls, db, session_id):
        return db.query(cls).filter(
            cls.session_id == session_id
        ).order_by(cls.assessment_date.desc()).first()

class IdiomTranslation(Base):
    __tablename__ = "idiom_translations"

    id = Column(Integer, primary_key=True, index=True)
    japanese_idiom = Column(String(255), nullable=False)
    literal_meaning = Column(Text)
    english_equivalent = Column(Text)
    explanation = Column(Text)
    usage_example = Column(Text)
    tags = Column(JSON, default=list)  # For categorizing idioms
    created_at = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def create(cls, db, idiom_data):
        idiom = cls(**idiom_data)
        db.add(idiom)
        db.commit()
        db.refresh(idiom)
        return idiom

    @classmethod
    def get_all(cls, db):
        return db.query(cls).all()

    @classmethod
    def search(cls, db, query):
        return db.query(cls).filter(
            cls.japanese_idiom.ilike(f"%{query}%") |
            cls.english_equivalent.ilike(f"%{query}%") |
            cls.literal_meaning.ilike(f"%{query}%")
        ).all()

# Create all tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()