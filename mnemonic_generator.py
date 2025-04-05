"""
AI-powered Mnemonic Generator for Japanese vocabulary and kanji.

This module provides functionality to generate memorable mnemonics
to help users remember Japanese vocabulary and kanji characters.
"""

import streamlit as st
import re
import os
from utils import load_grammar_rules
from database import get_db, UserProgress
import json
from random import choice

# Try to use OpenAI for mnemonic generation
try:
    from openai import OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except ImportError:
    openai_client = None
    st.warning("OpenAI package not installed. Using fallback mnemonic generation methods.")

class MnemonicGenerator:
    """
    Generator for creating memorable mnemonics for Japanese vocabulary and kanji.
    """
    
    def __init__(self, openai_client=None):
        """
        Initialize the mnemonic generator.
        
        Args:
            openai_client: Optional OpenAI client for AI-generated mnemonics
        """
        self.openai_client = openai_client
        
        # Load list of common kanji if available
        try:
            with open("data/common_kanji.json", "r", encoding="utf-8") as f:
                self.common_kanji = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.common_kanji = {}
    
    def generate_mnemonic(self, japanese_word, english_meaning=None, kanji_only=False):
        """
        Generate a mnemonic for a Japanese word or kanji.
        
        Args:
            japanese_word: The Japanese word or kanji to generate a mnemonic for
            english_meaning: The English meaning of the word (optional)
            kanji_only: Whether to focus only on the kanji components
            
        Returns:
            Dictionary with mnemonic information
        """
        if not japanese_word:
            return {"error": "No Japanese word provided"}
        
        # Try AI-generated mnemonic if OpenAI is available
        if self.openai_client:
            return self._generate_ai_mnemonic(japanese_word, english_meaning, kanji_only)
        else:
            # Use pattern-based mnemonic generation as fallback
            return self._generate_pattern_mnemonic(japanese_word, english_meaning, kanji_only)
    
    def _generate_ai_mnemonic(self, japanese_word, english_meaning=None, kanji_only=False):
        """
        Generate a mnemonic using OpenAI.
        
        Args:
            japanese_word: The Japanese word or kanji
            english_meaning: The English meaning (optional)
            kanji_only: Whether to focus only on kanji components
            
        Returns:
            Dictionary with mnemonic information
        """
        try:
            # Prepare prompt based on input
            if kanji_only:
                kanji_chars = re.findall(r'[\u4e00-\u9faf]', japanese_word)
                if not kanji_chars:
                    return {"error": "No kanji characters found in input"}
                
                prompt = f"""Create a memorable mnemonic to help remember the following kanji: {', '.join(kanji_chars)}
                
                For each kanji, provide:
                1. Visual components breakdown
                2. A vivid story or image that connects to its meaning
                3. An example word using the kanji
                
                If you know the meaning, it is: {english_meaning or 'unknown'}
                
                Format as JSON with these fields:
                - kanji: The kanji character
                - meaning: The meaning of the kanji
                - components: Visual components that make up the kanji
                - mnemonic_story: A memorable story connecting the components to the meaning
                - example_word: An example word using this kanji
                - example_meaning: The meaning of the example word
                """
            else:
                prompt = f"""Create a memorable mnemonic to help remember the Japanese word: {japanese_word}
                
                If you know, the English meaning is: {english_meaning or 'unknown'}
                
                Please include:
                1. Pronunciation guide with similar-sounding English words
                2. A vivid story that connects the sound and meaning
                3. Any kanji breakdown if the word contains kanji
                
                Format as JSON with these fields:
                - word: The Japanese word
                - pronunciation: How to pronounce it using English-like sounds
                - meaning: The English meaning
                - mnemonic_story: A memorable story connecting pronunciation to meaning
                - kanji_components: If applicable, breakdown of any kanji in the word
                """
            
            # Call the OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {"role": "system", "content": "You are a Japanese language learning assistant specializing in creating memorable mnemonics."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            # Fall back to pattern-based mnemonic if AI fails
            st.warning(f"AI mnemonic generation failed: {str(e)}. Using pattern-based generation instead.")
            return self._generate_pattern_mnemonic(japanese_word, english_meaning, kanji_only)
    
    def _generate_pattern_mnemonic(self, japanese_word, english_meaning=None, kanji_only=False):
        """
        Generate a mnemonic using pattern-based approaches.
        
        Args:
            japanese_word: The Japanese word or kanji
            english_meaning: The English meaning (optional)
            kanji_only: Whether to focus only on kanji components
            
        Returns:
            Dictionary with mnemonic information
        """
        # Extract kanji characters if kanji_only is True
        if kanji_only:
            kanji_chars = re.findall(r'[\u4e00-\u9faf]', japanese_word)
            if not kanji_chars:
                return {"error": "No kanji characters found in input"}
            
            # Create a mnemonic for each kanji
            kanji_mnemonics = []
            for kanji in kanji_chars:
                mnemonic = self._create_kanji_mnemonic(kanji)
                kanji_mnemonics.append(mnemonic)
            
            return {
                "kanji_breakdown": True,
                "word": japanese_word,
                "kanji_mnemonics": kanji_mnemonics
            }
        else:
            # Create a mnemonic for the whole word
            return self._create_word_mnemonic(japanese_word, english_meaning)
    
    def _create_kanji_mnemonic(self, kanji):
        """
        Create a mnemonic for a single kanji character.
        
        Args:
            kanji: The kanji character
            
        Returns:
            Dictionary with kanji mnemonic information
        """
        # Look up kanji information from our common kanji dictionary
        kanji_info = self.common_kanji.get(kanji, {})
        
        # If we don't have information, provide a basic structure
        if not kanji_info:
            return {
                "kanji": kanji,
                "meaning": "Unknown",
                "components": "Unknown",
                "mnemonic_story": f"This kanji {kanji} can be remembered by breaking it down into its visual components and creating a story connecting them to its meaning.",
                "example_word": "",
                "example_meaning": ""
            }
        
        # Use the information we have
        return {
            "kanji": kanji,
            "meaning": kanji_info.get("meaning", "Unknown"),
            "components": kanji_info.get("components", "Unknown"),
            "mnemonic_story": kanji_info.get("mnemonic", f"Look at the components of {kanji} and imagine a story connecting them."),
            "example_word": kanji_info.get("example_word", ""),
            "example_meaning": kanji_info.get("example_meaning", "")
        }
    
    def _create_word_mnemonic(self, word, english_meaning=None):
        """
        Create a mnemonic for a Japanese word.
        
        Args:
            word: The Japanese word
            english_meaning: The English meaning (optional)
            
        Returns:
            Dictionary with word mnemonic information
        """
        # Extract kanji if present
        kanji_chars = re.findall(r'[\u4e00-\u9faf]', word)
        
        # Basic pronunciation guide
        pronunciation = word
        for sound in ["ka", "ki", "ku", "ke", "ko", "sa", "shi", "su", "se", "so", 
                     "ta", "chi", "tsu", "te", "to", "na", "ni", "nu", "ne", "no",
                     "ha", "hi", "fu", "he", "ho", "ma", "mi", "mu", "me", "mo",
                     "ya", "yu", "yo", "ra", "ri", "ru", "re", "ro", "wa", "wo", "n"]:
            if sound in word.lower():
                pronunciation = pronunciation.replace(sound, f"*{sound}*")
        
        # Create a basic mnemonic structure
        mnemonic = {
            "word": word,
            "pronunciation": pronunciation,
            "meaning": english_meaning or "Unknown",
            "mnemonic_story": f"To remember the word '{word}', break it into sounds and create a vivid mental image connecting the sounds to its meaning.",
            "kanji_components": []
        }
        
        # Add kanji information if available
        if kanji_chars:
            for kanji in kanji_chars:
                kanji_info = self._create_kanji_mnemonic(kanji)
                mnemonic["kanji_components"].append(kanji_info)
        
        return mnemonic

