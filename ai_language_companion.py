"""
Personalized AI Language Learning Companion

This module implements a chatbot interface that serves as a personalized
Japanese language learning assistant using OpenAI's GPT models.
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from database import get_db, UserProgress, LanguageAssessment

class AILanguageCompanion:
    """
    An AI-powered language learning companion that provides personalized
    Japanese language practice, explanations, and conversation.
    """
    
    def __init__(self, session_id: str):
        """
        Initialize the AI language companion.
        
        Args:
            session_id: The user's session ID for progress tracking
        """
        self.session_id = session_id
        self.chat_history = []
        self.openai_client = None
        self._initialize_client()
        self.user_profile = self._load_user_profile()
        self.companion_personalities = {
            "sensei": {
                "name": "先生 (Sensei)",
                "description": "A traditional Japanese language teacher who is formal, patient, and thorough.",
                "avatar": "👨‍🏫",
                "system_prompt": (
                    "You are a traditional Japanese language teacher (先生, Sensei). "
                    "You are formal, patient, and thorough in your explanations. "
                    "You always provide example sentences and cultural context when explaining Japanese language concepts. "
                    "You use polite, respectful language and occasionally use Japanese terms of respect like '〜さん'. "
                    "You focus on proper grammar, correct usage, and helping the student understand the nuances of Japanese. "
                    "You sometimes refer to traditional Japanese learning methods and always emphasize the importance of practice."
                )
            },
            "friend": {
                "name": "友達 (Tomodachi)",
                "description": "A friendly Japanese conversation partner who uses casual language and encourages practical usage.",
                "avatar": "😊",
                "system_prompt": (
                    "You are a friendly Japanese conversation partner (友達, Tomodachi). "
                    "You use casual, everyday Japanese language and encourage natural conversation. "
                    "You often use casual Japanese expressions and slang appropriately, and explain them when you do. "
                    "Your focus is on helping the user become comfortable with practical, everyday Japanese. "
                    "You're encouraging, positive, and sometimes share fun facts about Japanese culture and daily life in Japan. "
                    "You prefer to correct mistakes gently and indirectly, focusing more on maintaining a natural conversation flow."
                )
            },
            "anime_fan": {
                "name": "アニメファン (Anime Fan)",
                "description": "An enthusiastic anime and manga fan who teaches using references to popular media.",
                "avatar": "🎭",
                "system_prompt": (
                    "You are an enthusiastic anime and manga fan who teaches Japanese through popular media references. "
                    "You often reference phrases, expressions, and language patterns from anime and manga to explain concepts. "
                    "You use a mix of excited and casual language, occasionally using anime catchphrases when appropriate. "
                    "You're knowledgeable about how Japanese is used in entertainment media vs. real life, and explain those differences. "
                    "You make learning fun by connecting language points to stories and characters the user might know. "
                    "You're encouraging and emphasize that learning Japanese can help with enjoying anime and manga in their original language."
                )
            },
            "cultural_guide": {
                "name": "文化ガイド (Cultural Guide)",
                "description": "A knowledgeable guide who connects language learning to Japanese cultural practices and traditions.",
                "avatar": "🏯",
                "system_prompt": (
                    "You are a knowledgeable Japanese cultural guide (文化ガイド, Bunka Gaido). "
                    "You connect language learning to Japanese cultural practices, traditions, history, and philosophy. "
                    "When explaining language concepts, you provide rich cultural context and how the language reflects Japanese worldviews. "
                    "You often refer to seasonal traditions, historical periods, art forms, or philosophical concepts when relevant. "
                    "You use thoughtful, somewhat formal language with a focus on the deeper meanings behind expressions. "
                    "You help the user understand not just how to speak Japanese, but how to appreciate the cultural contexts that shape the language."
                )
            },
            "business_coach": {
                "name": "ビジネスコーチ (Business Coach)",
                "description": "A professional who focuses on business Japanese and formal language for workplace settings.",
                "avatar": "💼",
                "system_prompt": (
                    "You are a Japanese business language coach (ビジネスコーチ, Bijinesu Kōchi). "
                    "You focus on helping the user master formal, professional Japanese for workplace settings. "
                    "You emphasize keigo (honorific language), appropriate business etiquette, and professional communication norms. "
                    "You use polished, precise language and teach the user about the hierarchical nature of Japanese business communication. "
                    "You often provide examples of email templates, meeting phrases, or presentation language. "
                    "You help the user understand the nuances of politeness levels and how to navigate Japanese business relationships through language."
                )
            }
        }
        self.selected_personality = "sensei"  # Default personality
        
    def _initialize_client(self):
        """Initialize the OpenAI client for interacting with GPT models"""
        try:
            from gpt_client import OpenAIClient
            self.openai_client = OpenAIClient()
        except Exception as e:
            print(f"Error initializing OpenAI client: {str(e)}")
            self.openai_client = None
    
    def _load_user_profile(self) -> Dict[str, Any]:
        """
        Load the user's profile and learning progress from the database
        
        Returns:
            Dictionary containing user profile information
        """
        db = next(get_db())
        try:
            user_progress = UserProgress.get_or_create(db, self.session_id)
            latest_assessment = LanguageAssessment.get_latest_assessment(db, self.session_id)
            
            # Extract user profile data
            profile = {
                "total_checks": user_progress.total_checks,
                "total_correct": user_progress.total_correct,
                "average_accuracy": user_progress.average_accuracy,
                "current_streak": user_progress.current_streak,
                "particle_mastery": user_progress.particle_mastery,
                "verb_mastery": user_progress.verb_mastery,
                "pattern_mastery": user_progress.pattern_mastery,
                "achievements": user_progress.achievements,
                "level": "beginner"
            }
            
            # Add assessment data if available
            if latest_assessment:
                profile["self_rated_level"] = latest_assessment.self_rated_level
                profile["recommended_level"] = latest_assessment.recommended_level
                profile["weak_areas"] = latest_assessment.weak_areas
                profile["strong_areas"] = latest_assessment.strong_areas
                profile["level"] = latest_assessment.recommended_level or "beginner"
            
            return profile
        finally:
            db.close()
    
    def select_personality(self, personality_key: str) -> bool:
        """
        Select a companion personality
        
        Args:
            personality_key: The key of the personality to select
            
        Returns:
            True if successful, False if the personality doesn't exist
        """
        if personality_key in self.companion_personalities:
            self.selected_personality = personality_key
            return True
        return False
    
    def get_available_personalities(self) -> Dict[str, Dict[str, str]]:
        """
        Get the list of available companion personalities
        
        Returns:
            Dictionary of personality information
        """
        return {k: {
            "name": v["name"],
            "description": v["description"],
            "avatar": v["avatar"]
        } for k, v in self.companion_personalities.items()}
    
    def get_current_personality(self) -> Dict[str, str]:
        """
        Get the current selected personality
        
        Returns:
            Dictionary with current personality information
        """
        personality = self.companion_personalities[self.selected_personality]
        return {
            "key": self.selected_personality,
            "name": personality["name"],
            "description": personality["description"],
            "avatar": personality["avatar"]
        }
    
    def send_message(self, message: str) -> Dict[str, Any]:
        """
        Send a message to the AI companion and get a response
        
        Args:
            message: The user's message text
            
        Returns:
            Dictionary with the AI's response and any additional data
        """
        if not self.openai_client:
            return {
                "response": "申し訳ありません (I apologize), but I'm unable to connect to my language model at the moment. Please check your API key configuration.",
                "error": True
            }
        
        # Reload user profile for the latest progress
        self.user_profile = self._load_user_profile()
        
        # Add the user message to history
        self.chat_history.append({"role": "user", "content": message})
        
        # Prepare the system message with personality and user profile
        personality = self.companion_personalities[self.selected_personality]
        system_message = self._create_system_message(personality["system_prompt"])
        
        # Create the messages array for the API call
        messages = [
            {"role": "system", "content": system_message}
        ]
        
        # Add conversation history (limited to last 10 messages to save tokens)
        history_to_include = self.chat_history[-10:] if len(self.chat_history) > 10 else self.chat_history
        messages.extend(history_to_include)
        
        try:
            # Send to the OpenAI API
            response = self.openai_client.chat_completion(
                messages=messages,
                model="gpt-4o",  # Use the newest model as of May 2024
                temperature=0.7
            )
            
            # Extract the response content
            ai_response = self.openai_client.extract_content(response)
            
            # Add to chat history
            self.chat_history.append({"role": "assistant", "content": ai_response})
            
            return {
                "response": ai_response,
                "error": False
            }
        except Exception as e:
            error_message = f"Error communicating with the language model: {str(e)}"
            return {
                "response": error_message,
                "error": True
            }
    
    def _create_system_message(self, base_prompt: str) -> str:
        """
        Create a detailed system message that includes user profile information
        
        Args:
            base_prompt: The base personality prompt
            
        Returns:
            Complete system message with user profile context
        """
        # Get user's level
        level = self.user_profile.get("level", "beginner")
        
        # Create a level-appropriate language instruction
        level_instruction = ""
        if level == "beginner":
            level_instruction = (
                "Use simple Japanese with basic grammar patterns. "
                "Always provide the meaning of Japanese phrases in English. "
                "Use only hiragana, katakana, and the most common kanji with furigana. "
                "Speak slowly with short sentences and provide romaji when helpful."
            )
        elif level == "intermediate":
            level_instruction = (
                "Use a mix of simple and moderate Japanese grammar patterns. "
                "Provide the meaning of advanced Japanese phrases in English. "
                "Use common kanji with furigana for rare kanji. "
                "Speak at a moderate pace with more complex sentence structures."
            )
        else:  # advanced
            level_instruction = (
                "Use natural Japanese including advanced grammar patterns. "
                "You can use more idiomatic expressions and advanced vocabulary. "
                "Use kanji naturally without furigana except for very rare characters. "
                "Speak at a natural pace and use authentic language patterns."
            )
        
        # Get information about the user's strengths and weaknesses
        weak_areas = ", ".join(self.user_profile.get("weak_areas", ["Basic grammar"]))
        strong_areas = ", ".join(self.user_profile.get("strong_areas", []))
        
        # Create the full system message
        system_message = (
            f"{base_prompt}\n\n"
            f"User information:\n"
            f"- Japanese level: {level}\n"
            f"- Areas to focus on: {weak_areas}\n"
            f"- Strong areas: {strong_areas}\n"
            f"- Current learning streak: {self.user_profile.get('current_streak', 0)} days\n\n"
            f"Language adaptation instructions:\n{level_instruction}\n\n"
            "Guidelines for your responses:\n"
            "1. Be encouraging and supportive of the learner's progress.\n"
            "2. When correcting mistakes, first acknowledge what was done correctly.\n"
            "3. Provide examples that are relevant to everyday situations.\n"
            "4. When introducing new vocabulary or grammar, connect it to what the user already knows.\n"
            "5. Occasionally ask questions to check understanding and encourage practice.\n"
            "6. If the user asks about a specific grammar point, provide clear explanations with examples.\n"
            "7. Respond appropriately to the user's questions about Japanese language or culture."
        )
        
        return system_message
    
    def generate_practice_exercise(self, exercise_type: str) -> Dict[str, Any]:
        """
        Generate a personalized practice exercise based on the user's level
        
        Args:
            exercise_type: The type of exercise to generate (e.g., "grammar", "vocabulary", "conversation")
            
        Returns:
            Dictionary containing the exercise content
        """
        if not self.openai_client:
            return {
                "exercise": "Unable to generate exercise due to API connection issues.",
                "error": True
            }
        
        # Reload user profile for the latest progress
        self.user_profile = self._load_user_profile()
        
        # Determine user's level
        level = self.user_profile.get("level", "beginner")
        
        # Get weak areas to focus on
        weak_areas = self.user_profile.get("weak_areas", ["Basic grammar"])
        weak_area_focus = weak_areas[0] if weak_areas else "General Japanese"
        
        # Create a prompt based on the exercise type
        if exercise_type == "grammar":
            prompt = (
                f"Create a personalized Japanese grammar exercise at the {level} level. "
                f"Focus on the user's weak area: {weak_area_focus}. "
                f"Include 3 practice sentences with blanks to fill in, answer choices, and explanations. "
                f"Format the response as a structured exercise with clear instructions, questions, answer choices, "
                f"and answer key with explanations. Ensure the difficulty is appropriate for a {level} level learner."
            )
        elif exercise_type == "vocabulary":
            prompt = (
                f"Create a personalized Japanese vocabulary exercise at the {level} level. "
                f"Choose a theme relevant to everyday situations. "
                f"Include 5 vocabulary words with their readings, meanings, and example sentences. "
                f"Then create a matching or fill-in-the-blank exercise using these words. "
                f"Format the response as a structured exercise with clear instructions, questions, "
                f"and answer key with explanations. Ensure the difficulty is appropriate for a {level} level learner."
            )
        elif exercise_type == "conversation":
            prompt = (
                f"Create a short Japanese conversation scenario at the {level} level. "
                f"The scenario should be practical and relevant to daily life in Japan. "
                f"Create a dialogue with 6-8 exchanges between two people. "
                f"Include the Japanese text, English translation, and notes about any important grammar points or cultural aspects. "
                f"Then add 2-3 comprehension questions about the dialogue. "
                f"Format the response as a structured exercise with clear sections. Ensure the difficulty is appropriate for a {level} level learner."
            )
        elif exercise_type == "reading":
            prompt = (
                f"Create a short Japanese reading passage at the {level} level. "
                f"The passage should be about an interesting aspect of Japanese culture or daily life. "
                f"Include the Japanese text with appropriate kanji usage for {level} level, followed by vocabulary notes, "
                f"and then an English translation. Add 3 comprehension questions about the passage. "
                f"Format the response as a structured exercise with clear sections. Ensure the difficulty is appropriate for a {level} level learner."
            )
        else:
            prompt = (
                f"Create a mixed Japanese language exercise at the {level} level. "
                f"Include elements of grammar, vocabulary, and practical usage. "
                f"Focus on the user's weak area: {weak_area_focus}. "
                f"Format the response as a structured exercise with clear instructions, questions, "
                f"and answer key with explanations. Ensure the difficulty is appropriate for a {level} level learner."
            )
        
        try:
            # Send to the OpenAI API
            response = self.openai_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Japanese language teacher who creates personalized learning exercises."},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4o",  # Use the newest model as of May 2024
                temperature=0.7
            )
            
            # Extract the response content
            exercise_content = self.openai_client.extract_content(response)
            
            return {
                "exercise": exercise_content,
                "type": exercise_type,
                "level": level,
                "focus": weak_area_focus,
                "error": False
            }
        except Exception as e:
            error_message = f"Error generating exercise: {str(e)}"
            return {
                "exercise": error_message,
                "error": True
            }
    
    def translate_text(self, text: str, direction: str = "ja_to_en") -> Dict[str, Any]:
        """
        Translate text between Japanese and English
        
        Args:
            text: The text to translate
            direction: Translation direction ("ja_to_en" or "en_to_ja")
            
        Returns:
            Dictionary with the translation and any notes
        """
        if not self.openai_client:
            return {
                "translation": "Unable to translate due to API connection issues.",
                "error": True
            }
        
        # Create a prompt based on the direction
        if direction == "ja_to_en":
            prompt = (
                f"Translate the following Japanese text to natural English:\n\n{text}\n\n"
                f"If there are any cultural nuances or idiomatic expressions that are important to understand, "
                f"please provide notes about them after the translation."
            )
        else:  # en_to_ja
            # Get user's level to adjust translation complexity
            level = self.user_profile.get("level", "beginner")
            
            level_instruction = ""
            if level == "beginner":
                level_instruction = "Use simple grammar patterns and vocabulary appropriate for beginners. Use hiragana and katakana with basic kanji."
            elif level == "intermediate":
                level_instruction = "Use intermediate grammar patterns and vocabulary. Use common kanji appropriate for intermediate learners."
            else:  # advanced
                level_instruction = "Use natural Japanese including advanced grammar patterns and vocabulary. Use kanji naturally as a native speaker would."
            
            prompt = (
                f"Translate the following English text to Japanese at a {level} level:\n\n{text}\n\n"
                f"{level_instruction}\n\n"
                f"Provide the translation in Japanese, followed by a romanized version in romaji, "
                f"and notes about any grammar points or vocabulary that might be new to a {level} level learner."
            )
        
        try:
            # Send to the OpenAI API
            response = self.openai_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a professional Japanese-English translator with excellent cultural understanding."},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4o",  # Use the newest model as of May 2024
                temperature=0.3  # Lower temperature for translation accuracy
            )
            
            # Extract the response content
            translation_content = self.openai_client.extract_content(response)
            
            return {
                "translation": translation_content,
                "direction": direction,
                "error": False
            }
        except Exception as e:
            error_message = f"Error during translation: {str(e)}"
            return {
                "translation": error_message,
                "error": True
            }
    
    def explain_grammar_point(self, grammar_point: str) -> Dict[str, Any]:
        """
        Provide a detailed explanation of a specific Japanese grammar point
        
        Args:
            grammar_point: The grammar point to explain
            
        Returns:
            Dictionary with the explanation and examples
        """
        if not self.openai_client:
            return {
                "explanation": "Unable to provide explanation due to API connection issues.",
                "error": True
            }
        
        # Get user's level
        level = self.user_profile.get("level", "beginner")
        
        # Prepare prompt for grammar explanation
        prompt = (
            f"Explain the Japanese grammar point '{grammar_point}' for a {level} level learner.\n\n"
            f"Include:\n"
            f"1. A clear explanation of how to use this grammar\n"
            f"2. The formation or conjugation pattern\n"
            f"3. Common usage contexts\n"
            f"4. At least 3 example sentences with translations\n"
            f"5. Any similar grammar points and how they differ\n"
            f"6. Common mistakes to avoid\n\n"
            f"Adjust the complexity of your explanation for a {level} level learner."
        )
        
        try:
            # Send to the OpenAI API
            response = self.openai_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Japanese grammar expert who explains concepts clearly with helpful examples."},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4o",  # Use the newest model as of May 2024
                temperature=0.5
            )
            
            # Extract the response content
            explanation_content = self.openai_client.extract_content(response)
            
            return {
                "explanation": explanation_content,
                "grammar_point": grammar_point,
                "error": False
            }
        except Exception as e:
            error_message = f"Error generating explanation: {str(e)}"
            return {
                "explanation": error_message,
                "error": True
            }
    
    def clear_chat_history(self) -> None:
        """Clear the conversation history"""
        self.chat_history = []