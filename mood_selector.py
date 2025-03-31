import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from visualizations import create_mood_trend_chart, create_difficulty_distribution_chart

class MoodDifficultySelector:
    """
    A class to handle emoji-based mood and difficulty selection for Japanese lessons.
    Tracks user mood over time and adjusts content difficulty based on selections.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize the mood/difficulty selector with a given session ID"""
        self.session_id = session_id if session_id else st.session_state.get('session_id', 'default_user')
        self.mood_history_file = f"mood_history_{self.session_id}.json"
        self.difficulty_history_file = f"difficulty_history_{self.session_id}.json"
        
        # Initialize storage for tracking mood and difficulty
        self._init_tracking_storage()
    
    def _init_tracking_storage(self) -> None:
        """Initialize the storage for tracking mood and difficulty selections"""
        # Initialize mood history
        if not os.path.exists(self.mood_history_file):
            with open(self.mood_history_file, 'w') as f:
                json.dump([], f)
        
        # Initialize difficulty history  
        if not os.path.exists(self.difficulty_history_file):
            with open(self.difficulty_history_file, 'w') as f:
                json.dump([], f)
    
    def _save_mood_history(self) -> None:
        """Save the mood history to a file"""
        try:
            with open(self.mood_history_file, 'r') as f:
                history = json.load(f)
                
            with open(self.mood_history_file, 'w') as f:
                json.dump(history, f)
                
        except Exception as e:
            st.error(f"Error saving mood history: {str(e)}")
    
    def _save_difficulty_history(self) -> None:
        """Save the difficulty history to a file"""
        try:
            with open(self.difficulty_history_file, 'r') as f:
                history = json.load(f)
                
            with open(self.difficulty_history_file, 'w') as f:
                json.dump(history, f)
                
        except Exception as e:
            st.error(f"Error saving difficulty history: {str(e)}")
    
    def display_mood_selector(self) -> str:
        """
        Display an emoji-based mood selector and return the selected mood
        
        Returns:
            The selected mood emoji
        """
        # Define mood options with emojis
        mood_options = {
            "😊": "Happy - I'm feeling great and ready to learn!",
            "😀": "Satisfied - I'm doing well and focused.",
            "😐": "Neutral - I'm neither particularly happy nor upset.",
            "😕": "Slightly Frustrated - I'm having some difficulty but still motivated.",
            "😞": "Frustrated - I'm finding today's content challenging."
        }
        
        # Create a horizontal layout for the mood buttons
        cols = st.columns(len(mood_options))
        
        selected_mood = None
        
        # Display mood buttons
        for i, (emoji, description) in enumerate(mood_options.items()):
            with cols[i]:
                if st.button(emoji, key=f"mood_{emoji}", help=description):
                    selected_mood = emoji
                    st.session_state.selected_mood = emoji
                    self._record_mood_selection(emoji)
                    
                st.caption(description.split(" - ")[0])
        
        # Get stored mood if one was already selected
        if not selected_mood and "selected_mood" in st.session_state:
            selected_mood = st.session_state.selected_mood
            
        # Show the selected mood
        if selected_mood:
            st.success(f"You selected: {selected_mood} - {mood_options[selected_mood]}")
        
        return selected_mood
    
    def _record_mood_selection(self, mood_emoji: str) -> None:
        """Record the selected mood in the user's history"""
        try:
            with open(self.mood_history_file, 'r') as f:
                history = json.load(f)
            
            # Add new mood entry
            history.append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M'),
                'mood': mood_emoji
            })
            
            # Save updated history
            with open(self.mood_history_file, 'w') as f:
                json.dump(history, f)
                
        except Exception as e:
            st.error(f"Error recording mood: {str(e)}")
    
    def display_difficulty_selector(self) -> str:
        """
        Display an emoji-based difficulty level selector and return the selected level
        
        Returns:
            The selected difficulty emoji
        """
        # Define difficulty options with emojis
        difficulty_options = {
            "🌱": "Beginner - I'm just starting out with Japanese.",
            "🌿": "Elementary - I know basic greetings and simple sentences.",
            "🌲": "Intermediate - I can have everyday conversations.",
            "🏔️": "Advanced - I can discuss complex topics fluidly.",
            "🏯": "Native-like - I have mastery of the language."
        }
        
        # Create a horizontal layout for the difficulty buttons
        cols = st.columns(len(difficulty_options))
        
        selected_difficulty = None
        
        # Display difficulty buttons
        for i, (emoji, description) in enumerate(difficulty_options.items()):
            with cols[i]:
                if st.button(emoji, key=f"diff_{emoji}", help=description):
                    selected_difficulty = emoji
                    st.session_state.selected_difficulty = emoji
                    self._record_difficulty_selection(emoji)
                    
                st.caption(description.split(" - ")[0])
        
        # Get stored difficulty if one was already selected
        if not selected_difficulty and "selected_difficulty" in st.session_state:
            selected_difficulty = st.session_state.selected_difficulty
            
        # Show the selected difficulty
        if selected_difficulty:
            st.success(f"You selected: {selected_difficulty} - {difficulty_options[selected_difficulty]}")
            
        return selected_difficulty
    
    def _record_difficulty_selection(self, difficulty_emoji: str) -> None:
        """Record the selected difficulty in the user's history"""
        try:
            with open(self.difficulty_history_file, 'r') as f:
                history = json.load(f)
            
            # Add new difficulty entry
            history.append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M'),
                'difficulty': difficulty_emoji
            })
            
            # Save updated history
            with open(self.difficulty_history_file, 'w') as f:
                json.dump(history, f)
                
        except Exception as e:
            st.error(f"Error recording difficulty: {str(e)}")
    
    def get_recommended_difficulty(self) -> str:
        """
        Get a recommended difficulty level based on the user's mood history
        
        Returns:
            The recommended difficulty emoji
        """
        try:
            # Load mood history
            with open(self.mood_history_file, 'r') as f:
                mood_history = json.load(f)
            
            # If we don't have enough data, return default intermediate difficulty
            if len(mood_history) < 3:
                return "🌲"  # Default to intermediate
            
            # Calculate average mood from recent entries (last 3)
            recent_moods = mood_history[-3:]
            
            # Convert emojis to numerical values
            mood_values = {
                "😊": 5,  # Happy
                "😀": 4,  # Satisfied
                "😐": 3,  # Neutral
                "😕": 2,  # Slightly Frustrated
                "😞": 1   # Frustrated
            }
            
            # Calculate average mood
            total = 0
            count = 0
            
            for entry in recent_moods:
                if 'mood' in entry and entry['mood'] in mood_values:
                    total += mood_values[entry['mood']]
                    count += 1
            
            if count == 0:
                return "🌲"  # Default to intermediate
                
            avg_mood = total / count
            
            # Map average mood to recommended difficulty
            if avg_mood >= 4.5:  # Very happy
                return "🏔️"  # Advanced (challenge them when they're feeling great)
            elif avg_mood >= 3.5:  # Happy
                return "🌲"  # Intermediate
            elif avg_mood >= 2.5:  # Neutral
                return "🌿"  # Elementary
            else:  # Frustrated
                return "🌱"  # Beginner (easier content when struggling)
                
        except Exception as e:
            st.error(f"Error getting recommended difficulty: {str(e)}")
            return "🌲"  # Default to intermediate
    
    def get_mood_trends(self) -> Dict:
        """
        Analyze mood trends over time
        
        Returns:
            Dictionary with mood trend analysis
        """
        try:
            # Load mood history
            with open(self.mood_history_file, 'r') as f:
                mood_history = json.load(f)
            
            # If we don't have enough data, return empty analysis
            if len(mood_history) < 2:
                return {
                    "trend": "insufficient_data",
                    "message": "Not enough mood data collected yet. Please continue using the app to get personalized insights."
                }
            
            # Convert emojis to numerical values
            mood_values = {
                "😊": 5,  # Happy
                "😀": 4,  # Satisfied
                "😐": 3,  # Neutral
                "😕": 2,  # Slightly Frustrated
                "😞": 1   # Frustrated
            }
            
            # Get recent moods
            recent_moods = mood_history[-min(5, len(mood_history)):]
            mood_scores = []
            
            for entry in recent_moods:
                if 'mood' in entry and entry['mood'] in mood_values:
                    mood_scores.append(mood_values[entry['mood']])
            
            if len(mood_scores) < 2:
                return {
                    "trend": "insufficient_data",
                    "message": "Not enough mood data collected yet. Please continue using the app to get personalized insights."
                }
                
            # Calculate trend
            start_avg = sum(mood_scores[:2]) / 2
            end_avg = sum(mood_scores[-2:]) / 2
            
            trend_diff = end_avg - start_avg
            
            if trend_diff > 0.5:
                trend = "improving"
                message = "Your mood appears to be improving! Keep up the good work."
            elif trend_diff < -0.5:
                trend = "declining"
                message = "Your mood seems to be declining. Consider taking on easier lessons or taking a short break."
            else:
                trend = "stable"
                message = "Your mood has been relatively stable. That's a good sign of consistent engagement."
            
            # Calculate most common mood
            mood_counts = {}
            for score in mood_scores:
                mood_counts[score] = mood_counts.get(score, 0) + 1
            
            most_common_score = max(mood_counts.items(), key=lambda x: x[1])[0]
            most_common_mood = {v: k for k, v in mood_values.items()}[most_common_score]
            
            return {
                "trend": trend,
                "message": message,
                "most_common_mood": most_common_mood,
                "mood_history": mood_history,
                "chart": create_mood_trend_chart(mood_history)
            }
            
        except Exception as e:
            st.error(f"Error analyzing mood trends: {str(e)}")
            return {
                "trend": "error",
                "message": f"Error analyzing mood trends: {str(e)}"
            }
    
    def adjust_content_for_mood_difficulty(
        self, 
        content_options: Dict[str, List[Dict]], 
        mood_emoji: Optional[str] = None, 
        difficulty_emoji: Optional[str] = None
    ) -> List[Dict]:
        """
        Adjust lesson content based on mood and difficulty selections
        
        Args:
            content_options: Dictionary of content options categorized by difficulty
            mood_emoji: Selected mood emoji (or None to use last recorded)
            difficulty_emoji: Selected difficulty emoji (or None to use recommended)
            
        Returns:
            Filtered and adjusted content list
        """
        # If no mood provided, use last recorded mood
        if not mood_emoji:
            try:
                with open(self.mood_history_file, 'r') as f:
                    mood_history = json.load(f)
                
                if mood_history:
                    mood_emoji = mood_history[-1].get('mood', "😐")  # Default to neutral
                else:
                    mood_emoji = "😐"  # Default to neutral
            except:
                mood_emoji = "😐"  # Default to neutral
        
        # If no difficulty provided, use recommended difficulty
        if not difficulty_emoji:
            difficulty_emoji = self.get_recommended_difficulty()
        
        # Map difficulty emojis to difficulty levels in content
        difficulty_map = {
            "🌱": "Beginner",
            "🌿": "Elementary", 
            "🌲": "Intermediate", 
            "🏔️": "Advanced", 
            "🏯": "Native-like"
        }
        
        # Map moods to content preferences
        mood_preferences = {
            "😊": {"engaging": 0.8, "challenging": 0.7, "visual": 0.6},
            "😀": {"engaging": 0.7, "structured": 0.6, "interactive": 0.7},
            "😐": {"structured": 0.8, "concise": 0.7, "practical": 0.6},
            "😕": {"concise": 0.9, "supportive": 0.8, "visual": 0.7},
            "😞": {"supportive": 0.9, "structured": 0.8, "practical": 0.8}
        }
        
        # Get content for selected difficulty
        selected_difficulty = difficulty_map.get(difficulty_emoji, "Intermediate")
        filtered_content = content_options.get(selected_difficulty, [])
        
        # If we have no content for the selected difficulty, use the closest available
        if not filtered_content:
            difficulty_levels = list(difficulty_map.values())
            selected_index = difficulty_levels.index(selected_difficulty) if selected_difficulty in difficulty_levels else 2
            
            # Try adjacent difficulty levels
            for offset in [1, -1, 2, -2]:
                try_index = selected_index + offset
                if 0 <= try_index < len(difficulty_levels):
                    try_difficulty = difficulty_levels[try_index]
                    if try_difficulty in content_options and content_options[try_difficulty]:
                        filtered_content = content_options[try_difficulty]
                        break
            
            # If still no content, use any available content
            if not filtered_content:
                for difficulty, content in content_options.items():
                    if content:
                        filtered_content = content
                        break
        
        # No content available at all
        if not filtered_content:
            return []
        
        # Get mood preferences
        prefs = mood_preferences.get(mood_emoji, mood_preferences["😐"])
        
        # Score and sort content based on mood preferences
        scored_content = []
        for item in filtered_content:
            score = 0
            for attr, weight in prefs.items():
                if item.get('attributes', {}).get(attr, False):
                    score += weight
            
            scored_content.append((score, item))
        
        # Sort by score (descending)
        scored_content.sort(reverse=True, key=lambda x: x[0])
        
        # Return the sorted content items
        return [item for _, item in scored_content]
    
    def display_mood_analysis(self) -> None:
        """Display an analysis of the user's mood history"""
        st.subheader("Your Mood Analysis")
        
        # Get mood trends
        mood_data = self.get_mood_trends()
        
        if mood_data.get("trend") == "insufficient_data":
            st.info(mood_data.get("message", "Not enough data collected yet."))
            return
        
        # Display mood trend message
        trend = mood_data.get("trend", "stable")
        message = mood_data.get("message", "")
        
        if trend == "improving":
            st.success(message)
        elif trend == "declining":
            st.warning(message)
        else:
            st.info(message)
        
        # Display mood chart if available
        if "chart" in mood_data and mood_data["chart"]:
            st.plotly_chart(mood_data["chart"], use_container_width=True)
        
        # Get difficulty history
        try:
            with open(self.difficulty_history_file, 'r') as f:
                difficulty_history = json.load(f)
            
            # Display difficulty distribution chart if we have enough data
            if len(difficulty_history) >= 2:
                diff_chart = create_difficulty_distribution_chart(difficulty_history)
                if diff_chart:
                    st.plotly_chart(diff_chart, use_container_width=True)
        except:
            pass
        
        # Display personalized tips based on mood trends
        with st.expander("💡 Personalized Learning Tips"):
            if trend == "improving":
                st.markdown("""
                - You're making great progress! This might be a good time to challenge yourself with more advanced content.
                - Consider setting specific learning goals to maintain your momentum.
                - Share your success with others - teaching is a great way to reinforce learning.
                """)
            elif trend == "declining":
                st.markdown("""
                - Learning languages can be challenging - it's okay to take a step back.
                - Try focusing on content you enjoy, like songs, anime, or topics you're interested in.
                - Short, frequent practice sessions may be more effective than long, intense ones.
                - Consider revisiting content you're already comfortable with to rebuild confidence.
                """)
            else:  # stable
                st.markdown("""
                - Your consistent engagement is key to language learning success.
                - Try mixing up your routine with different types of content.
                - Set small, achievable daily goals to maintain motivation.
                - Consider joining a language exchange to practice with native speakers.
                """)