def render_mnemonic_generator_ui():
    """
    Render the UI for the mnemonic generator.
    """
    st.title("📝 AI Mnemonic Generator")
    
    st.markdown("""
    Create memorable mnemonics to help you remember Japanese vocabulary and kanji.
    Mnemonics are memory aids that use associations, stories, or imagery to make learning easier.
    """)
    
    # Initialize the mnemonic generator
    global openai_client
    generator = MnemonicGenerator(openai_client)
    
    # Create tabs for different types of mnemonics
    tabs = st.tabs(["Vocabulary Mnemonics", "Kanji Breakdown", "Saved Mnemonics"])
    
    # Vocabulary Mnemonics tab
    with tabs[0]:
        st.header("Vocabulary Mnemonics")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            japanese_word = st.text_input(
                "Japanese Word/Phrase",
                placeholder="Enter a Japanese word or phrase",
                key="japanese_word_input"
            )
        
        with col2:
            english_meaning = st.text_input(
                "English Meaning (Optional)",
                placeholder="Optional meaning",
                key="english_meaning_input"
            )
        
        if st.button("Generate Vocabulary Mnemonic", key="gen_vocab_mnemonic_btn"):
            if japanese_word:
                with st.spinner("Creating your mnemonic..."):
                    result = generator.generate_mnemonic(japanese_word, english_meaning, kanji_only=False)
                
                if "error" in result:
                    st.error(result["error"])
                else:
                    _display_word_mnemonic(result)
                    
                    # Option to save the mnemonic
                    if st.button("Save This Mnemonic", key="save_word_mnemonic"):
                        _save_mnemonic(result, "vocabulary")
                        st.success("Mnemonic saved successfully!")
            else:
                st.warning("Please enter a Japanese word or phrase.")
    
    # Kanji Breakdown tab
    with tabs[1]:
        st.header("Kanji Breakdown")
        
        kanji_input = st.text_input(
            "Kanji Characters",
            placeholder="Enter one or more kanji characters",
            key="kanji_input"
        )
        
        if st.button("Analyze Kanji", key="analyze_kanji_btn"):
            if kanji_input:
                # Check if input contains kanji
                if re.search(r'[\u4e00-\u9faf]', kanji_input):
                    with st.spinner("Analyzing kanji..."):
                        result = generator.generate_mnemonic(kanji_input, kanji_only=True)
                    
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        _display_kanji_mnemonics(result)
                        
                        # Option to save the kanji analysis
                        if st.button("Save This Kanji Analysis", key="save_kanji_analysis"):
                            _save_mnemonic(result, "kanji")
                            st.success("Kanji analysis saved successfully!")
                else:
                    st.warning("No kanji characters detected. Please enter at least one kanji character.")
            else:
                st.warning("Please enter one or more kanji characters.")
    
    # Saved Mnemonics tab
    with tabs[2]:
        st.header("Your Saved Mnemonics")
        
        # Get saved mnemonics from session state
        if "saved_mnemonics" not in st.session_state:
            st.session_state.saved_mnemonics = []
        
        if not st.session_state.saved_mnemonics:
            st.info("You haven't saved any mnemonics yet. Generate and save mnemonics to see them here.")
        else:
            # Filter options
            filter_type = st.radio(
                "Filter by type:",
                ["All", "Vocabulary", "Kanji"],
                horizontal=True,
                key="mnemonic_filter"
            )
            
            # Filter mnemonics based on selection
            filtered_mnemonics = st.session_state.saved_mnemonics
            if filter_type == "Vocabulary":
                filtered_mnemonics = [m for m in st.session_state.saved_mnemonics if m["type"] == "vocabulary"]
            elif filter_type == "Kanji":
                filtered_mnemonics = [m for m in st.session_state.saved_mnemonics if m["type"] == "kanji"]
            
            if not filtered_mnemonics:
                st.info(f"No {filter_type.lower()} mnemonics saved yet.")
            else:
                # Create expandable sections for each saved mnemonic
                for i, mnemonic in enumerate(filtered_mnemonics):
                    if mnemonic["type"] == "vocabulary":
                        with st.expander(f"{mnemonic['data']['word']} - {mnemonic['data']['meaning']}", expanded=False):
                            _display_word_mnemonic(mnemonic["data"])
                            
                            # Delete option
                            if st.button("Delete", key=f"delete_mnemonic_{i}"):
                                st.session_state.saved_mnemonics.remove(mnemonic)
                                st.rerun()
                    elif mnemonic["type"] == "kanji":
                        with st.expander(f"Kanji Analysis: {mnemonic['data']['word']}", expanded=False):
                            _display_kanji_mnemonics(mnemonic["data"])
                            
                            # Delete option
                            if st.button("Delete", key=f"delete_kanji_analysis_{i}"):
                                st.session_state.saved_mnemonics.remove(mnemonic)
                                st.rerun()

