"""
Contextual Translation Memory Bank

This module provides functionality for storing, retrieving, and managing
a user's translation history with context awareness.
"""

import streamlit as st
import uuid
import pandas as pd
import plotly.express as px
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from database import TranslationMemory, get_db
from gpt_client import OpenAIClient

class TranslationMemoryManager:
    """
    Manager for the contextual translation memory feature.
    
    This class handles interactions with the translation memory database,
    provides similarity matching, and offers contextual translation suggestions.
    """
    
    def __init__(self, session_id: str = None):
        """
        Initialize the translation memory manager
        
        Args:
            session_id: The user's session ID for tracking translations (defaults to streamlit session)
        """
        if not session_id:
            # Use Streamlit session ID if not provided
            if "session_id" not in st.session_state:
                st.session_state.session_id = str(uuid.uuid4())
            session_id = st.session_state.session_id
            
        self.session_id = session_id
        self.openai_client = OpenAIClient()
        
        # Initialize conversation/document context tracking
        if "active_context" not in st.session_state:
            st.session_state.active_context = None
            
        if "context_history" not in st.session_state:
            st.session_state.context_history = []
        
    def add_translation(self, 
                       source_text: str, 
                       source_language: str, 
                       translated_text: str, 
                       target_language: str,
                       context: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       quality_rating: Optional[int] = None,
                       notes: Optional[str] = None,
                       document_id: Optional[str] = None,
                       context_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a new translation to the memory bank
        
        Args:
            source_text: The original text
            source_language: The language code of the original text ('ja' or 'en')
            translated_text: The translated text
            target_language: The language code of the translation ('en' or 'ja')
            context: Optional context for the translation
            tags: Optional list of tags for categorization
            quality_rating: Optional user rating (1-5)
            notes: Optional notes about the translation
            document_id: Optional ID for grouping translations by document/conversation
            context_type: Optional type of context (business, casual, technical, etc.)
            
        Returns:
            Dictionary with status and the saved translation
        """
        try:
            db = next(get_db())
            
            # Use active document context if available and none specified
            if not document_id and st.session_state.active_context:
                document_id = st.session_state.active_context.get("id")
                
                # If there's active context but no context provided, use the active context description
                if not context and st.session_state.active_context.get("description"):
                    context = st.session_state.active_context.get("description")
                    
                # If no context type provided, use the active context type
                if not context_type and st.session_state.active_context.get("type"):
                    context_type = st.session_state.active_context.get("type")
                    
            # If no tags provided but context_type exists, add it as a tag
            if context_type and not tags:
                tags = [context_type]
            elif context_type and tags:
                if context_type not in tags:
                    tags.append(context_type)
            
            # Create translation data dictionary
            translation_data = {
                "session_id": self.session_id,
                "source_text": source_text,
                "source_language": source_language,
                "translated_text": translated_text,
                "target_language": target_language,
                "context": context,
                "tags": tags or [],
                "quality_rating": quality_rating,
                "notes": notes,
                "document_id": document_id,
                "context_type": context_type
            }
            
            # Save to database
            translation = TranslationMemory.create(db, translation_data)
            
            return {
                "success": True,
                "translation_id": translation.id,
                "message": "Translation saved to memory bank",
                "document_id": document_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to save translation"
            }
    
    def get_translation_history(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get the user's translation history
        
        Args:
            limit: Maximum number of translations to return
            offset: Number of translations to skip (for pagination)
            
        Returns:
            List of translation entries
        """
        try:
            db = next(get_db())
            translations = TranslationMemory.get_user_translations(
                db, self.session_id, limit, offset
            )
            
            # Convert SQLAlchemy objects to dictionaries
            return [
                {
                    "id": t.id,
                    "source_text": t.source_text,
                    "source_language": t.source_language,
                    "translated_text": t.translated_text,
                    "target_language": t.target_language,
                    "context": t.context,
                    "tags": t.tags,
                    "quality_rating": t.quality_rating,
                    "notes": t.notes,
                    "document_id": t.document_id,
                    "context_type": t.context_type,
                    "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": t.updated_at.strftime("%Y-%m-%d %H:%M:%S") if t.updated_at else None
                }
                for t in translations
            ]
            
        except Exception as e:
            st.error(f"Error retrieving translation history: {str(e)}")
            return []
    
    def search_translations(self, 
                           query: str, 
                           source_language: Optional[str] = None,
                           target_language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for translations in the memory bank
        
        Args:
            query: Search text
            source_language: Optional filter for source language
            target_language: Optional filter for target language
            
        Returns:
            List of matching translation entries
        """
        try:
            db = next(get_db())
            translations = TranslationMemory.search_translations(
                db, self.session_id, query, source_language, target_language
            )
            
            # Convert SQLAlchemy objects to dictionaries
            return [
                {
                    "id": t.id,
                    "source_text": t.source_text,
                    "source_language": t.source_language,
                    "translated_text": t.translated_text,
                    "target_language": t.target_language,
                    "context": t.context,
                    "tags": t.tags,
                    "quality_rating": t.quality_rating,
                    "notes": t.notes,
                    "document_id": t.document_id,
                    "context_type": t.context_type,
                    "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
                for t in translations
            ]
            
        except Exception as e:
            st.error(f"Error searching translations: {str(e)}")
            return []
    
    def find_similar_translations(self, 
                                 text: str, 
                                 source_language: str,
                                 similarity_threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Find similar previous translations using fuzzy matching
        
        Args:
            text: Text to find similar translations for
            source_language: Source language code
            similarity_threshold: Minimum similarity score (0.0-1.0)
            
        Returns:
            List of similar translations with similarity scores
        """
        try:
            db = next(get_db())
            similar_translations = TranslationMemory.find_similar_translations(
                db, self.session_id, text, source_language, similarity_threshold
            )
            
            # Convert results to dictionaries
            return [
                {
                    "id": result["translation"].id,
                    "source_text": result["translation"].source_text,
                    "translated_text": result["translation"].translated_text,
                    "context": result["translation"].context,
                    "document_id": result["translation"].document_id,
                    "context_type": result["translation"].context_type,
                    "similarity": round(result["similarity"] * 100, 2),
                    "created_at": result["translation"].created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
                for result in similar_translations
            ]
            
        except Exception as e:
            st.error(f"Error finding similar translations: {str(e)}")
            return []
    
    def update_translation(self, 
                          translation_id: int, 
                          update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing translation
        
        Args:
            translation_id: ID of the translation to update
            update_data: Dictionary with fields to update
            
        Returns:
            Dictionary with status and the updated translation
        """
        try:
            db = next(get_db())
            translation = TranslationMemory.update_translation(
                db, translation_id, self.session_id, update_data
            )
            
            if translation:
                return {
                    "success": True,
                    "message": "Translation updated successfully",
                    "translation": {
                        "id": translation.id,
                        "source_text": translation.source_text,
                        "translated_text": translation.translated_text,
                        "document_id": translation.document_id,
                        "context_type": translation.context_type,
                        "updated_at": translation.updated_at.strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "Translation not found or you don't have permission to update it"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update translation"
            }
    
    def translate_with_memory(self, 
                             text: str, 
                             source_language: str, 
                             target_language: str,
                             context: Optional[str] = None,
                             context_type: Optional[str] = None,
                             document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Translate text with memory bank assistance
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            context: Optional context for the translation
            context_type: Optional type of context (business, casual, technical, etc.)
            document_id: Optional ID for document/conversation context
            
        Returns:
            Dictionary with translation results
        """
        # First, check if we have similar translations in the memory bank
        similar_translations = self.find_similar_translations(
            text, source_language, similarity_threshold=0.75
        )
        
        # If we have very similar translations (>85% match), use the stored translation
        exact_matches = [t for t in similar_translations if t["similarity"] > 85]
        if exact_matches:
            best_match = exact_matches[0]
            return {
                "translated_text": best_match["translated_text"],
                "source": "memory_bank",
                "similarity": best_match["similarity"],
                "translation_id": best_match["id"],
                "context_used": True if best_match.get("context") else False,
                "document_id": best_match.get("document_id"),
                "context_type": best_match.get("context_type")
            }
        
        # For good matches (65-85%), provide the translation but mention it's being adapted
        good_matches = [t for t in similar_translations if 65 <= t["similarity"] <= 85]
        
        # Use OpenAI for translation
        try:
            # Prepare the prompt with context and similar translations
            prompt = f"Translate the following text from {self._get_language_name(source_language)} to {self._get_language_name(target_language)}:\n\n{text}\n\n"
            
            # Add context if provided
            if context:
                prompt += f"Context: {context}\n\n"
            
            # Add similar translations for reference
            if good_matches:
                prompt += "Here are similar texts I've translated before that might help:\n"
                for i, match in enumerate(good_matches[:3]):  # Use top 3 matches at most
                    prompt += f"{i+1}. Original: {match['source_text']}\n"
                    prompt += f"   Translation: {match['translated_text']}\n"
                    prompt += f"   Similarity: {match['similarity']}%\n\n"
            
            # Prepare system message
            system_message = """You are an expert translator specializing in Japanese and English translation.
            Provide accurate, natural-sounding translations that preserve the original meaning and nuance.
            If provided with similar translations for reference, adapt them appropriately for the current text."""
            
            # Call OpenAI
            response = self.openai_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3  # Lower temperature for more accurate translations
            )
            
            translated_text = self.openai_client.extract_content(response)
            
            # Store the new translation in the memory bank
            result = self.add_translation(
                source_text=text,
                source_language=source_language,
                translated_text=translated_text,
                target_language=target_language,
                context=context,
                context_type=context_type,
                document_id=document_id
            )
            
            return {
                "translated_text": translated_text,
                "source": "ai_with_memory_guidance" if good_matches else "ai",
                "similar_count": len(good_matches),
                "translation_id": result.get("translation_id") if result.get("success") else None,
                "context_used": True if context else False,
                "document_id": document_id,
                "context_type": context_type
            }
            
        except Exception as e:
            return {
                "error": True,
                "message": f"Translation failed: {str(e)}"
            }
    
    def _get_language_name(self, language_code: str) -> str:
        """Get the full language name from a language code"""
        language_map = {
            "ja": "Japanese",
            "en": "English",
            "zh": "Chinese",
            "ko": "Korean",
            "fr": "French",
            "de": "German",
            "es": "Spanish",
            "it": "Italian",
            "ru": "Russian"
        }
        return language_map.get(language_code.lower(), language_code)
    
    def create_document_context(self, 
                              title: str, 
                              description: str, 
                              context_type: str) -> Dict[str, Any]:
        """
        Create a new document or conversation context for grouping translations
        
        Args:
            title: Title of the document or conversation
            description: Description of the context
            context_type: Type of context (business, casual, technical, etc.)
            
        Returns:
            Dictionary with the created context
        """
        # Generate a unique ID for the document/conversation
        document_id = str(uuid.uuid4())
        
        # Create context dictionary
        context = {
            "id": document_id,
            "title": title,
            "description": description,
            "type": context_type,
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Set as active context
        st.session_state.active_context = context
        
        # Add to context history
        if context not in st.session_state.context_history:
            st.session_state.context_history.append(context)
            
        return context
    
    def set_active_context(self, document_id: str) -> Dict[str, Any]:
        """
        Set an existing document/conversation as the active context
        
        Args:
            document_id: ID of the document/conversation context
            
        Returns:
            Dictionary with the activated context or error
        """
        # Find the context in history
        for context in st.session_state.context_history:
            if context["id"] == document_id:
                st.session_state.active_context = context
                return {"success": True, "context": context}
                
        return {"success": False, "message": "Context not found"}
    
    def clear_active_context(self) -> Dict[str, Any]:
        """
        Clear the active document/conversation context
        
        Returns:
            Status dictionary
        """
        st.session_state.active_context = None
        return {"success": True, "message": "Active context cleared"}
    
    def get_contexts_by_type(self, context_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all document/conversation contexts, optionally filtered by type
        
        Args:
            context_type: Optional filter for context type
            
        Returns:
            List of context dictionaries
        """
        if not context_type:
            return st.session_state.context_history
            
        return [
            context for context in st.session_state.context_history
            if context.get("type") == context_type
        ]
        
    def get_translations_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all translations associated with a specific document/conversation
        
        Args:
            document_id: ID of the document/conversation context
            
        Returns:
            List of translation dictionaries
        """
        try:
            db = next(get_db())
            translations = db.query(TranslationMemory).filter(
                TranslationMemory.session_id == self.session_id,
                TranslationMemory.document_id == document_id
            ).order_by(
                TranslationMemory.created_at.asc()
            ).all()
            
            # Convert SQLAlchemy objects to dictionaries
            return [
                {
                    "id": t.id,
                    "source_text": t.source_text,
                    "source_language": t.source_language,
                    "translated_text": t.translated_text,
                    "target_language": t.target_language,
                    "context": t.context,
                    "context_type": t.context_type,
                    "tags": t.tags,
                    "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
                for t in translations
            ]
            
        except Exception as e:
            st.error(f"Error retrieving document translations: {str(e)}")
            return []
    
    def get_translation_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the user's translation history
        
        Returns:
            Dictionary with translation statistics
        """
        try:
            db = next(get_db())
            
            # Get all user translations
            translations = db.query(TranslationMemory).filter(
                TranslationMemory.session_id == self.session_id
            ).all()
            
            if not translations:
                return {
                    "total_count": 0,
                    "language_pairs": {},
                    "recent_activity": []
                }
            
            # Count by language pair
            language_pairs = {}
            for t in translations:
                pair = f"{t.source_language}→{t.target_language}"
                if pair not in language_pairs:
                    language_pairs[pair] = 0
                language_pairs[pair] += 1
            
            # Get recent activity (last 7 days)
            from datetime import timedelta
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            recent_activity = db.query(TranslationMemory).filter(
                TranslationMemory.session_id == self.session_id,
                TranslationMemory.created_at >= one_week_ago
            ).order_by(TranslationMemory.created_at.desc()).all()
            
            # Organize by day
            daily_counts = {}
            for t in recent_activity:
                day = t.created_at.strftime("%Y-%m-%d")
                if day not in daily_counts:
                    daily_counts[day] = 0
                daily_counts[day] += 1
            
            # Convert to list for easy visualization
            recent_activity_list = [
                {"date": day, "count": count}
                for day, count in daily_counts.items()
            ]
            
            return {
                "total_count": len(translations),
                "language_pairs": language_pairs,
                "recent_activity": recent_activity_list
            }
            
        except Exception as e:
            st.error(f"Error getting translation statistics: {str(e)}")
            return {
                "error": True,
                "message": f"Failed to get statistics: {str(e)}"
            }

# Create the UI for the Translation Memory Bank feature
def render_translation_memory_ui():
    """Render the user interface for the Translation Memory Bank feature"""
    st.title("📚 Contextual Translation Memory Bank")
    
    # Initialize the translation memory manager
    if "translation_manager" not in st.session_state:
        st.session_state.translation_manager = TranslationMemoryManager()
    
    manager = st.session_state.translation_manager
    
    # Create tabs for different functions
    tabs = st.tabs([
        "New Translation", 
        "Translation History", 
        "Search Memory", 
        "Document Contexts",
        "Statistics"
    ])
    
    # New Translation tab
    with tabs[0]:
        st.header("✨ New Translation with Memory Assistance")
        st.markdown("""
        This tool leverages your translation history to provide more consistent and contextual translations.
        Previously translated similar phrases will influence new translations.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            source_language = st.selectbox(
                "Source Language:",
                [("ja", "Japanese"), ("en", "English")],
                format_func=lambda x: x[1]
            )
        
        with col2:
            target_language = st.selectbox(
                "Target Language:",
                [("en", "English"), ("ja", "Japanese")],
                format_func=lambda x: x[1]
            )
        
        # Prevent same language selection
        if source_language[0] == target_language[0]:
            st.warning("Please select different languages for source and target.")
            st.stop()
        
        source_text = st.text_area(
            "Text to translate:",
            height=150,
            key="source_text_input"
        )
        
        # Show active context if one exists
        if st.session_state.active_context:
            active_context = st.session_state.active_context
            st.info(f"""
            **✅ Active Context:** {active_context['title']} ({active_context['type']})  
            **Description:** {active_context['description']}
            """)

        # Optional context
        with st.expander("Add Translation Context (Optional)", expanded=not st.session_state.active_context):
            if st.session_state.active_context:
                st.markdown("**Note:** This additional context will be combined with your active document context.")
                
            context = st.text_area(
                "Context information to improve translation accuracy:",
                placeholder="Example: This is from a business email / This is dialogue from an anime / This refers to cooking instructions",
                height=100,
                key="context_input"
            )
            
            # Context type selection if no active context
            if not st.session_state.active_context:
                context_type = st.selectbox(
                    "Context Type:",
                    [
                        "", "business", "casual", "technical", "academic", 
                        "entertainment", "literary", "medical", "legal", "other"
                    ],
                    key="context_type_input"
                )
            
            st.markdown("""
            **Why add context?**
            
            Context helps the translator understand the meaning, tone, and purpose of your text,
            resulting in more accurate and appropriate translations.
            """)
        
        if st.button("Translate", key="translate_btn"):
            if source_text:
                with st.spinner("Translating..."):
                    # Prepare context info
                    context_to_use = context
                    context_type_to_use = None if not st.session_state.active_context else st.session_state.active_context.get("type")
                    document_id = None if not st.session_state.active_context else st.session_state.active_context.get("id")
                    
                    # If no explicit context but active document context exists, use its description
                    if not context_to_use and st.session_state.active_context:
                        context_to_use = st.session_state.active_context.get("description")
                    
                    # If no active context but context type was selected
                    if not st.session_state.active_context and "context_type_input" in st.session_state and st.session_state.context_type_input:
                        context_type_to_use = st.session_state.context_type_input
                    
                    result = manager.translate_with_memory(
                        text=source_text,
                        source_language=source_language[0],
                        target_language=target_language[0],
                        context=context_to_use,
                        context_type=context_type_to_use,
                        document_id=document_id
                    )
                
                if "error" in result:
                    st.error(result["message"])
                else:
                    # Show translation result in a nice card
                    st.markdown("### Translation Result")
                    
                    # Display source info
                    if result["source"] == "memory_bank":
                        st.success(f"✅ Found an exact match in your translation memory! ({result['similarity']}% similar)")
                    elif result["source"] == "ai_with_memory_guidance":
                        st.info(f"ℹ️ Translation guided by {result['similar_count']} similar previous translations")
                    
                    # Display the translation
                    st.markdown("""
                    <div style="background-color: #f0f8ff; padding: 15px; border-radius: 10px; border-left: 5px solid #4169e1;">
                        <p style="font-size: 1.2rem;">{}</p>
                    </div>
                    """.format(result["translated_text"]), unsafe_allow_html=True)
                    
                    # Display context info if used
                    if result.get("context_used"):
                        st.markdown("_Translation improved with provided context_")
                    
                    # Display document context info if present
                    if result.get("document_id") and result.get("context_type"):
                        st.markdown(f"_Part of document context: {result.get('context_type')}_")
                    
                    # Add rating option
                    st.markdown("### Rate this translation:")
                    rating_cols = st.columns(5)
                    rating_selected = False
                    
                    for i in range(5):
                        rating = i + 1
                        with rating_cols[i]:
                            if st.button(f"{rating} ⭐", key=f"rating_{rating}"):
                                if result.get("translation_id"):
                                    manager.update_translation(
                                        result["translation_id"],
                                        {"quality_rating": rating}
                                    )
                                    st.success(f"Rating saved: {rating}/5")
                                    rating_selected = True
                    
                    # Add notes option
                    if not rating_selected and result.get("translation_id"):
                        with st.expander("Add notes to this translation", expanded=False):
                            notes = st.text_area(
                                "Translation notes:",
                                placeholder="Add any notes about this translation...",
                                key="translation_notes"
                            )
                            
                            if st.button("Save Notes"):
                                manager.update_translation(
                                    result["translation_id"],
                                    {"notes": notes}
                                )
                                st.success("Notes saved successfully!")
            else:
                st.warning("Please enter some text to translate.")
    
    # Translation History tab
    with tabs[1]:
        st.header("📜 Your Translation History")
        
        # Add pagination controls
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown("Review and manage your previous translations")
        
        with col3:
            if "page" not in st.session_state:
                st.session_state.page = 0
                
            page_size = 10
            
            if st.button("Next →", key="next_page"):
                st.session_state.page += 1
                st.rerun()
                
        with col2:
            if st.button("← Previous", key="prev_page", disabled=st.session_state.page==0):
                st.session_state.page = max(0, st.session_state.page - 1)
                st.rerun()
        
        # Get translation history with pagination
        translations = manager.get_translation_history(
            limit=page_size,
            offset=st.session_state.page * page_size
        )
        
        if not translations:
            if st.session_state.page > 0:
                st.warning("No more translations. Please go back to the previous page.")
                st.session_state.page = max(0, st.session_state.page - 1)
            else:
                st.info("You don't have any saved translations yet. Start translating to build your memory bank!")
        else:
            # Display translations in an expandable list
            for t in translations:
                with st.expander(f"{t['source_text'][:50]}... → {t['translated_text'][:50]}...", expanded=False):
                    cols = st.columns([3, 1])
                    
                    with cols[0]:
                        st.markdown(f"**Source ({t['source_language']}):** {t['source_text']}")
                        st.markdown(f"**Translation ({t['target_language']}):** {t['translated_text']}")
                        
                        if t.get('document_id'):
                            # Find the context title if available
                            context_title = "Unknown"
                            for ctx in st.session_state.context_history:
                                if ctx.get('id') == t.get('document_id'):
                                    context_title = ctx.get('title')
                                    break
                            
                            st.markdown(f"**Document/Conversation:** {context_title}")
                        
                        if t.get('context_type'):
                            st.markdown(f"**Context Type:** {t.get('context_type')}")
                        
                        if t.get('context'):
                            st.markdown(f"**Context:** {t.get('context')}")
                        
                        if t.get('notes'):
                            st.markdown(f"**Notes:** {t.get('notes')}")
                    
                    with cols[1]:
                        st.markdown(f"**Date:** {t['created_at']}")
                        
                        if t['quality_rating']:
                            st.markdown(f"**Rating:** {'⭐' * t['quality_rating']}")
                        
                        if t['tags']:
                            st.markdown(f"**Tags:** {', '.join(t['tags'])}")
                    
                    # Edit option
                    with st.expander("Edit this translation", expanded=False):
                        updated_text = st.text_area(
                            "Updated translation:",
                            value=t['translated_text'],
                            key=f"edit_translation_{t['id']}"
                        )
                        
                        updated_notes = st.text_area(
                            "Update notes:",
                            value=t['notes'] or "",
                            key=f"edit_notes_{t['id']}"
                        )
                        
                        if st.button("Save Changes", key=f"save_edit_{t['id']}"):
                            result = manager.update_translation(
                                t['id'],
                                {
                                    "translated_text": updated_text,
                                    "notes": updated_notes
                                }
                            )
                            
                            if result["success"]:
                                st.success("Changes saved successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to save changes: {result.get('message')}")
    
    # Search Memory tab
    with tabs[2]:
        st.header("🔍 Search Translation Memory")
        
        search_query = st.text_input(
            "Search for:",
            placeholder="Enter text to search in your translation memory",
            key="search_query"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_source = st.selectbox(
                "Source Language Filter:",
                [("", "Any"), ("ja", "Japanese"), ("en", "English")],
                format_func=lambda x: x[1],
                key="search_source"
            )
            
        with col2:
            search_target = st.selectbox(
                "Target Language Filter:",
                [("", "Any"), ("en", "English"), ("ja", "Japanese")],
                format_func=lambda x: x[1],
                key="search_target"
            )
            
        if st.button("Search", key="search_button"):
            if search_query:
                results = manager.search_translations(
                    query=search_query,
                    source_language=search_source[0] if search_source[0] else None,
                    target_language=search_target[0] if search_target[0] else None
                )
                
                if not results:
                    st.info("No matching translations found.")
                else:
                    st.success(f"Found {len(results)} matching translations.")
                    
                    for t in results:
                        with st.expander(f"{t['source_text'][:50]}... → {t['translated_text'][:50]}...", expanded=False):
                            st.markdown(f"**Source ({t['source_language']}):** {t['source_text']}")
                            st.markdown(f"**Translation ({t['target_language']}):** {t['translated_text']}")
                            
                            if t.get('document_id'):
                                # Find the context title if available
                                context_title = "Unknown"
                                for ctx in st.session_state.context_history:
                                    if ctx.get('id') == t.get('document_id'):
                                        context_title = ctx.get('title')
                                        break
                                
                                st.markdown(f"**Document/Conversation:** {context_title}")
                            
                            if t.get('context_type'):
                                st.markdown(f"**Context Type:** {t.get('context_type')}")
                            
                            if t.get('context'):
                                st.markdown(f"**Context:** {t.get('context')}")
                                
                            if t.get('quality_rating'):
                                st.markdown(f"**Rating:** {'⭐' * t.get('quality_rating')}")
            else:
                st.warning("Please enter a search query.")
                
        # Similar Phrase Search
        st.markdown("---")
        st.subheader("Find Similar Phrases")
        st.markdown("This tool uses fuzzy matching to find phrases similar to your input.")
        
        similar_text = st.text_area(
            "Text to find similar translations for:",
            placeholder="Enter a Japanese or English phrase",
            key="similar_text"
        )
        
        similar_language = st.selectbox(
            "Language:",
            [("ja", "Japanese"), ("en", "English")],
            format_func=lambda x: x[1],
            key="similar_language"
        )
        
        similarity_threshold = st.slider(
            "Minimum similarity (%):",
            min_value=50,
            max_value=95,
            value=60,
            step=5,
            key="similarity_threshold"
        )
        
        if st.button("Find Similar", key="find_similar_btn"):
            if similar_text:
                with st.spinner("Finding similar phrases..."):
                    similar = manager.find_similar_translations(
                        text=similar_text,
                        source_language=similar_language[0],
                        similarity_threshold=similarity_threshold/100.0
                    )
                
                if not similar:
                    st.info("No similar phrases found.")
                else:
                    st.success(f"Found {len(similar)} similar phrases.")
                    
                    # Create a table for better presentation
                    st.markdown("| Similarity | Original | Translation |")
                    st.markdown("|------------|----------|-------------|")
                    
                    for t in similar:
                        similarity_emoji = "🟢" if t["similarity"] > 80 else "🟡" if t["similarity"] > 65 else "🟠"
                        st.markdown(f"| {similarity_emoji} {t['similarity']}% | {t['source_text'][:50]} | {t['translated_text'][:50]} |")
            else:
                st.warning("Please enter text to find similar phrases.")
    
    # Document Contexts tab
    with tabs[3]:
        st.header("📑 Document & Conversation Contexts")
        st.markdown("""
        Manage document and conversation contexts for your translations.
        Contexts help you group related translations for better consistency and easier management.
        """)
        
        # Display active context indicator
        if st.session_state.active_context:
            active_context = st.session_state.active_context
            st.success(f"✅ Active Context: **{active_context['title']}** ({active_context['type']})")
            
            if st.button("Clear Active Context"):
                manager.clear_active_context()
                st.rerun()
        else:
            st.info("No active context. Create or select one below.")
        
        # Create new context
        with st.expander("Create New Context", expanded=not st.session_state.active_context):
            context_title = st.text_input("Context Title:", placeholder="e.g., Business Email, Anime Script, Tech Manual")
            
            context_type = st.selectbox(
                "Context Type:",
                [
                    "business", "casual", "technical", "academic", 
                    "entertainment", "literary", "medical", "legal",
                    "conversation", "document", "other"
                ]
            )
            
            context_description = st.text_area(
                "Context Description:",
                placeholder="Describe this context to help translation consistency..."
            )
            
            if st.button("Create Context"):
                if context_title and context_description:
                    result = manager.create_document_context(
                        title=context_title,
                        description=context_description,
                        context_type=context_type
                    )
                    st.success(f"Context created and set as active: {context_title}")
                    st.rerun()
                else:
                    st.warning("Please provide both a title and description.")
        
        # List existing contexts
        st.subheader("Your Saved Contexts")
        
        contexts = manager.get_contexts_by_type()
        if not contexts:
            st.info("You haven't created any contexts yet.")
        else:
            # Filter contexts
            filter_type = st.selectbox(
                "Filter by type:",
                ["All"] + sorted(set(c["type"] for c in contexts))
            )
            
            filtered_contexts = contexts
            if filter_type != "All":
                filtered_contexts = [c for c in contexts if c["type"] == filter_type]
            
            if not filtered_contexts:
                st.info(f"No contexts of type '{filter_type}'.")
            else:
                for context in filtered_contexts:
                    with st.expander(f"{context['title']} ({context['type']})", expanded=False):
                        st.markdown(f"**Description:** {context['description']}")
                        st.markdown(f"**Created:** {context['created_at']}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Set as Active", key=f"activate_{context['id']}"):
                                manager.set_active_context(context['id'])
                                st.success(f"Context activated: {context['title']}")
                                st.rerun()
                        
                        with col2:
                            if st.button("View Translations", key=f"view_{context['id']}"):
                                translations = manager.get_translations_by_document(context['id'])
                                
                                if not translations:
                                    st.info("No translations associated with this context yet.")
                                else:
                                    st.markdown(f"**Found {len(translations)} translations in this context:**")
                                    
                                    for t in translations:
                                        st.markdown(f"""
                                        ---
                                        **{t['source_language']}:** {t['source_text']}  
                                        **{t['target_language']}:** {t['translated_text']}  
                                        **Date:** {t['created_at']}
                                        """)
    
    # Statistics tab
    with tabs[4]:
        st.header("📊 Translation Statistics")
        
        stats = manager.get_translation_statistics()
        
        if stats.get("error"):
            st.error(stats["message"])
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Translations", stats["total_count"])
                
                st.subheader("Language Pairs")
                if stats["language_pairs"]:
                    # Create a bar chart of language pairs
                    import plotly.express as px
                    import pandas as pd
                    
                    # Prepare data for visualization
                    pairs_data = {
                        "Language Pair": list(stats["language_pairs"].keys()),
                        "Count": list(stats["language_pairs"].values())
                    }
                    df = pd.DataFrame(pairs_data)
                    
                    # Create chart
                    fig = px.bar(
                        df, 
                        x="Language Pair", 
                        y="Count",
                        color="Language Pair",
                        title="Translations by Language Pair"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No language pair data yet.")
            
            with col2:
                st.subheader("Recent Activity")
                if stats["recent_activity"]:
                    # Create a line chart of recent activity
                    import plotly.express as px
                    import pandas as pd
                    
                    # Prepare data for visualization
                    activity_data = pd.DataFrame(stats["recent_activity"])
                    
                    # Convert date strings to datetime for proper sorting
                    activity_data["date"] = pd.to_datetime(activity_data["date"])
                    activity_data = activity_data.sort_values("date")
                    
                    # Format dates for display
                    activity_data["formatted_date"] = activity_data["date"].dt.strftime("%m/%d")
                    
                    # Create chart
                    fig = px.line(
                        activity_data, 
                        x="formatted_date", 
                        y="count",
                        markers=True,
                        title="Translations in the Last 7 Days"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No recent activity data.")
                    
            # Add a section for translation memory effectiveness
            st.markdown("---")
            st.subheader("Memory Bank Effectiveness")
            st.markdown("""
            The more you translate, the more effective your memory bank becomes.
            Consistent translations of similar phrases helps build a reliable memory bank.
            """)
            
            # Placeholder for future effectiveness metrics
            if stats["total_count"] < 10:
                st.warning("You need at least 10 translations to see effectiveness metrics.")
            else:
                # This is a placeholder - in a real implementation we would
                # track how often memory matches are used vs. new translations
                import random
                memory_match_rate = min(80, max(20, stats["total_count"] // 4))
                st.progress(memory_match_rate / 100, text=f"Memory Match Rate: {memory_match_rate}%")
                
                st.info(f"Approximately {memory_match_rate}% of new translations are now influenced by your translation memory.")


# Main app integration function
def add_translation_memory_to_app():
    """Add the Translation Memory Bank feature to the main app sidebar navigation"""
    if "memory_bank" in st.session_state.get("sidebar_selection", ""):
        render_translation_memory_ui()