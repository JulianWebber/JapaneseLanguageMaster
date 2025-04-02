"""
AI Language Companion UI Components

This module provides UI components for the Japanese language learning companion chatbot.
"""

import streamlit as st
import json
from typing import Callable, Dict, Any, List, Optional
from ai_language_companion import AILanguageCompanion

def create_message_container():
    """Create a container for chat messages if it doesn't exist"""
    if "companion_messages" not in st.session_state:
        st.session_state.companion_messages = []

def store_message(role: str, content: str, avatar: Optional[str] = None):
    """
    Store a message in the chat history
    
    Args:
        role: The role of the sender (user or assistant)
        content: The message content
        avatar: Optional avatar emoji for the message
    """
    if "companion_messages" not in st.session_state:
        create_message_container()
    
    st.session_state.companion_messages.append({
        "role": role,
        "content": content,
        "avatar": avatar
    })

def get_personality_avatar(personality_key: str) -> str:
    """Get the avatar for a specific personality"""
    personality_avatars = {
        "sensei": "👨‍🏫",
        "friend": "😊",
        "anime_fan": "🎭",
        "cultural_guide": "🏯",
        "business_coach": "💼"
    }
    return personality_avatars.get(personality_key, "🤖")

def render_chat_interface(companion: AILanguageCompanion):
    """
    Render the chat interface for the AI language companion
    
    Args:
        companion: An instance of the AILanguageCompanion
    """
    # Initialize message container if needed
    create_message_container()
    
    # Get current personality
    current_personality = companion.get_current_personality()
    personality_avatar = current_personality["avatar"]
    
    # Create a styled container for the chat interface
    st.markdown("""
    <style>
        .chat-container {
            border-radius: 10px;
            border: 1px solid #ddd;
            margin-bottom: 20px;
            background-color: rgba(255, 252, 245, 0.8);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .chat-message {
            padding: 10px 15px;
            margin: 8px;
            border-radius: 15px;
            position: relative;
            font-family: 'EB Garamond', 'Noto Serif JP', serif;
            animation: fadeIn 0.5s ease-out;
        }
        .user-message {
            background-color: #e1f5fe;
            border-bottom-right-radius: 5px;
            margin-left: 50px;
            box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        .assistant-message {
            background-color: #fff8e1;
            border-bottom-left-radius: 5px;
            margin-right: 50px;
            box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        .avatar {
            font-size: 24px;
            position: absolute;
            top: -10px;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .user-avatar {
            right: -20px;
        }
        .assistant-avatar {
            left: -20px;
        }
        .message-content {
            padding: 5px 0;
            line-height: 1.5;
        }
        .chat-controls {
            position: sticky;
            bottom: 0;
            background-color: rgba(255, 252, 245, 0.95);
            padding: 15px;
            border-top: 1px solid #eee;
            backdrop-filter: blur(5px);
            z-index: 100;
        }
        .personality-selector {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 10px;
            background-color: rgba(255, 248, 225, 0.5);
            border: 1px dashed #DAA520;
        }
        .stTextInput input {
            border-radius: 20px;
            padding: 10px 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            font-family: 'EB Garamond', 'Noto Serif JP', serif;
        }
        .stButton button {
            border-radius: 20px;
            padding: 2px 20px;
            background-color: #DAA520;
            color: white;
            border: none;
            font-family: 'Cinzel', serif;
            letter-spacing: 0.05em;
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            background-color: #B8860B;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .typing-indicator {
            display: flex;
            padding: 10px 15px;
            background-color: #fff8e1;
            border-radius: 15px;
            margin: 8px;
            margin-right: 50px;
            border-bottom-left-radius: 5px;
            box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
            animation: fadeIn 0.3s ease-out;
        }
        .typing-dot {
            width: 8px;
            height: 8px;
            margin: 0 3px;
            background-color: #DAA520;
            border-radius: 50%;
            opacity: 0.7;
            animation: typing 1.5s infinite ease-in-out;
        }
        .typing-dot:nth-child(1) {
            animation-delay: 0s;
        }
        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes typing {
            0%, 100% {
                transform: translateY(0px);
                opacity: 0.7;
            }
            50% {
                transform: translateY(-5px);
                opacity: 1;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Display personality selector
    available_personalities = companion.get_available_personalities()
    
    st.markdown("""
    <div class="personality-selector">
        <h3 style="margin-top: 0; color: #DAA520; font-family: serif; text-align: center; font-size: 1.2rem;">
            会話スタイルを選択 / Select a Conversation Style
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a row of personality options
    cols = st.columns(len(available_personalities))
    for i, (key, personality) in enumerate(available_personalities.items()):
        with cols[i]:
            is_selected = key == current_personality["key"]
            selected_style = "background-color: rgba(255, 215, 0, 0.2); border: 2px solid #DAA520;" if is_selected else ""
            
            # Create a clickable personality card
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; border-radius: 10px; {selected_style} cursor: pointer; 
                        margin-bottom: 10px; height: 120px; display: flex; flex-direction: column; justify-content: center;
                        transition: all 0.3s ease;" id="{key}_personality">
                <div style="font-size: 40px; margin-bottom: 5px;">{personality['avatar']}</div>
                <div style="font-weight: bold; margin-bottom: 5px; font-family: 'Noto Serif JP', serif;">
                    {personality['name']}
                </div>
                <div style="font-size: 0.8rem; color: #666;">
                    {personality['description'][:50]}...
                </div>
            </div>
            <script>
                document.getElementById("{key}_personality").addEventListener("click", function() {{
                    window.parent.postMessage({{
                        type: "streamlit:setComponentValue",
                        value: "{key}"
                    }}, "*");
                }});
            </script>
            """, unsafe_allow_html=True)
            
            # Use a hidden button to handle the actual selection
            if st.button(f"Select {personality['name']}", key=f"btn_{key}", help=personality["description"]):
                companion.select_personality(key)
                st.rerun()
    
    # Display the chat messages
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    
    # Show welcome message if no messages yet
    if len(st.session_state.companion_messages) == 0:
        welcome_message = f"""
        こんにちは！私はあなたの日本語学習パートナーです。 
        (Hello! I am your Japanese language learning partner.)
        
        I'm here to help you practice Japanese, answer your questions, and provide personalized lessons.
        
        You can:
        • Ask me questions about Japanese grammar or vocabulary
        • Practice conversation in Japanese
        • Request explanations of specific language points
        • Ask for translation help
        • Get personalized practice exercises
        
        どうぞよろしくお願いします！(I look forward to working with you!)
        """
        store_message("assistant", welcome_message, personality_avatar)
    
    # Render all stored messages
    for idx, msg in enumerate(st.session_state.companion_messages):
        if msg["role"] == "user":
            avatar_position = "user-avatar"
            message_class = "user-message"
            avatar = msg.get("avatar", "👤")
            show_reactions = False
        else:
            avatar_position = "assistant-avatar"
            message_class = "assistant-message"
            avatar = msg.get("avatar", personality_avatar)
            show_reactions = True
        
        content_with_breaks = msg['content'].replace('\n', '<br>')
        
        # Create unique message container ID for JavaScript interactions
        message_id = f"msg_{idx}"
        
        st.markdown(f"""
        <div class='chat-message {message_class}' id='{message_id}'>
            <div class='avatar {avatar_position}'>{avatar}</div>
            <div class='message-content'>{content_with_breaks}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add reaction buttons for assistant messages
        if show_reactions:
            # Create a row of reaction buttons
            reaction_cols = st.columns([1, 1, 1, 1, 1])
            common_reactions = ["👍", "❤️", "🎯", "🔄", "🤔"]
            
            with st.container():
                for i, emoji in enumerate(common_reactions):
                    with reaction_cols[i]:
                        if st.button(emoji, key=f"reaction_{idx}_{emoji}", help=f"React with {emoji}"):
                            # Record the reaction
                            result = companion.record_user_reaction(idx, emoji)
                            if result.get("success", False):
                                st.success(f"Recorded your {emoji} reaction!", icon=emoji)
                            else:
                                st.error(f"Failed to record reaction: {result.get('error', 'Unknown error')}")
                            
                            # Add short delay to show the success message
                            import time
                            time.sleep(0.5)
                            st.rerun()
    
    # Create the input area
    st.markdown("<div class='chat-controls'>", unsafe_allow_html=True)
    
    # User input and send button
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            "Message",
            key="companion_input",
            placeholder="Type your message here...",
            label_visibility="collapsed"
        )
    with col2:
        send_button = st.button("送信", help="Send message")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Create a conversation starters section
    with st.expander("💬 Conversation Starters", expanded=False):
        st.markdown("#### Choose a topic to get conversation prompts:")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            topic_category = st.selectbox(
                "Topic category:",
                ["general", "travel", "culture", "business"],
                key="starter_category"
            )
        with col2:
            if st.button("Get Starters", key="get_starters_btn"):
                starters = companion.get_conversation_starters(topic_category)
                st.session_state.conversation_starters = starters
        
        # Display conversation starters if available
        if "conversation_starters" in st.session_state and st.session_state.conversation_starters:
            st.markdown("#### Suggested conversation starters:")
            for i, starter in enumerate(st.session_state.conversation_starters):
                cols = st.columns([5, 1])
                with cols[0]:
                    st.markdown(f"**🇺🇸 {starter['en']}**")
                    st.markdown(f"**🇯🇵 {starter['ja']}**")
                with cols[1]:
                    if st.button("Use", key=f"use_starter_{i}"):
                        # Add to input and clear after clicking
                        st.session_state.companion_input = starter['ja']
                        st.rerun()
    
    # Create a tools section
    with st.expander("🧰 Learning Tools", expanded=False):
        tool_tabs = st.tabs(["Practice Exercises", "Translation Helper", "Grammar Explanation", "Vocabulary Flashcards"])
        
        with tool_tabs[0]:
            st.markdown("### 🏋️ Practice Exercises")
            exercise_type = st.selectbox(
                "Select exercise type:",
                ["grammar", "vocabulary", "conversation", "reading"],
                key="exercise_type"
            )
            if st.button("Generate Exercise", key="gen_exercise"):
                with st.spinner("Creating personalized exercise..."):
                    exercise = companion.generate_practice_exercise(exercise_type)
                    if not exercise.get("error", False):
                        st.markdown(f"## {exercise_type.title()} Exercise")
                        st.markdown(exercise["exercise"])
                    else:
                        st.error(exercise["exercise"])
        
        with tool_tabs[1]:
            st.markdown("### 🔤 Translation Helper")
            translation_direction = st.radio(
                "Translation direction:",
                ["Japanese to English", "English to Japanese"],
                key="translation_direction"
            )
            text_to_translate = st.text_area(
                "Text to translate:",
                key="text_to_translate",
                height=100
            )
            if st.button("Translate", key="translate_btn"):
                if text_to_translate:
                    with st.spinner("Translating..."):
                        direction = "ja_to_en" if translation_direction == "Japanese to English" else "en_to_ja"
                        translation = companion.translate_text(text_to_translate, direction)
                        if not translation.get("error", False):
                            st.markdown("### Translation")
                            st.markdown(translation["translation"])
                        else:
                            st.error(translation["translation"])
                else:
                    st.warning("Please enter some text to translate.")
        
        with tool_tabs[2]:
            st.markdown("### 📚 Grammar Explanation")
            grammar_point = st.text_input(
                "Enter a grammar point (e.g., te-form, ~たら, など):",
                key="grammar_point"
            )
            if st.button("Explain", key="explain_btn"):
                if grammar_point:
                    with st.spinner("Generating explanation..."):
                        explanation = companion.explain_grammar_point(grammar_point)
                        if not explanation.get("error", False):
                            st.markdown(f"### {grammar_point}")
                            st.markdown(explanation["explanation"])
                        else:
                            st.error(explanation["explanation"])
                else:
                    st.warning("Please enter a grammar point.")
        
        with tool_tabs[3]:
            st.markdown("### 🎴 Vocabulary Flashcards")
            
            flashcard_col1, flashcard_col2 = st.columns([3, 1])
            with flashcard_col1:
                flashcard_topic = st.text_input(
                    "Enter a vocabulary topic (e.g., food, travel, emotions):",
                    key="flashcard_topic"
                )
            with flashcard_col2:
                flashcard_count = st.number_input(
                    "Count:",
                    min_value=1,
                    max_value=10,
                    value=5,
                    step=1,
                    key="flashcard_count"
                )
            
            if st.button("Generate Flashcards", key="generate_flashcards_btn"):
                if flashcard_topic:
                    with st.spinner("Creating vocabulary flashcards..."):
                        flashcards = companion.generate_flashcards(flashcard_topic, flashcard_count)
                        
                        if flashcards and not any(card.get("error") for card in flashcards):
                            st.session_state.flashcards = flashcards
                            st.session_state.current_flashcard = 0
                        else:
                            error_msg = next((card.get("error") for card in flashcards if card.get("error")), "Failed to generate flashcards")
                            st.error(error_msg)
                else:
                    st.warning("Please enter a vocabulary topic.")
            
            # Display flashcards if available
            if "flashcards" in st.session_state and st.session_state.flashcards:
                current_index = st.session_state.current_flashcard
                if current_index < len(st.session_state.flashcards):
                    card = st.session_state.flashcards[current_index]
                    
                    # Create a styled flashcard
                    st.markdown("""
                    <style>
                    .flashcard {
                        background-color: #fff8e1;
                        border-radius: 10px;
                        padding: 20px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        margin: 10px 0;
                        border-left: 5px solid #DAA520;
                    }
                    .jp-term {
                        font-size: 2rem;
                        font-weight: bold;
                        color: #1A1A1A;
                        margin-bottom: 5px;
                        font-family: 'Noto Serif JP', serif;
                    }
                    .reading {
                        font-size: 1.2rem;
                        color: #666;
                        margin-bottom: 15px;
                        font-family: 'Noto Sans JP', sans-serif;
                    }
                    .meaning {
                        font-size: 1.5rem;
                        margin-bottom: 15px;
                        color: #333;
                        font-family: 'EB Garamond', serif;
                    }
                    .example {
                        background-color: rgba(218, 165, 32, 0.1);
                        padding: 10px;
                        border-radius: 5px;
                        margin-bottom: 10px;
                        font-family: 'Noto Serif JP', serif;
                    }
                    .note {
                        font-style: italic;
                        background-color: #e8f4f8;
                        padding: 8px;
                        border-radius: 5px;
                        font-size: 0.9rem;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Display the card content
                    st.markdown(f"""
                    <div class="flashcard">
                        <div class="jp-term">{card.get('japanese', '')}</div>
                        <div class="reading">{card.get('reading', '')}</div>
                        <div class="meaning">{card.get('english', '')}</div>
                        <div class="example">
                            <div>{card.get('example_ja', '')}</div>
                            <div>{card.get('example_en', '')}</div>
                        </div>
                        <div class="note">📝 {card.get('note', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Navigation buttons
                    nav_cols = st.columns([1, 1, 1])
                    with nav_cols[0]:
                        if current_index > 0:
                            if st.button("⬅️ Previous", key="prev_card"):
                                st.session_state.current_flashcard -= 1
                                st.rerun()
                    
                    with nav_cols[1]:
                        st.markdown(f"**Card {current_index + 1} of {len(st.session_state.flashcards)}**", 
                                  unsafe_allow_html=True)
                    
                    with nav_cols[2]:
                        if current_index < len(st.session_state.flashcards) - 1:
                            if st.button("Next ➡️", key="next_card"):
                                st.session_state.current_flashcard += 1
                                st.rerun()
    
    # Handle the send button click
    if send_button and user_input:
        # Add user message to chat
        store_message("user", user_input)
        
        # Get assistant response
        with st.spinner("思考中... (Thinking...)"):
            response = companion.send_message(user_input)
        
        if not response.get("error", False):
            # Add assistant message to chat
            store_message("assistant", response["response"], personality_avatar)
        else:
            # Add error message
            store_message("assistant", f"Error: {response['response']}", "❌")
        
        # Clear the input field (requires a rerun)
        st.session_state.companion_input = ""
        st.rerun()

def render_conversation_history(companion: AILanguageCompanion):
    """
    Render the conversation history management UI
    
    Args:
        companion: An instance of the AILanguageCompanion
    """
    st.markdown("### 会話履歴 / Conversation History")
    
    if st.button("Clear Conversation History", key="clear_history"):
        # Clear the conversation history both in UI and backend
        if "companion_messages" in st.session_state:
            st.session_state.companion_messages = []
        companion.clear_chat_history()
        st.success("Conversation history cleared!")
        st.rerun()

def render_companion_dashboard(companion: AILanguageCompanion):
    """
    Render a dashboard with the user's learning profile and companion stats
    
    Args:
        companion: An instance of the AILanguageCompanion
    """
    st.markdown("### あなたの学習プロフィール / Your Learning Profile")
    
    # Get user profile
    profile = companion._load_user_profile()
    
    # Display basic stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Level", profile.get("level", "Beginner").title())
    with col2:
        st.metric("Learning Streak", f"{profile.get('current_streak', 0)} days")
    with col3:
        st.metric("Overall Accuracy", f"{profile.get('average_accuracy', 0):.1f}%")
    
    # Show strengths and areas to work on
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Strengths:**")
        strengths = profile.get("strong_areas", [])
        if strengths:
            for strength in strengths:
                st.success(f"• {strength}")
        else:
            st.info("Complete an assessment to identify your strengths!")
    
    with col2:
        st.markdown("**Areas to Focus On:**")
        weak_areas = profile.get("weak_areas", [])
        if weak_areas:
            for area in weak_areas:
                st.warning(f"• {area}")
        else:
            st.info("Complete an assessment to identify areas to improve!")
    
    # Recent badges earned
    st.markdown("### 最近獲得したバッジ / Recently Earned Badges")
    badges = []
    for category, badge_list in profile.get("achievements", {}).items():
        for badge_id in badge_list:
            badges.append(badge_id)
    
    if badges:
        # Show most recent 3 badges
        badge_cols = st.columns(min(3, len(badges)))
        for i, badge_id in enumerate(badges[-3:]):
            with badge_cols[i]:
                st.markdown(f"**🏆 {badge_id}**")
    else:
        st.info("Practice more to earn achievement badges!")