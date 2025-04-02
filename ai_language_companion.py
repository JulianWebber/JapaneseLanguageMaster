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
            },
            "game_master": {
                "name": "ゲームマスター (Game Master)",
                "description": "A playful language tutor who uses games, challenges, and interactive activities to teach Japanese.",
                "avatar": "🎮",
                "system_prompt": (
                    "You are a playful Japanese language Game Master (ゲームマスター, Gēmu Masutā). "
                    "You make learning Japanese fun by incorporating games, challenges, quizzes, and interactive activities into your teaching. "
                    "You use a mix of casual and encouraging language, frequently praising effort and celebrating small victories. "
                    "You always structure your language games to be appropriate for the user's level while still being challenging enough to promote growth. "
                    "You keep track of 'game points' within a conversation and offer virtual rewards for completion of challenges. "
                    "You're creative with wordplay, associations, mnemonics, and stories to help vocabulary and grammar stick in memory. "
                    "You make every interaction feel like a language adventure rather than formal study."
                )
            },
            "travel_guide": {
                "name": "旅行ガイド (Travel Guide)",
                "description": "A helpful companion who teaches practical Japanese for travelers and shares recommendations about places to visit.",
                "avatar": "🧭",
                "system_prompt": (
                    "You are a Japanese travel guide (旅行ガイド, Ryokō Gaido) who helps prepare travelers for visiting Japan. "
                    "You focus on teaching practical travel-related phrases, vocabulary for transportation, accommodations, dining, and sightseeing. "
                    "You share insider tips about regions of Japan, tourism etiquette, and navigating cultural differences. "
                    "You provide specific recommendations about places to visit, seasonal events, and authentic experiences. "
                    "Your language is enthusiastic but practical, focusing on immediately useful expressions for travelers. "
                    "You often discuss regional dialects, local specialties, and how to read signs and transportation information. "
                    "You help the user understand how to communicate effectively in common travel scenarios."
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
    
    def send_message(self, message: str, track_metrics: bool = True) -> Dict[str, Any]:
        """
        Send a message to the AI companion and get a response
        
        Args:
            message: The user's message text
            track_metrics: Whether to track conversation metrics
            
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
        
    def get_conversation_starters(self, category: str = "general") -> List[Dict[str, str]]:
        """
        Get a list of suggested conversation starters based on the selected category
        
        Args:
            category: The topic category for conversation starters (general, travel, culture, etc.)
            
        Returns:
            List of conversation starter suggestions with prompts in both English and Japanese
        """
        # Define conversation starters by category and user level
        level = self.user_profile.get("level", "beginner")
        
        starters = {
            "general": {
                "beginner": [
                    {"en": "Hello! How are you today?", "ja": "こんにちは！お元気ですか？"},
                    {"en": "My name is [Your Name]. Nice to meet you.", "ja": "私の名前は[Your Name]です。よろしくお願いします。"},
                    {"en": "What's the weather like today?", "ja": "今日の天気はどうですか？"},
                    {"en": "I'm learning Japanese. Can you help me?", "ja": "日本語を勉強しています。手伝ってくれますか？"},
                    {"en": "What time is it now?", "ja": "今何時ですか？"}
                ],
                "intermediate": [
                    {"en": "What kind of hobbies do you enjoy in your free time?", "ja": "暇な時間には、どんな趣味を楽しんでいますか？"},
                    {"en": "Could you recommend some good Japanese music?", "ja": "いい日本の音楽をおすすめしていただけますか？"},
                    {"en": "What Japanese foods do you think I should try?", "ja": "どんな日本料理を食べてみるべきだと思いますか？"},
                    {"en": "I watched an interesting movie yesterday. Do you like movies?", "ja": "昨日、面白い映画を見ました。映画は好きですか？"},
                    {"en": "What's your favorite season and why?", "ja": "一番好きな季節は何ですか？そしてなぜですか？"}
                ],
                "advanced": [
                    {"en": "What are your thoughts on the recent trends in Japanese popular culture?", "ja": "最近の日本のポップカルチャーのトレンドについてどう思いますか？"},
                    {"en": "If you could change one thing about your daily routine, what would it be?", "ja": "日常のルーティンで一つ変えられるとしたら、何を変えますか？"},
                    {"en": "What are some challenges that face modern Japanese society?", "ja": "現代の日本社会が直面している課題にはどのようなものがありますか？"},
                    {"en": "Do you think AI will have a positive or negative impact on language learning?", "ja": "AIは語学学習にポジティブな影響をもたらすと思いますか、それともネガティブな影響でしょうか？"},
                    {"en": "What's a book or article that changed your perspective recently?", "ja": "最近あなたの視点を変えた本や記事はありますか？"}
                ]
            },
            "travel": {
                "beginner": [
                    {"en": "Where is a good place to visit in Japan?", "ja": "日本でおすすめの観光地はどこですか？"},
                    {"en": "How do I get to the train station?", "ja": "駅へはどうやって行きますか？"},
                    {"en": "Is this train going to Tokyo?", "ja": "この電車は東京行きですか？"},
                    {"en": "I'd like to go to a restaurant.", "ja": "レストランに行きたいです。"},
                    {"en": "How much does this cost?", "ja": "これはいくらですか？"}
                ],
                "intermediate": [
                    {"en": "Can you recommend some less touristy places to visit?", "ja": "あまり観光客が行かないおすすめの場所はありますか？"},
                    {"en": "What's the best way to experience traditional Japanese culture?", "ja": "伝統的な日本文化を体験するのに最適な方法は何ですか？"},
                    {"en": "Are there any local festivals happening while I'm visiting?", "ja": "滞在中に行われるローカルな祭りはありますか？"},
                    {"en": "What's the most efficient way to travel between cities in Japan?", "ja": "日本の都市間を移動する最も効率的な方法は何ですか？"},
                    {"en": "Where can I find authentic local cuisine?", "ja": "本格的な地元料理はどこで食べられますか？"}
                ],
                "advanced": [
                    {"en": "How has tourism changed this region over the last decade?", "ja": "この地域は過去10年間で観光によってどのように変化しましたか？"},
                    {"en": "What are some cultural etiquette rules that foreign visitors often misunderstand?", "ja": "外国人観光客がよく誤解する文化的なマナーには何がありますか？"},
                    {"en": "Could you explain the historical significance of this area?", "ja": "この地域の歴史的な重要性について説明していただけますか？"},
                    {"en": "What conservation efforts are being made to preserve traditional architecture here?", "ja": "ここでの伝統的な建築を保存するためにどのような保全活動が行われていますか？"},
                    {"en": "How do locals feel about the increase in international tourism?", "ja": "国際観光の増加について地元の人々はどう感じていますか？"}
                ]
            },
            "culture": {
                "beginner": [
                    {"en": "What are popular holidays in Japan?", "ja": "日本で人気のある祝日は何ですか？"},
                    {"en": "I like anime. Do you watch anime?", "ja": "アニメが好きです。アニメを見ますか？"},
                    {"en": "What food is famous in your region?", "ja": "あなたの地域で有名な食べ物は何ですか？"},
                    {"en": "Do you like Japanese music?", "ja": "日本の音楽は好きですか？"},
                    {"en": "What's your favorite season in Japan?", "ja": "日本で一番好きな季節は何ですか？"}
                ],
                "intermediate": [
                    {"en": "Could you explain the concept of 'wabi-sabi'?", "ja": "「侘び寂び」の概念を説明していただけますか？"},
                    {"en": "What are some important cultural values in Japanese society?", "ja": "日本社会における重要な文化的価値観にはどのようなものがありますか？"},
                    {"en": "How do traditional and modern culture mix in contemporary Japan?", "ja": "現代の日本では、伝統文化と現代文化がどのように融合していますか？"},
                    {"en": "Can you tell me about the tea ceremony tradition?", "ja": "茶道の伝統について教えていただけますか？"},
                    {"en": "What's the significance of seasonal events in Japanese culture?", "ja": "日本文化における季節のイベントの意義は何ですか？"}
                ],
                "advanced": [
                    {"en": "How has the concept of 'uchi-soto' influenced communication styles in Japan?", "ja": "「内外」の概念は日本のコミュニケーションスタイルにどのような影響を与えていますか？"},
                    {"en": "What role do traditional arts play in preserving cultural identity in modern Japan?", "ja": "伝統芸能は現代日本の文化的アイデンティティの保存にどのような役割を果たしていますか？"},
                    {"en": "How are changing family structures affecting traditional cultural practices?", "ja": "変化する家族構造は伝統的な文化的慣行にどのような影響を与えていますか？"},
                    {"en": "Can you discuss the philosophical underpinnings of Japanese aesthetics?", "ja": "日本の美学の哲学的基盤について議論していただけますか？"},
                    {"en": "How has globalization influenced Japanese cultural expression in the 21st century?", "ja": "グローバリゼーションは21世紀の日本の文化的表現にどのような影響を与えましたか？"}
                ]
            },
            "business": {
                "beginner": [
                    {"en": "Nice to meet you. I'm [Your Name] from [Company].", "ja": "はじめまして。[Company]の[Your Name]です。"},
                    {"en": "Please give me your business card.", "ja": "名刺をいただけますか。"},
                    {"en": "What time is our meeting?", "ja": "会議は何時ですか？"},
                    {"en": "I'd like to schedule a meeting.", "ja": "会議の予定を立てたいです。"},
                    {"en": "Thank you for your cooperation.", "ja": "ご協力ありがとうございます。"}
                ],
                "intermediate": [
                    {"en": "Could we discuss the details of our potential collaboration?", "ja": "潜在的な協力関係の詳細について話し合えますか？"},
                    {"en": "What are your company's main objectives for this quarter?", "ja": "今四半期の御社の主な目標は何ですか？"},
                    {"en": "I'd like to hear more about your approach to market challenges.", "ja": "市場の課題に対するアプローチについてもっと聞かせていただきたいです。"},
                    {"en": "How does your team handle project management?", "ja": "プロジェクト管理はどのように行っていますか？"},
                    {"en": "Can you explain your company's organizational structure?", "ja": "御社の組織構造について説明していただけますか？"}
                ],
                "advanced": [
                    {"en": "What strategies is your company implementing to address sustainability concerns?", "ja": "持続可能性の懸念に対処するために御社ではどのような戦略を実施していますか？"},
                    {"en": "How do you see the industry evolving over the next five years?", "ja": "今後5年間で業界はどのように進化すると思いますか？"},
                    {"en": "What innovative approaches has your team developed to address market disruptions?", "ja": "市場の混乱に対処するために、チームはどのような革新的なアプローチを開発しましたか？"},
                    {"en": "Could we discuss the implications of recent regulatory changes on our partnership?", "ja": "最近の規制変更がパートナーシップに与える影響について話し合えますか？"},
                    {"en": "How does your organization balance tradition and innovation in its corporate culture?", "ja": "御社は企業文化において伝統と革新のバランスをどのように取っていますか？"}
                ]
            }
        }
        
        # Return starters based on category and level
        if category in starters and level in starters[category]:
            return starters[category][level]
        
        # Default to general beginner if category not found
        return starters["general"]["beginner"]
        
    def record_user_reaction(self, message_id: int, reaction: str) -> Dict[str, Any]:
        """
        Record a user's reaction to an AI response for personalization
        
        Args:
            message_id: The ID of the message being reacted to
            reaction: The reaction emoji or code (e.g., "helpful", "confusing", "interesting")
            
        Returns:
            Success status and updated reaction information
        """
        if message_id < 0 or message_id >= len(self.chat_history):
            return {"success": False, "error": "Invalid message ID"}
            
        # Define meaning for different reaction types
        reaction_meanings = {
            "👍": "helpful",
            "👎": "not_helpful",
            "😕": "confusing",
            "💡": "insightful",
            "🔄": "want_more_examples",
            "⭐": "favorite",
            "❤️": "loved_it",
            "🤔": "needs_clarification",
            "📝": "want_to_practice_this",
            "🎯": "exactly_what_i_needed"
        }
        
        # Translate emoji to meaning if needed
        reaction_meaning = reaction_meanings.get(reaction, reaction)
        
        # Add reaction to the message
        if "reactions" not in self.chat_history[message_id]:
            self.chat_history[message_id]["reactions"] = []
            
        self.chat_history[message_id]["reactions"].append({
            "reaction": reaction,
            "meaning": reaction_meaning,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Use reaction to adjust future responses
        if message_id > 0 and self.chat_history[message_id]["role"] == "assistant":
            # Analyze previous messages to refine understanding
            message_content = self.chat_history[message_id]["content"]
            previous_message = self.chat_history[message_id-1]["content"] if message_id > 0 else ""
            
            # In a real implementation, we would store this in a database for learning
            # For now, we'll simply return confirmation
            return {
                "success": True,
                "message": "Reaction recorded and will be used to personalize future responses",
                "reaction_data": {
                    "reaction": reaction,
                    "meaning": reaction_meaning,
                    "message_role": self.chat_history[message_id]["role"],
                    "message_preview": message_content[:50] + "..." if len(message_content) > 50 else message_content
                }
            }
        
        return {"success": True, "message": "Reaction recorded"}
    
    def generate_flashcards(self, topic: str, count: int = 5) -> List[Dict[str, str]]:
        """
        Generate vocabulary flashcards based on a specific topic
        
        Args:
            topic: The vocabulary topic
            count: Number of flashcards to generate (default: 5)
            
        Returns:
            List of flashcards with Japanese, English, example sentence, and notes
        """
        if not self.openai_client:
            return [{"error": "Unable to generate flashcards due to API connection issues."}]
        
        # Get user's level
        level = self.user_profile.get("level", "beginner")
        
        # Prepare the prompt
        prompt = f"""
        Generate {count} vocabulary flashcards for a {level}-level Japanese language learner on the topic of "{topic}".
        
        For each flashcard, provide:
        1. The Japanese term (with kanji if appropriate for {level} level)
        2. The reading in hiragana
        3. The English definition
        4. An example sentence in Japanese
        5. The English translation of the sentence
        6. A short learning note or mnemonic to help remember the word
        
        Return the flashcards as a JSON array of objects with the fields: 
        "japanese", "reading", "english", "example_ja", "example_en", and "note"
        """
        
        try:
            # Send to the OpenAI API with a structured response format
            response = self.openai_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a helpful Japanese language tutor specializing in vocabulary development."},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4o",
                response_format={"type": "json_object"}
            )
            
            # Extract the content and parse the JSON
            content = self.openai_client.extract_content(response)
            try:
                result = json.loads(content)
                if "flashcards" in result:
                    return result["flashcards"]
                else:
                    return result.get("cards", [])
            except json.JSONDecodeError:
                # If not valid JSON, try to extract structured data with a simpler format
                return [{"error": "Could not parse the generated flashcards."}]
                
        except Exception as e:
            return [{"error": f"Error generating flashcards: {str(e)}"}]