def _display_word_mnemonic(mnemonic_data):
    """
    Display a vocabulary mnemonic in a nice format.
    
    Args:
        mnemonic_data: Dictionary with mnemonic information
    """
    # Create a card-like display for the mnemonic
    st.markdown(f"""
    <div style="background-color: #f0f8ff; padding: 15px; border-radius: 10px; border-left: 5px solid #4169e1;">
        <h3 style="color: #333;">{mnemonic_data['word']}</h3>
        <p><strong>Meaning:</strong> {mnemonic_data['meaning']}</p>
        <p><strong>Pronunciation:</strong> {mnemonic_data['pronunciation']}</p>
        <h4>Mnemonic Story:</h4>
        <p style="font-style: italic;">{mnemonic_data['mnemonic_story']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display kanji components if available
    if mnemonic_data.get('kanji_components') and len(mnemonic_data['kanji_components']) > 0:
        st.markdown("### Kanji Components")
        
        for i, component in enumerate(mnemonic_data['kanji_components']):
            st.markdown(f"""
            <div style="background-color: #fff8f0; padding: 10px; margin: 10px 0; border-radius: 5px; border-left: 3px solid #ffa500;">
                <h4 style="margin-top: 0;">{component['kanji']} - {component['meaning']}</h4>
                <p><strong>Components:</strong> {component['components']}</p>
                <p><strong>Story:</strong> {component['mnemonic_story']}</p>
                {f"<p><strong>Example:</strong> {component['example_word']} ({component['example_meaning']})</p>" if component.get('example_word') else ""}
            </div>
            """, unsafe_allow_html=True)

def _display_kanji_mnemonics(kanji_data):
    """
    Display kanji mnemonics in a nice format.
    
    Args:
        kanji_data: Dictionary with kanji mnemonic information
    """
    st.markdown(f"## Analysis for: {kanji_data['word']}")
    
    if kanji_data.get('kanji_mnemonics'):
        for i, mnemonic in enumerate(kanji_data['kanji_mnemonics']):
            st.markdown(f"""
            <div style="background-color: #fff8f0; padding: 15px; margin: 15px 0; border-radius: 10px; border-left: 5px solid #ffa500;">
                <h3 style="color: #333;">{mnemonic['kanji']} - {mnemonic['meaning']}</h3>
                <p><strong>Components:</strong> {mnemonic['components']}</p>
                <h4>Mnemonic Story:</h4>
                <p style="font-style: italic;">{mnemonic['mnemonic_story']}</p>
                {f"<p><strong>Example:</strong> {mnemonic['example_word']} ({mnemonic['example_meaning']})</p>" if mnemonic.get('example_word') else ""}
            </div>
            """, unsafe_allow_html=True)
    elif kanji_data.get('kanji_mnemonic'):
        # Handle single kanji mnemonic
        mnemonic = kanji_data['kanji_mnemonic']
        st.markdown(f"""
        <div style="background-color: #fff8f0; padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500;">
            <h3 style="color: #333;">{mnemonic['kanji']} - {mnemonic['meaning']}</h3>
            <p><strong>Components:</strong> {mnemonic['components']}</p>
            <h4>Mnemonic Story:</h4>
            <p style="font-style: italic;">{mnemonic['mnemonic_story']}</p>
            {f"<p><strong>Example:</strong> {mnemonic['example_word']} ({mnemonic['example_meaning']})</p>" if mnemonic.get('example_word') else ""}
        </div>
        """, unsafe_allow_html=True)

def _save_mnemonic(data, mnemonic_type):
    """
    Save a mnemonic to session state.
    
    Args:
        data: The mnemonic data
        mnemonic_type: Type of mnemonic ("vocabulary" or "kanji")
    """
    if "saved_mnemonics" not in st.session_state:
        st.session_state.saved_mnemonics = []
    
    # Create a mnemonic record
    mnemonic_record = {
        "type": mnemonic_type,
        "data": data,
        "saved_at": str(st.session_state.get("session_id", "unknown"))
    }
    
    # Add to saved mnemonics
    st.session_state.saved_mnemonics.append(mnemonic_record)