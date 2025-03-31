import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import random
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import Session, relationship
from sqlalchemy.ext.declarative import declarative_base
from database import Base, get_db

class Lesson(Base):
    __tablename__ = "lessons"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    difficulty = Column(String(50), nullable=False)  # Beginner, Elementary, Intermediate, Advanced, Native-like
    tags = Column(JSON, default=list)
    content = Column(JSON)  # Stores the lesson content in JSON format
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = Column(Boolean, default=True)
    
    completions = relationship("LessonCompletion", back_populates="lesson")
    
    @classmethod
    def create(cls, db: Session, lesson_data: Dict) -> "Lesson":
        """Create a new lesson in the database"""
        lesson = cls(
            title=lesson_data.get('title', 'Untitled Lesson'),
            description=lesson_data.get('description', ''),
            difficulty=lesson_data.get('difficulty', 'Intermediate'),
            tags=lesson_data.get('tags', []),
            content=lesson_data.get('content', {}),
            is_published=lesson_data.get('is_published', True)
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        return lesson
    
    @classmethod
    def get_all(cls, db: Session, difficulty: Optional[str] = None) -> List["Lesson"]:
        """Get all lessons, optionally filtered by difficulty"""
        query = db.query(cls).filter(cls.is_published == True)
        
        if difficulty:
            query = query.filter(cls.difficulty == difficulty)
            
        return query.order_by(cls.difficulty, cls.title).all()
    
    @classmethod
    def get_by_id(cls, db: Session, lesson_id: int) -> Optional["Lesson"]:
        """Get a lesson by its ID"""
        return db.query(cls).filter(cls.id == lesson_id).first()
    
    @classmethod
    def search(cls, db: Session, query: str) -> List["Lesson"]:
        """Search for lessons by title or description"""
        return db.query(cls).filter(
            cls.is_published == True,
            (cls.title.ilike(f"%{query}%") | cls.description.ilike(f"%{query}%"))
        ).all()

class LessonCompletion(Base):
    __tablename__ = "lesson_completions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False)
    lesson_id = Column(Integer, ForeignKey('lessons.id'), nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)
    mood_before = Column(String(10))  # Emoji representing mood before lesson
    mood_after = Column(String(10))   # Emoji representing mood after lesson
    difficulty_selected = Column(String(10))  # Emoji representing difficulty level
    notes = Column(Text)  # User notes about the lesson
    satisfaction_rating = Column(Integer)  # Rating 1-5
    
    lesson = relationship("Lesson", back_populates="completions")
    
    @classmethod
    def create(cls, db: Session, completion_data: Dict) -> "LessonCompletion":
        """Record a lesson completion"""
        completion = cls(
            session_id=completion_data.get('session_id'),
            lesson_id=completion_data.get('lesson_id'),
            mood_before=completion_data.get('mood_before'),
            mood_after=completion_data.get('mood_after'),
            difficulty_selected=completion_data.get('difficulty_selected'),
            notes=completion_data.get('notes'),
            satisfaction_rating=completion_data.get('satisfaction_rating')
        )
        db.add(completion)
        db.commit()
        db.refresh(completion)
        return completion
    
    @classmethod
    def get_user_completions(cls, db: Session, session_id: str) -> List["LessonCompletion"]:
        """Get all lessons completed by a user"""
        return db.query(cls).filter(
            cls.session_id == session_id
        ).order_by(cls.completed_at.desc()).all()
    
    @classmethod
    def has_completed_lesson(cls, db: Session, session_id: str, lesson_id: int) -> bool:
        """Check if a user has completed a specific lesson"""
        return db.query(cls).filter(
            cls.session_id == session_id,
            cls.lesson_id == lesson_id
        ).first() is not None

class LessonManager:
    """Class to handle lesson content management and display"""
    
    def __init__(self, db: Session, session_id: Optional[str] = None):
        self.db = db
        self.session_id = session_id if session_id else st.session_state.get('session_id', 'default_user')
    
    def create_lesson(self, lesson_data: Dict) -> Lesson:
        """Create a new lesson in the database"""
        return Lesson.create(self.db, lesson_data)
    
    def get_all_lessons(self, difficulty: Optional[str] = None) -> List[Lesson]:
        """Get all lessons, optionally filtered by difficulty"""
        return Lesson.get_all(self.db, difficulty)
    
    def get_lesson_by_id(self, lesson_id: int) -> Optional[Lesson]:
        """Get a lesson by its ID"""
        return Lesson.get_by_id(self.db, lesson_id)
    
    def record_completion(self, 
                        lesson_id: int, 
                        mood_before: Optional[str] = None,
                        mood_after: Optional[str] = None,
                        difficulty_selected: Optional[str] = None,
                        satisfaction_rating: Optional[int] = None,
                        notes: Optional[str] = None) -> LessonCompletion:
        """Record that a user has completed a lesson"""
        completion_data = {
            'session_id': self.session_id,
            'lesson_id': lesson_id,
            'mood_before': mood_before,
            'mood_after': mood_after,
            'difficulty_selected': difficulty_selected,
            'satisfaction_rating': satisfaction_rating,
            'notes': notes
        }
        
        return LessonCompletion.create(self.db, completion_data)
    
    def has_user_completed_lesson(self, lesson_id: int) -> bool:
        """Check if the current user has completed a specific lesson"""
        return LessonCompletion.has_completed_lesson(self.db, self.session_id, lesson_id)
    
    def get_user_lesson_history(self) -> List[LessonCompletion]:
        """Get all lessons completed by the current user"""
        return LessonCompletion.get_user_completions(self.db, self.session_id)
    
    def display_lesson_catalog(self, 
                             difficulty_filter: Optional[str] = None,
                             category_filter: Optional[str] = None) -> None:
        """Display a catalog of available lessons with filters"""
        # Get lessons with filters
        lessons = self.get_all_lessons(difficulty=difficulty_filter)
        
        # Filter by category if specified
        if category_filter and lessons:
            lessons = [
                lesson for lesson in lessons 
                if any(tag.lower() == category_filter.lower() for tag in lesson.tags)
            ]
        
        if not lessons:
            st.warning("No lessons found matching your criteria.")
            return
        
        # Group lessons by difficulty
        lessons_by_difficulty = {}
        for lesson in lessons:
            if lesson.difficulty not in lessons_by_difficulty:
                lessons_by_difficulty[lesson.difficulty] = []
            lessons_by_difficulty[lesson.difficulty].append(lesson)
        
        # Display lessons grouped by difficulty
        for difficulty, difficulty_lessons in lessons_by_difficulty.items():
            with st.expander(f"{difficulty} ({len(difficulty_lessons)} lessons)", expanded=True):
                for i, lesson in enumerate(difficulty_lessons):
                    # Create card-like display for each lesson
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            # Display lesson title and tags
                            st.subheader(lesson.title)
                            st.write(lesson.description)
                            
                            # Display tags as pills
                            if lesson.tags:
                                tag_html = " ".join([f'<span style="background-color: #e0e0e0; padding: 3px 8px; border-radius: 10px; margin-right: 5px; font-size: 0.8em;">{tag}</span>' for tag in lesson.tags])
                                st.markdown(tag_html, unsafe_allow_html=True)
                        
                        with col2:
                            # Check if user has completed this lesson
                            is_completed = self.has_user_completed_lesson(lesson.id)
                            
                            if is_completed:
                                st.success("✓ Completed")
                            
                            # Button to view the lesson
                            if st.button("Start Lesson", key=f"lesson_{lesson.id}"):
                                st.session_state.selected_lesson_id = lesson.id
                                st.rerun()
                        
                        # Add a divider between lessons
                        if i < len(difficulty_lessons) - 1:
                            st.markdown("---")
    
    def display_lesson_content(self, lesson_id: int, mood_emoji: Optional[str] = None,
                            difficulty_emoji: Optional[str] = None) -> None:
        """Display the content of a specific lesson"""
        # Get the lesson
        lesson = self.get_lesson_by_id(lesson_id)
        
        if not lesson:
            st.error("Lesson not found.")
            if st.button("← Back to Lessons"):
                if "selected_lesson_id" in st.session_state:
                    del st.session_state.selected_lesson_id
                st.rerun()
            return
        
        # Display back button and lesson title
        col1, col2 = st.columns([1, 9])
        with col1:
            if st.button("← Back"):
                if "selected_lesson_id" in st.session_state:
                    del st.session_state.selected_lesson_id
                st.rerun()
        with col2:
            st.title(lesson.title)
        
        # Display lesson metadata
        st.write(f"**Difficulty:** {lesson.difficulty}")
        
        # Display tags if available
        if lesson.tags:
            tag_html = " ".join([f'<span style="background-color: #e0e0e0; padding: 3px 8px; border-radius: 10px; margin-right: 5px; font-size: 0.8em;">{tag}</span>' for tag in lesson.tags])
            st.markdown(f"**Tags:** {tag_html}", unsafe_allow_html=True)
        
        # Display selected mood and difficulty if available
        if mood_emoji or difficulty_emoji:
            mood_diff_col1, mood_diff_col2 = st.columns(2)
            with mood_diff_col1:
                if mood_emoji:
                    st.write(f"**Your mood:** {mood_emoji}")
            with mood_diff_col2:
                if difficulty_emoji:
                    st.write(f"**Your selected difficulty:** {difficulty_emoji}")
        
        st.markdown("---")
        
        # Display lesson content
        if lesson.content:
            # Introduction section
            if "introduction" in lesson.content:
                st.subheader("Introduction")
                st.write(lesson.content["introduction"])
            
            # Main content sections
            if "sections" in lesson.content:
                for i, section in enumerate(lesson.content["sections"]):
                    st.subheader(section.get("title", f"Section {i+1}"))
                    st.write(section.get("content", ""))
                    
                    # Examples
                    if "examples" in section:
                        with st.expander("Examples", expanded=True):
                            for j, example in enumerate(section["examples"]):
                                st.markdown(f"**Example {j+1}:**")
                                
                                if "japanese" in example:
                                    st.markdown(f"*Japanese:* {example['japanese']}")
                                
                                if "romaji" in example:
                                    st.markdown(f"*Romaji:* {example['romaji']}")
                                
                                if "english" in example:
                                    st.markdown(f"*English:* {example['english']}")
                                
                                if "explanation" in example:
                                    st.markdown(f"*Explanation:* {example['explanation']}")
                                
                                if j < len(section["examples"]) - 1:
                                    st.markdown("---")
                    
                    # Practice exercises
                    if "practice" in section:
                        with st.expander("Practice Exercises"):
                            for j, exercise in enumerate(section["practice"]):
                                st.markdown(f"**Exercise {j+1}:**")
                                
                                if "question" in exercise:
                                    st.markdown(exercise["question"])
                                
                                # Add answer reveal functionality
                                if "answer" in exercise:
                                    if st.button(f"Show Answer", key=f"answer_{i}_{j}"):
                                        st.success(f"Answer: {exercise['answer']}")
                                
                                if j < len(section["practice"]) - 1:
                                    st.markdown("---")
            
            # Summary
            if "summary" in lesson.content:
                st.subheader("Summary")
                st.write(lesson.content["summary"])
            
            # Additional resources
            if "resources" in lesson.content:
                st.subheader("Additional Resources")
                for resource in lesson.content["resources"]:
                    st.markdown(f"- [{resource.get('title', 'Resource')}]({resource.get('url', '#')}): {resource.get('description', '')}")
        else:
            st.warning("No content available for this lesson.")
        
        # Lesson completion form
        st.markdown("---")
        st.subheader("Mark as Completed")
        
        if self.has_user_completed_lesson(lesson_id):
            st.success("You have already completed this lesson.")
        else:
            with st.form(key="completion_form"):
                # Mood after lesson
                st.write("How do you feel after completing this lesson?")
                mood_options = ["😊", "😀", "😐", "😕", "😞"]
                mood_after = st.select_slider(
                    "Select your mood:",
                    options=mood_options,
                    value="😀"
                )
                
                # Difficulty rating
                difficulty_options = ["🌱 Too Easy", "🌿 Just Right", "🌲 Challenging", "🏔️ Too Difficult"]
                difficulty_rating = st.select_slider(
                    "How difficult was this lesson for you?",
                    options=difficulty_options,
                    value="🌿 Just Right"
                )
                
                # Satisfaction rating
                satisfaction = st.slider("How would you rate this lesson? (1-5)", 1, 5, 3)
                
                # Notes
                notes = st.text_area("Any notes or comments about this lesson?")
                
                # Submit button
                submit = st.form_submit_button("Mark as Completed")
                
                if submit:
                    # Get emoji from difficulty rating
                    difficulty_emoji_selected = difficulty_rating.split(" ")[0]
                    
                    # Record completion
                    self.record_completion(
                        lesson_id,
                        mood_before=mood_emoji,
                        mood_after=mood_after,
                        difficulty_selected=difficulty_emoji_selected,
                        satisfaction_rating=satisfaction,
                        notes=notes
                    )
                    
                    st.success("Lesson marked as completed! Great job!")
                    st.balloons()
    
    def get_lesson_recommendations(self, 
                                 completed_lessons: Optional[List[int]] = None, 
                                 preferred_difficulty: Optional[str] = None, 
                                 mood_score: Optional[int] = None) -> List[Lesson]:
        """Get personalized lesson recommendations based on user data"""
        # Get all lessons
        all_lessons = self.get_all_lessons()
        
        # If no lessons available, return empty list
        if not all_lessons:
            return []
        
        # Get user's completed lessons if not provided
        if completed_lessons is None:
            completed = self.get_user_lesson_history()
            completed_lessons = [c.lesson_id for c in completed]
        
        # Filter out completed lessons
        available_lessons = [l for l in all_lessons if l.id not in completed_lessons]
        
        # If no available lessons, recommend reviewing completed ones
        if not available_lessons:
            # Return a sample of completed lessons for review
            completed_full = [l for l in all_lessons if l.id in completed_lessons]
            return random.sample(completed_full, min(3, len(completed_full)))
        
        # Sort available lessons by relevance
        scored_lessons = []
        
        for lesson in available_lessons:
            score = 0
            
            # Adjust score based on difficulty preference
            if preferred_difficulty:
                if lesson.difficulty == preferred_difficulty:
                    score += 10
                elif lesson.difficulty in ["Beginner", "Elementary"] and preferred_difficulty in ["Beginner", "Elementary"]:
                    score += 5
                elif lesson.difficulty in ["Intermediate"] and preferred_difficulty in ["Elementary", "Intermediate", "Advanced"]:
                    score += 3
                elif lesson.difficulty in ["Advanced", "Native-like"] and preferred_difficulty in ["Advanced", "Native-like"]:
                    score += 5
            
            # Adjust score based on mood
            if mood_score is not None:
                # If user is feeling good (4-5), suggest more challenging content
                if mood_score >= 4:
                    if lesson.difficulty in ["Intermediate", "Advanced", "Native-like"]:
                        score += 5
                # If user is feeling neutral (3), maintain current level
                elif mood_score == 3:
                    if preferred_difficulty and lesson.difficulty == preferred_difficulty:
                        score += 3
                # If user is feeling frustrated (1-2), suggest easier content
                else:
                    if lesson.difficulty in ["Beginner", "Elementary"]:
                        score += 5
            
            scored_lessons.append((score, lesson))
        
        # Sort lessons by score (descending)
        scored_lessons.sort(reverse=True, key=lambda x: x[0])
        
        # Return top 5 recommendations
        return [lesson for _, lesson in scored_lessons[:5]]
    
    @staticmethod
    def generate_sample_lesson(difficulty: str, category: str) -> Dict:
        """Generate sample lesson content for development"""
        # Define lesson titles and content based on difficulty and category
        titles = {
            "grammar": {
                "Beginner": "Basic Japanese Sentence Structure",
                "Elementary": "Common Particles: は, が, を, に, で",
                "Intermediate": "Japanese Verb Conjugation: Te-form",
                "Advanced": "Complex Sentence Patterns with たら, なら, and ば",
                "Native-like": "Nuanced Expressions: 〜ものだ, 〜わけだ, 〜ことだ"
            },
            "vocabulary": {
                "Beginner": "Essential Japanese Greetings",
                "Elementary": "Food and Restaurant Vocabulary",
                "Intermediate": "Business Japanese Vocabulary",
                "Advanced": "Specialized Vocabulary for Academic Writing",
                "Native-like": "Regional Dialects and Slang"
            },
            "reading": {
                "Beginner": "Reading Hiragana and Katakana",
                "Elementary": "Simple Japanese Stories with Furigana",
                "Intermediate": "Reading Japanese News Articles",
                "Advanced": "Literary Japanese: Modern Fiction",
                "Native-like": "Classical Japanese Literature"
            },
            "listening": {
                "Beginner": "Understanding Simple Japanese Conversations",
                "Elementary": "Listening to Weather Forecasts",
                "Intermediate": "Japanese Drama Comprehension",
                "Advanced": "Understanding Fast-Paced Native Speech",
                "Native-like": "Regional Accents and Dialects"
            },
            "speaking": {
                "Beginner": "Basic Japanese Pronunciation",
                "Elementary": "Ordering Food and Shopping",
                "Intermediate": "Discussing Hobbies and Interests",
                "Advanced": "Debating Contemporary Issues",
                "Native-like": "Mastering Keigo (Honorific Speech)"
            },
            "writing": {
                "Beginner": "Writing Hiragana and Katakana",
                "Elementary": "Writing Basic Kanji",
                "Intermediate": "Composing Emails in Japanese",
                "Advanced": "Academic Essay Writing",
                "Native-like": "Creative Writing in Japanese"
            },
            "culture": {
                "Beginner": "Japanese Etiquette Basics",
                "Elementary": "Japanese Festivals and Traditions",
                "Intermediate": "Japanese Pop Culture and Media",
                "Advanced": "Japanese Business Culture",
                "Native-like": "Regional Cultural Differences in Japan"
            }
        }
        
        # Get title for this category and difficulty
        title = titles.get(category, {}).get(difficulty, f"{difficulty} {category.capitalize()} Lesson")
        
        # Generate appropriate introduction based on category and difficulty
        introductions = {
            "grammar": f"This lesson covers {difficulty.lower()} level Japanese grammar. Understanding these patterns will help you construct {['simple', 'proper', 'complex', 'sophisticated', 'nuanced'][['Beginner', 'Elementary', 'Intermediate', 'Advanced', 'Native-like'].index(difficulty)]} sentences.",
            "vocabulary": f"Expand your Japanese vocabulary with these {difficulty.lower()} level words. Building a strong vocabulary is essential for {['basic', 'everyday', 'intermediate', 'advanced', 'native-like'][['Beginner', 'Elementary', 'Intermediate', 'Advanced', 'Native-like'].index(difficulty)]} communication.",
            "reading": f"Improve your reading skills with {difficulty.lower()} level Japanese texts. This lesson will help you develop {['fundamental', 'basic', 'intermediate', 'advanced', 'native-level'][['Beginner', 'Elementary', 'Intermediate', 'Advanced', 'Native-like'].index(difficulty)]} reading comprehension.",
            "listening": f"Enhance your listening abilities with {difficulty.lower()} level audio materials. This lesson focuses on {['simple', 'everyday', 'natural', 'complex', 'nuanced'][['Beginner', 'Elementary', 'Intermediate', 'Advanced', 'Native-like'].index(difficulty)]} Japanese speech patterns.",
            "speaking": f"Practice your speaking skills with {difficulty.lower()} level conversation exercises. This lesson will help you speak more {['basically', 'naturally', 'fluently', 'eloquently', 'natively'][['Beginner', 'Elementary', 'Intermediate', 'Advanced', 'Native-like'].index(difficulty)]}.",
            "writing": f"Develop your writing ability with {difficulty.lower()} level writing exercises. This lesson covers {['basic', 'elementary', 'intermediate', 'advanced', 'native-level'][['Beginner', 'Elementary', 'Intermediate', 'Advanced', 'Native-like'].index(difficulty)]} Japanese writing.",
            "culture": f"Learn about Japanese culture with this {difficulty.lower()} level lesson. Understanding cultural context is {['helpful', 'important', 'essential', 'critical', 'fundamental'][['Beginner', 'Elementary', 'Intermediate', 'Advanced', 'Native-like'].index(difficulty)]} for truly mastering Japanese."
        }
        
        introduction = introductions.get(category, f"Welcome to this {difficulty} level lesson about Japanese {category}.")
        
        # Create sample content for sections
        section_content = []
        for i in range(3):  # Generate 3 sections
            section_title = f"Section {i+1}: {['Introduction to', 'Understanding', 'Mastering'][i]} {title.split(':')[-1] if ':' in title else title}"
            
            # Generate examples appropriate for the difficulty level
            examples = []
            for j in range(2):  # 2 examples per section
                if category == "grammar":
                    if difficulty == "Beginner":
                        examples.append({
                            "japanese": "私は学生です。",
                            "romaji": "Watashi wa gakusei desu.",
                            "english": "I am a student.",
                            "explanation": "This is a basic Japanese sentence using the topic particle は (wa) and the copula です (desu)."
                        })
                    elif difficulty == "Elementary":
                        examples.append({
                            "japanese": "私は図書館で勉強します。",
                            "romaji": "Watashi wa toshokan de benkyou shimasu.",
                            "english": "I study at the library.",
                            "explanation": "This sentence uses the particle で (de) to indicate the location where an action takes place."
                        })
                    elif difficulty == "Intermediate":
                        examples.append({
                            "japanese": "日本に行ったことがあります。",
                            "romaji": "Nihon ni itta koto ga arimasu.",
                            "english": "I have been to Japan.",
                            "explanation": "This sentence uses the ～たことがある pattern to express past experience."
                        })
                    elif difficulty == "Advanced":
                        examples.append({
                            "japanese": "試験に合格したらプレゼントを買ってあげます。",
                            "romaji": "Shiken ni goukaku shitara purezento wo katte agemasu.",
                            "english": "If you pass the exam, I'll buy you a present.",
                            "explanation": "This sentence uses the ～たら conditional form to express 'if/when' something happens."
                        })
                    else:  # Native-like
                        examples.append({
                            "japanese": "そんなことをすれば問題が起きるに決まっているじゃないか。",
                            "romaji": "Sonna koto wo sureba mondai ga okiru ni kimatte iru janai ka.",
                            "english": "It's obvious that doing such a thing will cause problems, isn't it?",
                            "explanation": "This sentence uses the pattern ～に決まっている to express certainty, along with the ～ば conditional and rhetorical question form."
                        })
                else:
                    # For non-grammar categories, create simpler examples
                    examples.append({
                        "japanese": f"Sample Japanese text for {difficulty} {category}",
                        "romaji": "Sample romaji transcription",
                        "english": f"Sample translation for {difficulty} {category}",
                        "explanation": f"This is an example relevant to {difficulty} level {category}."
                    })
            
            # Generate practice exercises
            practice = []
            for j in range(2):  # 2 exercises per section
                practice.append({
                    "question": f"Practice Question {j+1}: Complete the following sentence...",
                    "answer": "Sample answer to the practice question."
                })
            
            section_content.append({
                "title": section_title,
                "content": f"This section covers important aspects of {category} at the {difficulty} level. Pay special attention to the examples and practice exercises to reinforce your learning.",
                "examples": examples,
                "practice": practice
            })
        
        # Create sample summary
        summary = f"In this lesson, you learned about {difficulty.lower()} level Japanese {category}. Continue practicing these concepts to strengthen your skills."
        
        # Create sample resources
        resources = [
            {
                "title": "Japanese-English Dictionary",
                "url": "https://jisho.org/",
                "description": "A comprehensive online Japanese-English dictionary."
            },
            {
                "title": "Japanese Grammar Guide",
                "url": "https://guidetojapanese.org/",
                "description": "A detailed guide to Japanese grammar."
            }
        ]
        
        # Create attributes for content personalization
        attributes = {
            "engaging": random.choice([True, False]),
            "challenging": random.choice([True, False]),
            "visual": random.choice([True, False]),
            "structured": random.choice([True, False]),
            "interactive": random.choice([True, False]),
            "concise": random.choice([True, False]),
            "supportive": random.choice([True, False]),
            "practical": random.choice([True, False])
        }
        
        # Create the full lesson data
        lesson_data = {
            "title": title,
            "description": f"A {difficulty.lower()} level lesson focusing on Japanese {category}.",
            "difficulty": difficulty,
            "tags": [category, difficulty, f"{category}_{difficulty.lower()}"],
            "content": {
                "introduction": introduction,
                "sections": section_content,
                "summary": summary,
                "resources": resources,
                "attributes": attributes
            },
            "is_published": True
        }
        
        return lesson_data