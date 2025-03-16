import streamlit as st
import json
from grammar_checker import GrammarChecker
from utils import load_grammar_rules, analyze_text
from database import get_db, GrammarCheck, CustomGrammarRule, UserProgress
from contextlib import contextmanager
import uuid

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
page = st.sidebar.radio("Navigation", ["Grammar Check", "Progress Dashboard", "Custom Rules"])

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

        # Streak information
        st.write("### Learning Streak 🔥")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current Streak", f"{user_progress.current_streak} days")
        with col2:
            st.metric("Longest Streak", f"{user_progress.longest_streak} days")

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

        # Mastery breakdown
        st.subheader("Mastery Levels")

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

        # Recent activity
        st.subheader("Recent Activity")
        recent_checks = GrammarCheck.get_recent_checks(db, limit=5)
        for check in recent_checks:
            with st.expander(f"Check {check.created_at.strftime('%Y-%m-%d %H:%M')}"):
                st.write("**Input Text:**")
                st.write(check.input_text)
                st.write("**Results:**")
                st.write(f"- Issues Found: {len(check.grammar_issues)}")
                st.write(f"- Particles Used: {len(check.particle_usage)}")
                st.write(f"- Verbs Analyzed: {len(check.verb_conjugations)}")

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