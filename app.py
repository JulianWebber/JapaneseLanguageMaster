import streamlit as st
import json
from grammar_checker import GrammarChecker
from utils import load_grammar_rules, analyze_text
from database import get_db, GrammarCheck, CustomGrammarRule, UserProgress, LanguageAssessment
from contextlib import contextmanager
import uuid
from visualizations import (
    create_streak_chart,
    create_mastery_radar,
    create_achievement_progress
)
from assessment import LanguageLevelAssessor
from idiom_translator import IdiomTranslator # Added import

# Initialize the application
st.set_page_config(page_title="Japanese Grammar Checker", layout="wide")

# Load grammar rules
grammar_rules = load_grammar_rules()

@contextmanager
def get_database():
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

# Initialize session state for user tracking
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Initialize the checker with database connection
with get_database() as db:
    checker = GrammarChecker(grammar_rules, db)

st.title("Japanese Grammar Checker")

# Sidebar navigation
page = st.sidebar.radio( # Updated navigation
    "Navigation",
    ["Grammar Check", "Progress Dashboard", "Custom Rules", "Self Assessment", "Idiom Translator"]
)

if page == "Grammar Check":
    # Main input section
    st.subheader("Enter Japanese Text")
    input_text = st.text_area("Japanese Text", placeholder="Enter Japanese text here...", key="input_text")

    if input_text:
        # Analysis section
        st.subheader("Grammar Analysis")

        # Perform grammar check and update progress
        with get_database() as db:
            checker.load_custom_rules()  # Refresh custom rules
            analysis_results = checker.check_grammar(input_text)

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
                        st.error(f"**Description:** {issue['description']}")
                        st.info(f"**Suggestion:** {issue['suggestion']}")
                        if 'example' in issue:
                            st.success(f"**Example:** {issue['example']}")
                        if 'context' in issue:
                            st.write(f"**Context:** {issue['context']}")
                        if issue.get('custom_rule'):
                            st.info("_(Custom Rule)_")
            else:
                st.success("No grammar issues found!")

        with tab2:
            if analysis_results.get('advanced_patterns'):
                for pattern in analysis_results['advanced_patterns']:
                    with st.expander(f"Pattern: {pattern['pattern']}"):
                        st.write(f"**Usage:** {pattern['usage']}")
                        st.write(f"**Context:** {pattern['context']}")
            else:
                st.info("No advanced patterns detected.")

        with tab3:
            if analysis_results.get('custom_patterns'):
                for pattern in analysis_results['custom_patterns']:
                    with st.expander(f"Pattern: {pattern['pattern']}"):
                        st.write(f"**Usage:** {pattern['usage']}")
                        st.write(f"**Context:** {pattern['context']}")
            else:
                st.info("No custom patterns detected.")

        with tab4:
            if analysis_results['particle_usage']:
                for particle in analysis_results['particle_usage']:
                    with st.expander(f"Particle: {particle['particle']}"):
                        st.write(f"**Usage:** {particle['usage']}")
                        st.write(f"**Context:** {particle['context']}")
            else:
                st.info("No particle usage to analyze.")

        with tab5:
            if analysis_results['verb_conjugations']:
                for verb in analysis_results['verb_conjugations']:
                    with st.expander(f"Verb: {verb['base_form']}"):
                        st.write(f"**Conjugation:** {verb['conjugation']}")
                        st.write(f"**Form:** {verb['form']}")
                        if 'context' in verb:
                            st.write(f"**Context:** {verb['context']}")
            else:
                st.info("No verb conjugations to analyze.")

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
        st.subheader("🏆 Achievements")

        if user_progress.achievements:
            # Achievement progress chart
            achievement_chart = create_achievement_progress(user_progress.achievements)
            if achievement_chart:
                st.plotly_chart(achievement_chart, use_container_width=True)

            with st.expander("Achievement Details", expanded=True):
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

            # Calculate total achievements
            total_achievements = sum(len(achievements) for achievements in user_progress.achievements.values())
            st.info(f"Total Achievements Earned: {total_achievements}")
        else:
            st.info("Start practicing to earn achievements! 🌟")
            st.write("Available achievements:")
            st.write("- 🔥 Streak achievements (3, 7, 14, 30, 60, 90 days)")
            st.write("- 🎯 Accuracy achievements (60%, 70%, 80%, 90%, 95%)")
            st.write("- 📚 Practice count achievements (10, 50, 100, 500, 1000 checks)")
            st.write("- 📖 Mastery level achievements (50%, 70%, 90% mastery)")

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


elif page == "Idiom Translator": # New Idiom Translator page
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