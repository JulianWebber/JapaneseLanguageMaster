import streamlit as st
import json
from grammar_checker import GrammarChecker
from utils import load_grammar_rules, analyze_text
from database import get_db, GrammarCheck
from contextlib import contextmanager

# Initialize the application
st.set_page_config(page_title="Japanese Grammar Checker", layout="wide")

# Load grammar rules
grammar_rules = load_grammar_rules()
checker = GrammarChecker(grammar_rules)

@contextmanager
def get_database():
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

st.title("Japanese Grammar Checker")

# Main input section
st.subheader("Enter Japanese Text")
input_text = st.text_area("Japanese Text", placeholder="Enter Japanese text here...", key="input_text")

if input_text:
    # Analysis section
    st.subheader("Grammar Analysis")

    # Perform grammar check
    analysis_results = checker.check_grammar(input_text)

    # Save to database
    with get_database() as db:
        GrammarCheck.create(db, input_text, analysis_results)

    # Display results in tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Grammar Issues",
        "Advanced Patterns",
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
        if analysis_results['particle_usage']:
            for particle in analysis_results['particle_usage']:
                with st.expander(f"Particle: {particle['particle']}"):
                    st.write(f"**Usage:** {particle['usage']}")
                    st.write(f"**Context:** {particle['context']}")
        else:
            st.info("No particle usage to analyze.")

    with tab4:
        if analysis_results['verb_conjugations']:
            for verb in analysis_results['verb_conjugations']:
                with st.expander(f"Verb: {verb['base_form']}"):
                    st.write(f"**Conjugation:** {verb['conjugation']}")
                    st.write(f"**Form:** {verb['form']}")
                    if 'context' in verb:
                        st.write(f"**Context:** {verb['context']}")
        else:
            st.info("No verb conjugations to analyze.")

# Recent checks section
st.sidebar.title("Recent Checks")
with get_database() as db:
    recent_checks = GrammarCheck.get_recent_checks(db)
    for check in recent_checks:
        with st.sidebar.expander(f"Check {check.created_at.strftime('%Y-%m-%d %H:%M')}"):
            st.write("**Input Text:**")
            st.write(check.input_text)
            st.write("**Found Issues:**", len(check.grammar_issues))
            st.write("**Advanced Patterns:**", len(check.advanced_patterns)) #Corrected line
            st.write("**Particles Analyzed:**", len(check.particle_usage))
            st.write("**Verbs Analyzed:**", len(check.verb_conjugations))

# Grammar reference section
with st.expander("Grammar Reference"):
    st.write("Common Grammar Patterns:")
    for pattern in grammar_rules['common_patterns']:
        st.write(f"**Pattern:** {pattern['pattern']}")
        st.write(f"**Usage:** {pattern['explanation']}")
        st.write(f"**Example:** {pattern['example']}")
        if 'context_rules' in pattern:
            st.write("**Context Rules:**")
            for rule in pattern['context_rules']:
                st.write(f"- {rule}")
        st.markdown("---")

    st.write("Conditional Patterns:")
    for pattern in grammar_rules.get('conditional_patterns', []):
        st.write(f"**Pattern:** {pattern['pattern']}")
        st.write("**Examples:**")
        for example in pattern['examples']:
            st.write(f"- {example['correct']}")
            st.write(f"  ({example['explanation']})")
        st.markdown("---")