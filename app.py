import streamlit as st
import json
from grammar_checker import GrammarChecker
from gpt_grammar_checker import GPTGrammarChecker
from utils import load_grammar_rules, analyze_text
from database import get_db, GrammarCheck, CustomGrammarRule, UserProgress, LanguageAssessment
from contextlib import contextmanager
import uuid
from visualizations import (
    create_streak_chart,
    create_mastery_radar,
    create_achievement_progress,
    create_japanese_cultural_badge_progress,
    create_japanese_badge_card,
    create_next_badge_card
)
from japanese_badges import get_badge_info
from assessment import LanguageLevelAssessor
from idiom_translator import IdiomTranslator
from mood_selector import MoodDifficultySelector
from lesson_content import LessonManager, Lesson, LessonCompletion
from ai_language_companion import AILanguageCompanion
from companion_ui import render_chat_interface, render_conversation_history, render_companion_dashboard
from translation_memory import render_translation_memory_ui

# Initialize the application
st.set_page_config(page_title="Japanese Grammar Checker", layout="wide")

# Add custom CSS for animations and elaborate fonts
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;700&family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Cinzel:wght@400;700&family=EB+Garamond:ital,wght@0,400;0,700;1,400&display=swap');
    
    /* Base font styles */
    .stApp {
        font-family: 'EB Garamond', 'Noto Serif JP', serif;
    }
    
    /* Headings */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Cinzel', 'Noto Serif JP', serif;
        letter-spacing: 0.05em;
        font-weight: 700;
    }
    
    h1, .stMarkdown h1 {
        border-bottom: 2px solid gold;
        padding-bottom: 0.3em;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Paragraph text */
    p, .stMarkdown p {
        font-family: 'EB Garamond', 'Noto Serif JP', serif;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    
    /* Japanese text specifically */
    .japanese-text {
        font-family: 'Noto Serif JP', serif;
        font-weight: 500;
    }
    
    /* Buttons with decorative style */
    .stButton > button {
        font-family: 'Playfair Display', 'Noto Serif JP', serif;
        border: 1px solid #ddd;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        letter-spacing: 0.03em;
    }
    
    /* Sidebar navigation */
    .stSidebar [data-testid="stSidebarNav"] {
        font-family: 'Cinzel', 'Noto Serif JP', serif;
        letter-spacing: 0.05em;
    }
    
    /* Form elements */
    .stTextInput, .stTextArea, .stSelectbox > div > div {
        font-family: 'EB Garamond', 'Noto Serif JP', serif;
        font-size: 1.05rem;
    }

    /* Animation keyframes */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Apply animations to main content */
    .stApp > header,
    .main > div,
    .element-container,
    .stMarkdown,
    .stButton,
    .stTextInput,
    .stTextArea {
        animation: fadeIn 0.5s ease-out;
    }

    /* Smooth transitions for interactive elements */
    .stSelectbox,
    .stMultiSelect,
    .stSlider {
        transition: all 0.3s ease;
    }

    /* Hover effects */
    .stButton > button:hover {
        transform: translateY(-2px);
        transition: transform 0.3s ease;
        border-color: gold;
    }

    /* Sidebar transitions */
    .sidebar .sidebar-content {
        transition: margin 0.3s ease-in-out;
    }
    /* Achievement cards animation */
    .achievement-card {
        animation: slideIn 0.5s ease-out;
        transition: transform 0.3s ease;
        font-family: 'Playfair Display', 'Noto Serif JP', serif;
        border-left: 3px solid gold;
        padding-left: 10px;
    }
    .achievement-card:hover {
        transform: translateY(-5px);
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }

    /* Progress bar animations */
    .stProgress > div {
        transition: width 1s ease-in-out;
    }

    /* Tab transitions */
    .stTabs {
        transition: opacity 0.3s ease;
        font-family: 'Cinzel', 'Noto Serif JP', serif;
    }
    .stTab {
        transition: background-color 0.3s ease;
    }

    /* Loading animation */
    .stSpinner {
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    /* Success message animation */
    .stSuccess {
        animation: fadeInUp 0.5s ease-out;
        font-family: 'EB Garamond', 'Noto Serif JP', serif;
        font-style: italic;
    }
    @keyframes fadeInUp {
        from { 
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Error message animation */
    .stError {
        animation: shake 0.5s ease-in-out;
        font-family: 'EB Garamond', 'Noto Serif JP', serif;
    }
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }

    /* Form transition */
    .stForm {
        transition: all 0.3s ease;
    }
    .stForm:hover {
        transform: scale(1.01);
    }

    /* Sidebar active state */
    .stSidebar [data-testid="stSidebarNav"] li {
        transition: all 0.2s ease;
    }
    .stSidebar [data-testid="stSidebarNav"] li:hover {
        background-color: rgba(151, 166, 195, 0.15);
        border-radius: 4px;
        border-left: 3px solid gold;
    }
    
    /* Japanese text styling */
    .grammar-result {
        font-family: 'Noto Serif JP', serif;
        font-size: 1.1rem;
        line-height: 1.8;
        padding: 15px;
        border-left: 3px solid #6c757d;
        background-color: rgba(108, 117, 125, 0.05);
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for transitions
if 'previous_page' not in st.session_state:
    st.session_state.previous_page = None

if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    
# Initialize session state for AI input
if 'ai_input_text' not in st.session_state:
    st.session_state.ai_input_text = ""

# Load grammar rules
grammar_rules = load_grammar_rules()

@contextmanager
def get_database():
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

# Initialize the checker with database connection
with get_database() as db:
    checker = GrammarChecker(grammar_rules, db)

st.markdown("<h1 style='font-family: \"Cinzel\", \"Noto Serif JP\", serif; letter-spacing: 0.08em; text-align: center; padding: 20px 0; background: linear-gradient(90deg, rgba(255,215,0,0.1) 0%, rgba(255,215,0,0.2) 50%, rgba(255,215,0,0.1) 100%); border-radius: 5px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>日本語文法チェッカー<br><span style=\"font-size: 0.7em; letter-spacing: 0.05em;\">Japanese Grammar Checker</span></h1>", unsafe_allow_html=True)

# Sidebar navigation with decorative header
st.sidebar.markdown("""
<div style="font-family: 'Cinzel', 'Noto Serif JP', serif; text-align: center; padding: 10px 0; margin-bottom: 20px; border-bottom: 2px solid gold; letter-spacing: 0.08em;">
    <h3 style="margin: 0; color: #333; text-shadow: 1px 1px 1px rgba(0,0,0,0.1);">
        <span style="font-size: 0.9em;">✧</span> Navigation <span style="font-size: 0.9em;">✧</span>
    </h3>
</div>
""", unsafe_allow_html=True)

# Create a custom CSS class for selected navigation items
st.markdown("""
<style>
.nav-option {
    padding: 10px 15px;
    margin: 5px 0;
    border-radius: 5px;
    transition: all 0.3s ease;
    font-family: 'EB Garamond', 'Noto Serif JP', serif;
    border-left: 3px solid transparent;
}
.nav-option:hover {
    background-color: rgba(255, 215, 0, 0.1);
    border-left: 3px solid gold;
}
.nav-option.selected {
    background-color: rgba(255, 215, 0, 0.2);
    border-left: 3px solid gold;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Navigation options with icons
nav_options = [
    {"name": "Grammar Check", "icon": "✓"},
    {"name": "AI Grammar Analysis", "icon": "🤖"},
    {"name": "Progress Dashboard", "icon": "📊"},
    {"name": "Language Companion", "icon": "💬"},
    {"name": "Custom Rules", "icon": "⚙️"},
    {"name": "Self Assessment", "icon": "📝"},
    {"name": "Idiom Translator", "icon": "🔄"},
    {"name": "Pronunciation Practice", "icon": "🎤"},
    {"name": "Lessons", "icon": "📚"},
    {"name": "Translation Memory Bank", "icon": "🔠"}
]

# Get current page from radio buttons but with enhanced styling
page = st.sidebar.radio(
    "Navigation",
    [option["name"] for option in nav_options],
    label_visibility="collapsed"
)

# Display the selected page in an elegant way
st.sidebar.markdown(f"""
<div style="text-align: center; margin: 20px 0; font-family: 'Cinzel', 'Noto Serif JP', serif;">
    <p style="font-size: 0.85em; color: #666; margin-bottom: 5px;">CURRENT SECTION</p>
    <h4 style="margin: 0; color: #333; text-shadow: 1px 1px 1px rgba(0,0,0,0.05);">
        {next((option["icon"] for option in nav_options if option["name"] == page), "")} {page}
    </h4>
</div>
""", unsafe_allow_html=True)

if page == "Grammar Check":
    # Main input section
    st.subheader("Enter Japanese Text")
    input_text = st.text_area("Japanese Text", placeholder="Enter Japanese text here...", key="input_text")
    
    # Add option to use AI-powered analysis
    analysis_mode = st.radio(
        "Analysis Mode",
        ["Standard Analysis", "AI-Powered Analysis (OpenAI)"],
        help="Standard analysis uses predefined grammar rules. AI-Powered analysis uses OpenAI's GPT model for more comprehensive feedback."
    )

    if input_text:
        # Analysis section
        st.subheader("Grammar Analysis")
        
        with st.spinner("Analyzing your text..."):
            # Perform grammar check based on selected mode
            with get_database() as db:
                checker.load_custom_rules()  # Refresh custom rules
                
                if analysis_mode == "Standard Analysis":
                    analysis_results = checker.check_grammar(input_text)
                else:
                    # Use GPT-powered analysis
                    try:
                        gpt_checker = GPTGrammarChecker()
                        gpt_results = gpt_checker.check_grammar(input_text)
                        
                        # Convert GPT results to match our standard format
                        analysis_results = {
                            'grammar_issues': [],
                            'particle_usage': [],
                            'verb_conjugations': [],
                            'advanced_patterns': [],
                            'custom_patterns': []
                        }
                        
                        # Add grammar issues from GPT analysis
                        if 'grammar_issues' in gpt_results and not gpt_results.get('error', False):
                            for issue in gpt_results['grammar_issues']:
                                analysis_results['grammar_issues'].append({
                                    'pattern': issue.get('error_text', ''),
                                    'description': issue.get('explanation', ''),
                                    'suggestion': f"{issue.get('correct_text', '')} - {issue.get('rule', '')}",
                                    'example': issue.get('correct_text', '')
                                })
                        
                        # Add particle usage from GPT analysis
                        if 'particle_usage' in gpt_results and not gpt_results.get('error', False):
                            for particle in gpt_results['particle_usage']:
                                analysis_results['particle_usage'].append({
                                    'particle': particle.get('particle', ''),
                                    'usage': particle.get('usage_context', ''),
                                    'context': f"Correct: {particle.get('correct', False)}",
                                    'suggestion': particle.get('suggestion', '')
                                })
                        
                        # Add verb conjugations from GPT analysis
                        if 'verb_conjugations' in gpt_results and not gpt_results.get('error', False):
                            for verb in gpt_results['verb_conjugations']:
                                analysis_results['verb_conjugations'].append({
                                    'base_form': verb.get('verb', ''),
                                    'conjugation': verb.get('suggestion', ''),
                                    'form': verb.get('form', ''),
                                    'context': f"Correct: {verb.get('correct', False)}"
                                })
                        
                        # Display overall assessment if available
                        if 'overall_assessment' in gpt_results and not gpt_results.get('error', False):
                            st.info("### Overall Assessment")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Naturalness", f"{gpt_results['overall_assessment'].get('naturalness', 0)}/5")
                            with col2:
                                st.metric("Formality", f"{gpt_results['overall_assessment'].get('formality', 0)}/5")
                            with col3:
                                st.metric("Clarity", f"{gpt_results['overall_assessment'].get('clarity', 0)}/5")
                        
                        # Display improved text if available
                        if 'improved_text' in gpt_results and gpt_results['improved_text'] != input_text and not gpt_results.get('error', False):
                            st.success("### Suggested Improvement")
                            st.write(gpt_results['improved_text'])
                        
                        # Display honorific/polite speech analysis if available
                        if 'honorific_polite_speech' in gpt_results and gpt_results['honorific_polite_speech'] and not gpt_results.get('error', False):
                            st.info("### Honorific/Polite Speech Analysis")
                            for expression in gpt_results['honorific_polite_speech']:
                                st.write(f"- **{expression.get('expression', '')}**: {expression.get('type', '')} " +
                                        f"(Level: {expression.get('level', '')})")
                                if expression.get('alternative', ''):
                                    st.write(f"  Alternative: {expression['alternative']}")
                    
                    except Exception as e:
                        st.error(f"Error in AI analysis: {str(e)}")
                        # Fallback to standard analysis
                        analysis_results = checker.check_grammar(input_text)
                        st.warning("Falling back to standard analysis due to an error with AI processing.")
                
                # Get or create user progress
                user_progress = UserProgress.get_or_create(db, st.session_state.session_id)
                
                # Create grammar check linked to user progress
                check = GrammarCheck.create(db, input_text, analysis_results)
                check.user_progress_id = user_progress.id
                
                # Update user progress
                user_progress.update_progress(db, analysis_results)
                
                db.commit()

        # Display results in tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Grammar Issues",
            "Advanced Patterns",
            "Custom Patterns",
            "Particle Usage",
            "Verb Conjugations"
        ])

        with tab1:
            if analysis_results['grammar_issues']:
                for issue in analysis_results['grammar_issues']:
                    with st.expander(f"Issue: {issue.get('pattern', 'Grammar Pattern')}"):
                        # Create the HTML with conditionals outside the f-string
                        example_html = f"<p><span style='color:#35AF35; font-weight:bold; font-family:\"Cinzel\", serif;'>Example:</span> <span class='japanese-text'>{issue['example']}</span></p>" if 'example' in issue else ""
                        context_html = f"<p><span style='color:#8035E3; font-weight:bold; font-family:\"Cinzel\", serif;'>Context:</span> <span class='japanese-text'>{issue['context']}</span></p>" if 'context' in issue else ""
                        custom_rule_html = "<p><em style='font-family:\"EB Garamond\", serif; font-style:italic;'>(Custom Rule)</em></p>" if issue.get('custom_rule') else ""
                        
                        # Now build the complete HTML
                        html = f"""
                        <div class="grammar-result">
                            <p><span style="color:#E35335; font-weight:bold; font-family:'Cinzel', serif;">Description:</span> 
                            <span class="japanese-text">{issue['description']}</span></p>
                            
                            <p><span style="color:#3581E3; font-weight:bold; font-family:'Cinzel', serif;">Suggestion:</span> 
                            <span class="japanese-text">{issue['suggestion']}</span></p>
                            
                            {example_html}
                            
                            {context_html}
                            
                            {custom_rule_html}
                        </div>
                        """
                        st.markdown(html, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 15px; border-left: 3px solid #35AF35; background-color: rgba(53, 175, 53, 0.1); font-family: 'EB Garamond', serif; font-size: 1.1rem;">
                    <span style="color:#35AF35; font-weight:bold; font-family:'Cinzel', serif;">✓</span> No grammar issues found!
                </div>
                """, unsafe_allow_html=True)

        with tab2:
            if analysis_results.get('advanced_patterns'):
                for pattern in analysis_results['advanced_patterns']:
                    with st.expander(f"Pattern: {pattern['pattern']}"):
                        st.markdown(f"""
                        <div class="grammar-result">
                            <p><span style="color:#3581E3; font-weight:bold; font-family:'Cinzel', serif;">Usage:</span> 
                            <span class="japanese-text">{pattern['usage']}</span></p>
                            
                            <p><span style="color:#8035E3; font-weight:bold; font-family:'Cinzel', serif;">Context:</span> 
                            <span class="japanese-text">{pattern['context']}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 15px; border-left: 3px solid #3581E3; background-color: rgba(53, 129, 227, 0.1); font-family: 'EB Garamond', serif; font-size: 1.1rem;">
                    <span style="color:#3581E3; font-weight:bold; font-family:'Cinzel', serif;">ℹ</span> No advanced patterns detected.
                </div>
                """, unsafe_allow_html=True)

        with tab3:
            if analysis_results.get('custom_patterns'):
                for pattern in analysis_results['custom_patterns']:
                    with st.expander(f"Pattern: {pattern['pattern']}"):
                        st.markdown(f"""
                        <div class="grammar-result">
                            <p><span style="color:#E35335; font-weight:bold; font-family:'Cinzel', serif;">Usage:</span> 
                            <span class="japanese-text">{pattern['usage']}</span></p>
                            
                            <p><span style="color:#8035E3; font-weight:bold; font-family:'Cinzel', serif;">Context:</span> 
                            <span class="japanese-text">{pattern['context']}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 15px; border-left: 3px solid #E35335; background-color: rgba(227, 83, 53, 0.1); font-family: 'EB Garamond', serif; font-size: 1.1rem;">
                    <span style="color:#E35335; font-weight:bold; font-family:'Cinzel', serif;">ℹ</span> No custom patterns detected.
                </div>
                """, unsafe_allow_html=True)

        with tab4:
            if analysis_results['particle_usage']:
                for particle in analysis_results['particle_usage']:
                    with st.expander(f"Particle: {particle['particle']}"):
                        st.markdown(f"""
                        <div class="grammar-result">
                            <p><span style="color:#FFA500; font-weight:bold; font-family:'Cinzel', serif;">Usage:</span> 
                            <span class="japanese-text">{particle['usage']}</span></p>
                            
                            <p><span style="color:#8035E3; font-weight:bold; font-family:'Cinzel', serif;">Context:</span> 
                            <span class="japanese-text">{particle['context']}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 15px; border-left: 3px solid #FFA500; background-color: rgba(255, 165, 0, 0.1); font-family: 'EB Garamond', serif; font-size: 1.1rem;">
                    <span style="color:#FFA500; font-weight:bold; font-family:'Cinzel', serif;">ℹ</span> No particle usage to analyze.
                </div>
                """, unsafe_allow_html=True)

        with tab5:
            if analysis_results['verb_conjugations']:
                for verb in analysis_results['verb_conjugations']:
                    with st.expander(f"Verb: {verb['base_form']}"):
                        # Create context HTML separately
                        context_html = f"<p><span style='color:#8035E3; font-weight:bold; font-family:\"Cinzel\", serif;'>Context:</span> <span class='japanese-text'>{verb['context']}</span></p>" if 'context' in verb else ""
                        
                        # Now build the complete HTML
                        markup = f"""
                        <div class="grammar-result">
                            <p><span style="color:#9370DB; font-weight:bold; font-family:'Cinzel', serif;">Conjugation:</span> 
                            <span class="japanese-text">{verb['conjugation']}</span></p>
                            
                            <p><span style="color:#3581E3; font-weight:bold; font-family:'Cinzel', serif;">Form:</span> 
                            <span class="japanese-text">{verb['form']}</span></p>
                            
                            {context_html}
                        </div>
                        """
                        st.markdown(markup, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 15px; border-left: 3px solid #9370DB; background-color: rgba(147, 112, 219, 0.1); font-family: 'EB Garamond', serif; font-size: 1.1rem;">
                    <span style="color:#9370DB; font-weight:bold; font-family:'Cinzel', serif;">ℹ</span> No verb conjugations to analyze.
                </div>
                """, unsafe_allow_html=True)

elif page == "AI Grammar Analysis":
    st.subheader("AI-Powered Grammar Analysis Tool")
    
    with st.expander("About this Tool", expanded=False):
        st.markdown("""
        This tool uses OpenAI's GPT language model to provide in-depth analysis of Japanese grammar.
        - Get comprehensive grammar explanations
        - Generate practice examples for specific grammar points
        - Receive detailed feedback on your writing
        - Understand honorific and polite speech usage
        """)
    
    # Left column for text input, right column for analysis settings
    col1, col2 = st.columns([3, 1])
    
    with col1:
        ai_input_text = st.text_area(
            "Japanese Text for Analysis", 
            placeholder="Enter Japanese text here for AI analysis...",
            value=st.session_state.ai_input_text,
            height=150
        )
    
    with col2:
        analysis_options = st.multiselect(
            "Analysis Focus",
            [
                "Grammar Errors", 
                "Particle Usage", 
                "Verb Conjugations",
                "Honorific Speech",
                "Naturalness",
                "Formality"
            ],
            default=["Grammar Errors"],
            help="Select what aspects of the text you want the AI to focus on"
        )
        
        difficulty_level = st.selectbox(
            "Practice Examples Difficulty",
            ["初級 (Beginner)", "中級 (Intermediate)", "上級 (Advanced)"],
            index=1
        )
        # Extract just the Japanese part of the difficulty level
        difficulty = difficulty_level.split(" ")[0]
    
    # Analysis button
    analyze_button = st.button("Analyze with AI", type="primary")
    
    if analyze_button and ai_input_text:
        with st.spinner("AI is analyzing your text..."):
            try:
                # Initialize the GPT checker
                gpt_checker = GPTGrammarChecker()
                
                # Perform the analysis
                results = gpt_checker.check_grammar(ai_input_text)
                
                if results.get('error', False):
                    st.error(f"Error in AI analysis: {results.get('message', 'Unknown error')}")
                else:
                    # Display overall assessment with improved visuals
                    if 'overall_assessment' in results:
                        st.subheader("Overall Assessment")
                        cols = st.columns(3)
                        metrics = {
                            "Naturalness": "🌟",
                            "Formality": "👔",
                            "Clarity": "💡"
                        }
                        
                        for i, (metric, icon) in enumerate(metrics.items()):
                            with cols[i]:
                                value = results['overall_assessment'].get(metric.lower(), 0)
                                st.metric(
                                    f"{icon} {metric}",
                                    f"{value}/5",
                                    delta=None
                                )
                                # Add visual rating
                                st.progress(value/5, text="")
                    
                    # Display improved text if available
                    if 'improved_text' in results and results['improved_text'] != ai_input_text:
                        st.subheader("Improved Version")
                        st.success(results['improved_text'])
                        
                        # Add a comparison view
                        with st.expander("Show Side-by-Side Comparison"):
                            comp_col1, comp_col2 = st.columns(2)
                            with comp_col1:
                                st.markdown("**Original Text:**")
                                st.info(ai_input_text)
                            with comp_col2:
                                st.markdown("**Improved Text:**")
                                st.success(results['improved_text'])
                    
                    # Grammar issues section
                    if results.get('grammar_issues'):
                        st.subheader("Grammar Issues")
                        for i, issue in enumerate(results['grammar_issues']):
                            with st.expander(f"Issue {i+1}: {issue.get('error_text', 'Grammar Issue')}"):
                                st.error(f"**Error:** {issue.get('error_text', '')}")
                                st.success(f"**Correction:** {issue.get('correct_text', '')}")
                                st.info(f"**Explanation:** {issue.get('explanation', '')}")
                                st.write(f"**Rule:** {issue.get('rule', '')}")
                                
                                # Add a button to get more detailed explanation
                                if st.button(f"Get Detailed Explanation for Issue {i+1}"):
                                    with st.spinner("Generating detailed explanation..."):
                                        explanation = gpt_checker.get_detailed_explanation(
                                            issue.get('rule', ''), 
                                            ai_input_text
                                        )
                                        st.markdown("### Detailed Explanation")
                                        st.markdown(explanation)
                                
                                # Add a button to generate practice examples
                                if st.button(f"Generate Practice Examples for Issue {i+1}"):
                                    with st.spinner("Generating practice examples..."):
                                        examples = gpt_checker.generate_practice_examples(
                                            issue.get('rule', ''),
                                            difficulty
                                        )
                                        
                                        st.markdown("### Practice Examples")
                                        for j, example in enumerate(examples):
                                            st.markdown(f"**Example {j+1}:** {example.get('question', '')}")
                                            options = example.get('options', [])
                                            correct = example.get('correct_answer', '')
                                            
                                            # Display options with correct one highlighted
                                            for option in options:
                                                if option == correct:
                                                    st.success(f"✓ {option}")
                                                else:
                                                    st.write(f"○ {option}")
                                                    
                                            st.info(f"**Explanation:** {example.get('explanation', '')}")
                                            st.markdown("---")
                    else:
                        st.success("No grammar issues found! Your text looks good grammatically.")
                    
                    # Particle usage analysis
                    if results.get('particle_usage'):
                        st.subheader("Particle Usage Analysis")
                        for particle in results['particle_usage']:
                            is_correct = particle.get('correct', False)
                            with st.expander(
                                f"{'✓' if is_correct else '✗'} Particle: {particle.get('particle', '')}"
                            ):
                                st.write(f"**Usage Context:** {particle.get('usage_context', '')}")
                                if is_correct:
                                    st.success("This particle is used correctly.")
                                else:
                                    st.error("This particle is used incorrectly.")
                                    st.info(f"**Suggestion:** {particle.get('suggestion', '')}")
                    
                    # Verb conjugation analysis
                    if results.get('verb_conjugations'):
                        st.subheader("Verb Conjugation Analysis")
                        for verb in results['verb_conjugations']:
                            is_correct = verb.get('correct', False)
                            with st.expander(
                                f"{'✓' if is_correct else '✗'} Verb: {verb.get('verb', '')}"
                            ):
                                st.write(f"**Form:** {verb.get('form', '')}")
                                if is_correct:
                                    st.success("This verb is conjugated correctly.")
                                else:
                                    st.error("This verb is conjugated incorrectly.")
                                    st.info(f"**Suggestion:** {verb.get('suggestion', '')}")
                    
                    # Honorific/polite speech analysis
                    if results.get('honorific_polite_speech'):
                        st.subheader("Honorific & Polite Speech Analysis")
                        for expression in results['honorific_polite_speech']:
                            with st.expander(f"Expression: {expression.get('expression', '')}"):
                                st.write(f"**Type:** {expression.get('type', '')}")
                                st.write(f"**Formality Level:** {expression.get('level', '')}")
                                if expression.get('alternative', ''):
                                    st.info(f"**Alternative:** {expression.get('alternative', '')}")
                    
                    # Grammar practice section
                    st.subheader("Generate Practice Examples")
                    grammar_point = st.text_input(
                        "Enter a specific grammar point to practice",
                        placeholder="e.g., て-form, potential form, causative form, etc."
                    )
                    
                    if grammar_point:
                        if st.button("Generate Practice Examples"):
                            with st.spinner("Generating practice examples..."):
                                examples = gpt_checker.generate_practice_examples(
                                    grammar_point,
                                    difficulty
                                )
                                
                                st.markdown("### Practice Examples")
                                for j, example in enumerate(examples):
                                    with st.expander(f"Example {j+1}"):
                                        st.markdown(f"**Question:** {example.get('question', '')}")
                                        options = example.get('options', [])
                                        correct = example.get('correct_answer', '')
                                        
                                        # Display options with correct one hidden until revealed
                                        show_answer = st.checkbox(f"Show answer for Example {j+1}")
                                        
                                        for option in options:
                                            if option == correct and show_answer:
                                                st.success(f"✓ {option}")
                                            else:
                                                st.write(f"○ {option}")
                                                
                                        if show_answer:
                                            st.info(f"**Explanation:** {example.get('explanation', '')}")
            
            except Exception as e:
                st.error(f"An error occurred during AI analysis: {str(e)}")
                st.info("Please try again with a different text or check your OpenAI API key.")
    
    else:
        if not ai_input_text and analyze_button:
            st.warning("Please enter some Japanese text to analyze.")
        
        # Show some example texts that the user can use
        with st.expander("Example Texts to Try"):
            examples = [
                ("Basic greeting with particle mistake", "おはようございます。わたしは田中です。日本のから来ました。"),
                ("Incorrect verb conjugation", "昨日、映画を見られます。とても面白かったです。"),
                ("Incorrect usage of polite forms", "先生が来る。質問があります。"),
                ("Mixed politeness levels", "こんにちは！僕は大学生だ。何を勉強していますか？")
            ]
            
            for title, example in examples:
                if st.button(f"Try: {title}"):
                    st.session_state.ai_input_text = example
                    st.rerun()

elif page == "Progress Dashboard":
    st.subheader("Your Learning Progress")

    with get_database() as db:
        user_progress = UserProgress.get_or_create(db, st.session_state.session_id)

        # Streak information with animated chart
        st.write("### Learning Streak 🔥")
        streak_chart = create_streak_chart(
            user_progress.current_streak,
            user_progress.longest_streak
        )
        st.plotly_chart(streak_chart, use_container_width=True)

        # Display streak motivation message
        if user_progress.current_streak > 0:
            st.success(f"Keep going! You've been learning for {user_progress.current_streak} consecutive days!")

            # Calculate next milestone
            next_milestone = ((user_progress.current_streak // 5) + 1) * 5
            days_to_milestone = next_milestone - user_progress.current_streak
            if days_to_milestone > 0:
                st.info(f"🎯 {days_to_milestone} more days until your next milestone! ({next_milestone} days)")
        else:
            st.warning("Start your learning streak today! Practice daily to build your streak. 🎯")

        # Last activity
        st.write(f"Last practice: {user_progress.last_check_date.strftime('%Y-%m-%d')}")

        # Overall stats
        st.write("### Overall Progress")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Checks", user_progress.total_checks)
        with col2:
            st.metric("Correct Usage", user_progress.total_correct)
        with col3:
            accuracy = f"{user_progress.average_accuracy * 100:.1f}%"
            st.metric("Average Accuracy", accuracy)

        # Mastery radar chart
        st.subheader("Mastery Overview")
        mastery_chart = create_mastery_radar(
            user_progress.particle_mastery,
            user_progress.verb_mastery,
            user_progress.pattern_mastery
        )
        st.plotly_chart(mastery_chart, use_container_width=True)

        # Detailed mastery breakdown
        with st.expander("Detailed Mastery Breakdown", expanded=False):
            # Particle mastery
            st.write("**Particle Usage Mastery**")
            if user_progress.particle_mastery:
                for particle, stats in user_progress.particle_mastery.items():
                    mastery = (stats['correct'] / stats['count']) * 100 if stats['count'] > 0 else 0
                    st.progress(mastery / 100, text=f"{particle}: {mastery:.1f}%")
            else:
                st.info("No particle usage data yet")

            # Verb mastery
            st.write("**Verb Conjugation Mastery**")
            if user_progress.verb_mastery:
                for conjugation, stats in user_progress.verb_mastery.items():
                    mastery = (stats['correct'] / stats['count']) * 100 if stats['count'] > 0 else 0
                    st.progress(mastery / 100, text=f"{conjugation}: {mastery:.1f}%")
            else:
                st.info("No verb conjugation data yet")

            # Pattern mastery
            st.write("**Grammar Pattern Mastery**")
            if user_progress.pattern_mastery:
                for pattern, stats in user_progress.pattern_mastery.items():
                    mastery = (stats['correct'] / stats['count']) * 100 if stats['count'] > 0 else 0
                    st.progress(mastery / 100, text=f"{pattern}: {mastery:.1f}%")
            else:
                st.info("No grammar pattern data yet")

        # Achievements section with animated progress
        st.subheader("🏆 日本文化の徽章 (Japanese Cultural Badges)")

        if user_progress.achievements:
            # First tab shows the traditional achievement progress
            tab1, tab2 = st.tabs(["Achievement Progress", "Japanese Cultural Badges"])
            
            with tab1:
                # Achievement progress chart
                achievement_chart = create_achievement_progress(user_progress.achievements)
                if achievement_chart:
                    st.plotly_chart(achievement_chart, use_container_width=True)
                    
                # Calculate total achievements
                total_achievements = sum(len(achievements) for achievements in user_progress.achievements.values())
                st.info(f"Total Achievements Earned: {total_achievements}")

            with tab2:
                # Japanese cultural badge progress visualization
                cultural_badge_chart = create_japanese_cultural_badge_progress(user_progress.achievements)
                if cultural_badge_chart:
                    st.plotly_chart(cultural_badge_chart, use_container_width=True)
                
                # Categorized badges display
                badge_categories = {
                    "streak": "🔥 継続学習 (Continuous Learning)",
                    "accuracy": "🎯 正確性 (Accuracy)",
                    "practice": "📚 練習量 (Practice Volume)",
                    "particle_mastery": "🔤 助詞の習得 (Particle Mastery)",
                    "verb_mastery": "📝 動詞の習得 (Verb Mastery)",
                    "pattern_mastery": "📖 文型の習得 (Grammar Pattern Mastery)"
                }
                
                # For each category, display earned badges and next badge
                for cat_id, cat_name in badge_categories.items():
                    with st.expander(cat_name, expanded=False):
                        earned_badges = []
                        if cat_id == "streak":
                            earned_badges = user_progress.achievements.get('streak', [])
                        elif cat_id == "accuracy":
                            earned_badges = user_progress.achievements.get('accuracy', [])
                        elif cat_id == "practice":
                            earned_badges = user_progress.achievements.get('practice', [])
                        elif cat_id == "particle_mastery" or cat_id == "verb_mastery" or cat_id == "pattern_mastery":
                            prefix = cat_id.split('_')[0]
                            earned_badges = [badge for badge in user_progress.achievements.get('mastery', []) 
                                             if badge.startswith(prefix)]
                        
                        # Display earned badges
                        if earned_badges:
                            for badge_id in earned_badges:
                                st.markdown(create_japanese_badge_card(badge_id), unsafe_allow_html=True)
                                
                            # Show progress toward next badge
                            st.markdown("#### Next Badge to Earn")
                            st.markdown(create_next_badge_card(cat_id, earned_badges), unsafe_allow_html=True)
                        else:
                            st.markdown("#### Begin Your Journey")
                            st.markdown(create_next_badge_card(cat_id, []), unsafe_allow_html=True)
            
            # Traditional achievement list in an expander
            with st.expander("Achievement List", expanded=False):
                # Streak Achievements
                st.write("**Streak Achievements**")
                for achievement in user_progress.achievements.get('streak', []):
                    days = achievement.split('_')[1]
                    st.success(f"🔥 {days}-Day Streak Champion!")

                # Accuracy Achievements
                st.write("**Accuracy Achievements**")
                for achievement in user_progress.achievements.get('accuracy', []):
                    accuracy = achievement.split('_')[1]
                    st.success(f"🎯 {accuracy}% Accuracy Master!")

                # Practice Achievements
                st.write("**Practice Achievements**")
                for achievement in user_progress.achievements.get('practice', []):
                    count = achievement.split('_')[1]
                    st.success(f"📚 Completed {count} Grammar Checks!")

                # Mastery Achievements
                st.write("**Mastery Achievements**")
                for achievement in user_progress.achievements.get('mastery', []):
                    category, _, level = achievement.split('_')
                    icon = "🔤" if category == "particle" else "📝" if category == "verb" else "📖"
                    st.success(f"{icon} {category.title()} Mastery Level {level}%")
        else:
            # Show introduction to Japanese cultural badges
            st.info("Start practicing to earn Japanese cultural badges! 🏮")
            st.markdown("""
            <div style="
                border: 2px solid #DAA520; 
                border-radius: 10px; 
                padding: 15px; 
                margin: 10px 0; 
                background: linear-gradient(135deg, rgba(255,252,245,0.9) 0%, rgba(248,243,230,0.9) 100%);
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                font-family: serif;
            ">
                <h3 style="
                    color: #D73E02; 
                    font-family: serif;
                    font-size: 1.4rem;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                    margin-top: 0;
                ">🏮 日本文化の徽章について / About Japanese Cultural Badges 🏮</h3>
                <p>Our achievement system is inspired by Japanese cultural elements, traditions, and concepts.</p>
                <ul>
                    <li><b>継続学習 (Continuous Learning)</b>: Badges inspired by Japanese moon viewing traditions and significant numbers in culture.</li>
                    <li><b>正確性 (Accuracy)</b>: Badges based on traditional Japanese craftsmanship ranks and apprenticeship systems.</li>
                    <li><b>練習量 (Practice Volume)</b>: Badges referencing famous Japanese collections and cultural numeric milestones.</li>
                    <li><b>助詞の習得 (Particle Mastery)</b>: Traditional Japanese ranking system applied to your particle mastery.</li>
                    <li><b>動詞の習得 (Verb Mastery)</b>: Progress through traditional Japanese craftsman roles as you master verbs.</li>
                    <li><b>文型の習得 (Grammar Pattern Mastery)</b>: Zen-inspired journey from pattern learning to creative pattern breaking.</li>
                </ul>
                <p>Each badge includes cultural context to help you appreciate Japanese language learning as part of a broader cultural experience.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Preview of badges to earn
            st.markdown("### Preview of Badges to Earn")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(create_japanese_badge_card("streak_3"), unsafe_allow_html=True)
            with col2:
                st.markdown(create_japanese_badge_card("accuracy_60"), unsafe_allow_html=True)

elif page == "Language Companion":
    st.subheader("AI 言語学習パートナー / AI Language Learning Companion")
    
    # Initialize the AI companion
    if 'ai_companion' not in st.session_state:
        st.session_state.ai_companion = AILanguageCompanion(st.session_state.session_id)
    
    # Add decorative Japanese-styled header
    st.markdown("""
    <div style="
        text-align: center;
        padding: 20px 0;
        margin-bottom: 20px;
        background: linear-gradient(90deg, rgba(255,215,0,0.1) 0%, rgba(255,215,0,0.2) 50%, rgba(255,215,0,0.1) 100%);
        border-radius: 5px;
        font-family: 'Noto Serif JP', serif;
    ">
        <h2 style="
            margin: 0;
            color: #333;
            font-family: 'Cinzel', 'Noto Serif JP', serif;
            letter-spacing: 0.05em;
        ">
            会話で学ぶ日本語
        </h2>
        <p style="
            margin: 5px 0 0 0;
            font-style: italic;
            color: #666;
        ">
            Learn Japanese Through Conversation
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different companion features
    tab1, tab2, tab3 = st.tabs(["会話 / Chat", "学習プロフィール / Learning Profile", "設定 / Settings"])
    
    with tab1:
        # Render the chat interface
        render_chat_interface(st.session_state.ai_companion)
    
    with tab2:
        # Render the user's learning profile and companion dashboard
        render_companion_dashboard(st.session_state.ai_companion)
        
        # Conversation history management
        render_conversation_history(st.session_state.ai_companion)
    
    with tab3:
        st.markdown("### 設定 / Settings")
        
        st.markdown("""
        <div style="
            padding: 15px;
            border-radius: 10px;
            background-color: rgba(255, 252, 245, 0.8);
            margin-bottom: 20px;
            border: 1px solid #ddd;
            font-family: 'EB Garamond', 'Noto Serif JP', serif;
        ">
            <p style="margin-top: 0;">
                Your AI language companion helps you practice Japanese through natural conversation.
                Customize your experience with the settings below.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display OpenAI API connection status
        if st.session_state.ai_companion.openai_client:
            api_status = "Connected"
            status_color = "#35AF35"
        else:
            api_status = "Disconnected"
            status_color = "#E35335"
            
        st.markdown(f"""
        <div style="
            padding: 10px 15px;
            border-radius: 5px;
            background-color: rgba({status_color.replace('#', '')}, 0.1);
            margin-bottom: 10px;
            border-left: 3px solid {status_color};
        ">
            <span style="color: {status_color}; font-weight: bold;">API Status:</span> {api_status}
        </div>
        """, unsafe_allow_html=True)
        
        # Additional settings could be added here in the future
        st.info("Additional settings will be available in future updates.")
        
        # Provide usage tips
        with st.expander("Usage Tips", expanded=True):
            st.markdown("""
            ### How to get the most from your language companion:
            
            1. **Choose the right personality** for your learning style
            2. **Practice regularly** to build vocabulary and grammar skills
            3. **Ask specific questions** about grammar points you're struggling with
            4. **Try different conversation topics** to expand your vocabulary
            5. **Use the translation tool** when you encounter unfamiliar words
            6. **Generate practice exercises** tailored to your level
            7. **Review your conversation history** to reinforce learning
            
            Your companion adapts to your level based on your progress in the app!
            """)
            
        # Credits and information
        st.markdown("""
        <div style="
            font-size: 0.8rem;
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-family: 'EB Garamond', serif;
        ">
            Powered by OpenAI's GPT-4o language model.<br>
            Your conversations help personalize your learning experience.
        </div>
        """, unsafe_allow_html=True)

elif page == "Custom Rules":
    st.subheader("Custom Grammar Rules")

    # Add new rule section
    with st.expander("Add New Rule", expanded=True):
        with st.form("new_rule_form"):
            name = st.text_input("Rule Name", placeholder="e.g., Polite Request Form")
            pattern = st.text_input("Pattern", placeholder="e.g., ～てください")
            check_pattern = st.text_input("Check Pattern (Regex)", placeholder="e.g., て[くだ|下だ]さい")
            correct_pattern = st.text_input("Correct Pattern (Regex)", placeholder="e.g., てください")
            explanation = st.text_area("Explanation", placeholder="e.g., Used for making polite requests")
            example = st.text_input("Example", placeholder="e.g., 見てください (Please look)")
            error_description = st.text_area("Error Description", placeholder="e.g., Incorrect formation of てください")
            suggestion = st.text_area("Suggestion", placeholder="e.g., Use てください for polite requests")

            # Context rules selection
            context_rules = st.multiselect(
                "Context Rules",
                ["must_follow_te_form", "end_of_sentence", "must_follow_verb_or_adjective", "requires_contrasting_clause"],
                help="Select applicable context rules for this pattern"
            )

            submitted = st.form_submit_button("Add Rule")

            if submitted and name and pattern and check_pattern and correct_pattern:
                with get_database() as db:
                    rule_data = {
                        "name": name,
                        "pattern": pattern,
                        "check_pattern": check_pattern,
                        "correct_pattern": correct_pattern,
                        "explanation": explanation,
                        "example": example,
                        "error_description": error_description,
                        "suggestion": suggestion,
                        "context_rules": context_rules
                    }
                    CustomGrammarRule.create(db, rule_data)
                    st.success("Rule added successfully!")
                    checker.load_custom_rules()  # Refresh custom rules

    # List existing rules
    st.subheader("Existing Custom Rules")
    with get_database() as db:
        custom_rules = CustomGrammarRule.get_active_rules(db)
        for rule in custom_rules:
            with st.expander(f"Rule: {rule.name}"):
                st.write(f"**Pattern:** {rule.pattern}")
                st.write(f"**Explanation:** {rule.explanation}")
                st.write(f"**Example:** {rule.example}")
                if rule.context_rules:
                    st.write("**Context Rules:**")
                    for context_rule in rule.context_rules:
                        st.write(f"- {context_rule}")

                # Delete button
                if st.button(f"Delete Rule {rule.id}"):
                    CustomGrammarRule.delete_rule(db, rule.id)
                    st.success("Rule deleted successfully!")
                    st.rerun()

elif page == "Self Assessment":
    st.subheader("Japanese Language Self-Assessment")

    # Initialize assessor
    assessor = LanguageLevelAssessor()

    # Check if user has a recent assessment
    with get_database() as db:
        latest_assessment = LanguageAssessment.get_latest_assessment(
            db, st.session_state.session_id
        )

        if latest_assessment:
            last_assessment_date = latest_assessment.assessment_date.strftime('%Y-%m-%d')
            st.info(f"Your last assessment was on {last_assessment_date}")

            # Show previous results
            with st.expander("View Previous Assessment Results"):
                st.write("**Self-Rated Level:**", latest_assessment.self_rated_level)
                st.write("**Recommended Level:**", latest_assessment.recommended_level)

                st.write("**Strong Areas:**")
                for area in latest_assessment.strong_areas:
                    st.success(f"- {area}")

                st.write("**Areas for Improvement:**")
                for area in latest_assessment.weak_areas:
                    st.warning(f"- {area}")

    # Start new assessment button
    start_new = st.button("Start New Assessment")

    if start_new or not latest_assessment:
        st.write("### Step 1: Self-Rate Your Level")
        self_rated_level = st.radio(
            "How would you rate your current Japanese level?",
            ["beginner", "intermediate", "advanced"]
        )

        st.write("### Step 2: Grammar Comfort Assessment")
        st.write("Rate your comfort level with the following grammar patterns:")

        comfort_ratings = {}
        for category, patterns in assessor.grammar_categories.items():
            st.write(f"**{category.title()}**")
            comfort_ratings[category] = st.slider(
                f"How comfortable are you with {category}?",
                0, 5, 2,
                help=f"Patterns include: {', '.join(patterns)}"
            )

        st.write("### Step 3: Quick Assessment Test")
        with st.form("assessment_test"):
            st.write("Answer these sample questions:")

            test_answers = {}
            # Sample questions based on user's self-rated level
            if self_rated_level == "beginner":
                test_answers['q1'] = st.radio(
                    "1. Which particle marks the topic of a sentence?",
                    ["は", "が", "を", "に"]
                ) == "は"
                test_answers['q2'] = st.radio(
                    "2. What is the polite form of 食べる (to eat)?",
                    ["食べます", "食べられる", "食べている", "食べた"]
                ) == "食べます"
            elif self_rated_level == "intermediate":
                test_answers['q1'] = st.radio(
                    "1. Which form expresses 'if' condition?",
                    ["〜たら", "〜ている", "〜ました", "〜ます"]
                ) == "〜たら"
                test_answers['q2'] = st.radio(
                    "2. What is the te-form of 行く?",
                    ["行って", "行きて", "行った", "行きます"]
                ) == "行って"
            else:  # advanced
                test_answers['q1'] = st.radio(
                    "1. Which is the humble form of 見る?",
                    ["拝見する", "ご覧になる", "見られる", "見ます"]
                ) == "拝見する"
                test_answers['q2'] = st.radio(
                    "2. What is the causative-passive form of 食べる?",
                    ["食べさせられる", "食べられる", "食べさせる", "食べている"]
                ) == "食べさせられる"

            submitted = st.form_submit_button("Submit Assessment")

            if submitted:
                # Calculate results
                comfort_level = assessor.calculate_comfort_level(comfort_ratings)
                strong_areas, weak_areas = assessor.analyze_strengths_weaknesses(comfort_ratings)
                test_results = assessor.evaluate_test_results(test_answers)
                recommendations = assessor.get_recommended_materials(comfort_level, weak_areas)

                # Store assessment results
                assessment_data = {
                    'self_rated_level': self_rated_level,
                    'grammar_comfort': comfort_ratings,
                    'test_results': test_results,
                    'recommended_level': test_results['mastery_level'],
                    'weak_areas': weak_areas,
                    'strong_areas': strong_areas
                }

                with get_database() as db:
                    LanguageAssessment.create(db, st.session_state.session_id, assessment_data)

                # Display results
                st.success("Assessment Complete!")

                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Your Results**")
                    st.write(f"Self-Rated Level: {self_rated_level}")
                    st.write(f"Test Score: {test_results['score']}%")
                    st.write(f"Recommended Level: {test_results['mastery_level']}")

                with col2:
                    st.write("**Recommendations**")
                    for point in recommendations['grammar_points']:
                        st.info(point)

                st.write("**Strong Areas:**")
                for area in strong_areas:
                    st.success(f"- {area}")

                st.write("**Areas for Improvement:**")
                for area in weak_areas:
                    st.warning(f"- {area}")

                if recommendations['practice_areas']:
                    st.write("**Suggested Practice:**")
                    for practice in recommendations['practice_areas']:
                        st.info(practice)


elif page == "Idiom Translator":
    st.subheader("Japanese Idiom Translator")

    with get_database() as db:
        translator = IdiomTranslator(db)

        # Search interface
        search_query = st.text_input(
            "Search for idioms",
            placeholder="Enter Japanese or English text..."
        )

        # Text analysis interface
        text_input = st.text_area(
            "Or enter text to find idioms",
            placeholder="Enter Japanese text to find idioms..."
        )

        col1, col2 = st.columns(2)

        with col1:
            if search_query:
                st.write("### Search Results")
                results = translator.search_idioms(search_query)
                if results:
                    for idiom in results:
                        with st.expander(f"🎯 {idiom['japanese']}"):
                            st.write("**Literal Meaning:**", idiom['literal'])
                            st.write("**English Equivalent:**", idiom['english'])
                            st.write("**Explanation:**", idiom['explanation'])
                            st.write("**Example Usage:**", idiom['example'])

                            # Add mnemonic device section
                            with st.expander("🧠 Memory Aid", expanded=True):
                                mnemonic = idiom['mnemonic']
                                if mnemonic['sound_hints']:
                                    st.write("**Sound Hints:**")
                                    for hint in mnemonic['sound_hints']:
                                        st.write(f"- '{hint['japanese']}' sounds like '{hint['english']}'")

                                if mnemonic['visual_cues']:
                                    st.write("**Visual Hints:**")
                                    for cue in mnemonic['visual_cues']:
                                        st.write(f"- {cue}")

                                st.write("**Memory Story:**")
                                st.info(mnemonic['mnemonic_story'])

                                st.write("**Practice Tip:**")
                                st.success(mnemonic['practice_tip'])

                else:
                    st.info("No idioms found matching your search.")

        with col2:
            if text_input:
                st.write("### Found Idioms")
                found_idioms = translator.analyze_text_for_idioms(text_input)
                if found_idioms:
                    for idiom in found_idioms:
                        with st.expander(f"📍 {idiom['japanese']}"):
                            st.write("**English Equivalent:**", idiom['english'])
                            st.write("**Explanation:**", idiom['explanation'])
                else:
                    st.info("No idioms found in the text.")

        # Add new idiom interface for administrators
        with st.expander("Add New Idiom", expanded=False):
            with st.form("new_idiom_form"):
                japanese_idiom = st.text_input("Japanese Idiom")
                literal_meaning = st.text_input("Literal Meaning")
                english_equivalent = st.text_input("English Equivalent")
                explanation = st.text_area("Explanation")
                usage_example = st.text_area("Usage Example")
                tags = st.text_input("Tags (comma-separated)")

                submitted = st.form_submit_button("Add Idiom")

                if submitted and japanese_idiom and english_equivalent:
                    idiom_data = {
                        "japanese_idiom": japanese_idiom,
                        "literal_meaning": literal_meaning,
                        "english_equivalent": english_equivalent,
                        "explanation": explanation,
                        "usage_example": usage_example,
                        "tags": [tag.strip() for tag in tags.split(",")] if tags else []
                    }
                    translator.add_idiom(idiom_data)
                    st.success("Idiom added successfully!")
                    st.rerun()

elif page == "Pronunciation Practice":
    st.subheader("Pronunciation Practice")

    # Initialize pronunciation analyzer
    from pronunciation_feedback import PronunciationAnalyzer
    analyzer = PronunciationAnalyzer()

    st.write("""
    ### Practice Your Japanese Pronunciation
    Record yourself speaking Japanese and get AI-powered feedback on your pronunciation.
    """)

    # Text input for target phrase
    target_phrase = st.text_input(
        "Enter the Japanese phrase you want to practice:",
        placeholder="例：こんにちは"
    )

    # Recording interface
    if target_phrase:
        if st.button("🎙️ Start Recording"):
            with st.spinner("Recording... Speak now!"):
                try:
                    # Record audio
                    audio, sample_rate = analyzer.record_audio()
                    audio_path = analyzer.save_audio(audio, sample_rate)

                    # Analyze pronunciation
                    results = analyzer.analyze_pronunciation(audio_path, target_phrase)

                    # Display results
                    st.success("Recording completed!")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Pronunciation Score",
                            f"{results['pronunciation_score']:.1f}%"
                        )
                    with col2:
                        st.write("**Detected Text:**")
                        st.write(results['transcribed_text'])

                    st.info(results['feedback'])

                    # Cleanup
                    analyzer.cleanup(audio_path)
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    st.warning("Please make sure your microphone is connected and try again.")
    else:
        st.info("Enter a Japanese phrase above to start practicing pronunciation.")

    # Add pronunciation tips
    with st.expander("📚 Pronunciation Tips"):
        st.write("""
        - Speak clearly and at a natural pace
        - Pay attention to pitch accent
        - Practice with short phrases first
        - Record yourself multiple times to track improvement
        - Listen to native speakers for reference
        """)

elif page == "Lessons":
    # Lessons page with mood and difficulty emoji selectors
    st.title("Japanese Lessons")
    
    # Initialize mood/difficulty selector and lesson manager
    with get_database() as db:
        mood_selector = MoodDifficultySelector(st.session_state.session_id)
        lesson_manager = LessonManager(db, st.session_state.session_id)
    
    # Check if we're viewing a specific lesson
    if "selected_lesson_id" in st.session_state:
        # Get the selected mood emoji (if any)
        selected_mood = st.session_state.get("selected_mood", None)
        
        # Get the selected difficulty level (if any)
        selected_difficulty = st.session_state.get("selected_difficulty", None)
        
        # Display the selected lesson
        with get_database() as db:
            lesson_manager = LessonManager(db, st.session_state.session_id)
            lesson_manager.display_lesson_content(
                st.session_state["selected_lesson_id"],
                mood_emoji=selected_mood,
                difficulty_emoji=selected_difficulty
            )
    else:
        # Split into two tabs - one for lessons and one for mood analysis
        tab1, tab2 = st.tabs(["Lessons", "Mood Tracker"])
        
        with tab1:
            # Display mood selector at the top
            st.markdown("### How are you feeling today?")
            st.write("Your mood affects how we'll recommend lessons to you.")
            
            selected_mood = mood_selector.display_mood_selector()
            
            # Display difficulty selector
            st.markdown("### Choose your preferred difficulty")
            st.write("This helps us tailor lessons to your comfort level.")
            
            selected_difficulty = mood_selector.display_difficulty_selector()
            
            # Insert a divider
            st.markdown("---")
            
            # Check if we have enough sample lessons, if not, create some
            with get_database() as db:
                lesson_count = len(lesson_manager.get_all_lessons())
                
                # If no lessons exist, create sample lessons for each difficulty/category
                if lesson_count == 0:
                    st.info("Setting up sample lessons for demonstration...")
                    
                    # Create sample lessons for each difficulty and category
                    difficulties = ["Beginner", "Elementary", "Intermediate", "Advanced", "Native-like"]
                    categories = ["grammar", "vocabulary", "reading", "listening", "speaking", "writing", "culture"]
                    
                    for difficulty in difficulties:
                        # Create one lesson per category for this difficulty
                        for category in categories:
                            # Generate sample lesson content
                            lesson_data = LessonManager.generate_sample_lesson(difficulty, category)
                            
                            # Create the lesson in the database
                            lesson_manager.create_lesson(lesson_data)
                    
                    st.success(f"Created {len(difficulties) * len(categories)} sample lessons!")
                
                # Display lesson catalog with any selected filters
                difficulty_filter = None
                if selected_difficulty:
                    difficulty_map = {
                        "🌱": "Beginner",
                        "🌿": "Elementary", 
                        "🌲": "Intermediate", 
                        "🏔️": "Advanced", 
                        "🏯": "Native-like"
                    }
                    difficulty_filter = difficulty_map.get(selected_difficulty)
                
                lesson_manager.display_lesson_catalog(difficulty_filter=difficulty_filter)
        
        with tab2:
            # Display mood analysis
            mood_selector.display_mood_analysis()
            
            # Get user's lesson history
            with get_database() as db:
                lesson_manager = LessonManager(db, st.session_state.session_id)
                lesson_history = lesson_manager.get_user_lesson_history()
                
                # Display lesson history if available
                if lesson_history:
                    st.subheader("Your Lesson History")
                    
                    for completion in lesson_history:
                        with st.expander(f"Lesson: {completion.lesson.title} - {completion.completed_at.strftime('%Y-%m-%d %H:%M')}"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                if completion.mood_before:
                                    st.write(f"Mood before: {completion.mood_before}")
                                if completion.mood_after:
                                    st.write(f"Mood after: {completion.mood_after}")
                            
                            with col2:
                                if completion.difficulty_selected:
                                    st.write(f"Difficulty: {completion.difficulty_selected}")
                                if completion.satisfaction_rating:
                                    st.write(f"Rating: {'⭐' * completion.satisfaction_rating}")
                            
                            with col3:
                                if completion.notes:
                                    st.write("Notes:")
                                    st.write(completion.notes)
                else:
                    st.info("You haven't completed any lessons yet. Start learning to track your progress!")

elif page == "Translation Memory Bank":
    render_translation_memory_ui()

# Recent checks section in sidebar
st.sidebar.title("Recent Checks")
with get_database() as db:
    recent_checks = GrammarCheck.get_recent_checks(db)
    for check in recent_checks:
        with st.sidebar.expander(f"Check {check.created_at.strftime('%Y-%m-%d %H:%M')}"):
            st.write("**Input Text:**")
            st.write(check.input_text)
            st.write("**Found Issues:**", len(check.grammar_issues))
            st.write("**Advanced Patterns:**", len(check.advanced_patterns))
            st.write("**Particles Analyzed:**", len(check.particle_usage))
            st.write("**Verbs Analyzed:**", len(check.verb_conjugations))