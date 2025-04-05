"""
Sentence Pattern Generator for Japanese language learning.

This module provides functionality to generate example sentences using specific
grammar patterns and vocabulary to help users practice their Japanese.
"""

import streamlit as st
import re
import os
import json
import random
from typing import List, Dict, Any, Optional
from utils import load_grammar_rules
from database import get_db, UserProgress

# Try to use OpenAI for sentence generation
try:
    from openai import OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except ImportError:
    openai_client = None
    st.warning("OpenAI package not installed. Using fallback sentence generation methods.")

class SentenceGenerator:
    """
    Generator for creating example sentences using Japanese grammar patterns.
    """
    
    def __init__(self, openai_client=None):
        """
        Initialize the sentence generator.
        
        Args:
            openai_client: Optional OpenAI client for AI-generated sentences
        """
        self.openai_client = openai_client
        
        # Load grammar patterns from rules
        try:
            self.grammar_rules = load_grammar_rules()
            
            # Extract patterns from grammar rules
            self.patterns = {}
            
            for rule in self.grammar_rules.get("rules", []):
                pattern_str = rule.get("pattern", "")
                if pattern_str:
                    name = pattern_str
                    if "name" in rule:
                        name = rule["name"]
                    
                    self.patterns[name] = {
                        "pattern": pattern_str,
                        "example": rule.get("example", ""),
                        "explanation": rule.get("explanation", ""),
                        "jlpt_level": rule.get("jlpt_level", "N/A"),
                    }
        except Exception as e:
            st.warning(f"Error loading grammar patterns: {str(e)}")
            self.grammar_rules = {"rules": []}
            self.patterns = {}
        
        # Load vocabulary if available
        try:
            with open("data/vocabulary.json", "r", encoding="utf-8") as f:
                self.vocabulary = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Create basic vocabulary categories
            self.vocabulary = {
                "nouns": [],
                "verbs": [],
                "adjectives": [],
                "adverbs": [],
                "time_expressions": [],
                "locations": [],
                "particles": []
            }
    
    def generate_sentences(self, pattern: str, count: int = 5, difficulty: str = "medium", topics: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """
        Generate example sentences using a specific grammar pattern.
        
        Args:
            pattern: The grammar pattern to use
            count: Number of sentences to generate
            difficulty: Difficulty level (easy, medium, hard)
            topics: Optional list of topics to focus on
            
        Returns:
            List of dictionaries with generated sentences
        """
        # Try AI-generated sentences if OpenAI is available
        if self.openai_client:
            try:
                return self._generate_ai_sentences(pattern, count, difficulty, topics)
            except Exception as e:
                st.warning(f"AI sentence generation failed: {str(e)}. Using pattern-based generation instead.")
                return self._generate_pattern_sentences(pattern, count, difficulty, topics)
        else:
            # Use pattern-based generation as fallback
            return self._generate_pattern_sentences(pattern, count, difficulty, topics)
    
    def _generate_ai_sentences(self, pattern: str, count: int = 5, difficulty: str = "medium", topics: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """
        Generate sentences using OpenAI.
        
        Args:
            pattern: The grammar pattern to use
            count: Number of sentences to generate
            difficulty: Difficulty level (easy, medium, hard)
            topics: Optional list of topics to focus on
            
        Returns:
            List of dictionaries with generated sentences
        """
        # Get the pattern information
        pattern_info = self.patterns.get(pattern, {"pattern": pattern, "explanation": "Unknown pattern"})
        
        # Format topics as a string if provided
        topics_str = f"on the following topics: {', '.join(topics)}" if topics else "on various everyday topics"
        
        # Prepare system message
        system_message = """
        You are a Japanese language teaching assistant specialized in creating example sentences 
        for grammar pattern practice. Create natural, useful example sentences that clearly 
        demonstrate the grammar pattern in context.
        """
        
        # Prepare prompt with detailed instructions
        prompt = f"""
        Please generate {count} example sentences in Japanese that use the grammar pattern: {pattern_info['pattern']}
        
        Pattern explanation: {pattern_info['explanation']}
        
        Requirements:
        - Difficulty level: {difficulty}
        - Create sentences {topics_str}
        - Each sentence should clearly demonstrate the pattern
        - Provide both the Japanese sentence and its English translation
        - Include furigana for any kanji
        - Highlight where the pattern appears in the sentence
        - Add a brief note explaining how the pattern is used in that specific sentence
        
        Format your response as a JSON array with each object containing:
        - japanese: The full Japanese sentence
        - english: The English translation
        - furigana: The sentence with furigana for kanji
        - pattern_highlight: The sentence with the pattern highlighted (using ** around the pattern)
        - explanation: A brief explanation of how the pattern is used in this sentence
        
        Difficulty guidelines:
        - easy: Use basic vocabulary (JLPT N5-N4), short sentences, common situations
        - medium: Moderately complex vocabulary (JLPT N4-N3), longer sentences, broader topics
        - hard: Advanced vocabulary (JLPT N3-N2), complex sentences, specialized topics
        """
        
        # Call the OpenAI API
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        try:
            result = json.loads(response.choices[0].message.content)
            
            # Extract the sentences array from the result
            if isinstance(result, dict) and "sentences" in result:
                return result["sentences"]
            elif isinstance(result, list):
                return result
            else:
                # Try to find any array in the response
                for key, value in result.items():
                    if isinstance(value, list) and len(value) > 0:
                        return value
                
                # If we can't find a valid array, create an error entry
                return [{
                    "japanese": f"Error: Could not generate sentences for pattern {pattern}",
                    "english": "Error in sentence generation",
                    "furigana": "",
                    "pattern_highlight": "",
                    "explanation": "Please try a different pattern or try again later."
                }]
        except Exception as e:
            # Return an error entry
            return [{
                "japanese": f"Error parsing AI response: {str(e)}",
                "english": "Error in sentence generation",
                "furigana": "",
                "pattern_highlight": "",
                "explanation": "Please try a different pattern or try again later."
            }]
    
    def _generate_pattern_sentences(self, pattern: str, count: int = 5, difficulty: str = "medium", topics: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """
        Generate sentences using template-based approach.
        
        Args:
            pattern: The grammar pattern to use
            count: Number of sentences to generate
            difficulty: Difficulty level (easy, medium, hard)
            topics: Optional list of topics to focus on
            
        Returns:
            List of dictionaries with generated sentences
        """
        # Get the pattern information
        pattern_info = self.patterns.get(pattern, {"pattern": pattern, "explanation": "Unknown pattern", "example": ""})
        
        # If no vocabulary is available, return the example from the pattern
        if not any(self.vocabulary.values()):
            if pattern_info.get("example"):
                return [{
                    "japanese": pattern_info["example"],
                    "english": "Example sentence (translation not available)",
                    "furigana": pattern_info["example"],
                    "pattern_highlight": pattern_info["example"],
                    "explanation": pattern_info["explanation"]
                }]
            else:
                return [{
                    "japanese": f"パターン: {pattern}",
                    "english": f"Pattern: {pattern}",
                    "furigana": f"パターン: {pattern}",
                    "pattern_highlight": f"パターン: {pattern}",
                    "explanation": "No example sentences available for this pattern."
                }]
        
        # Generate sentences based on templates
        sentences = []
        
        # Create templates based on common sentence structures
        templates = self._get_templates_for_pattern(pattern, difficulty)
        
        # Generate sentences using the templates
        for i in range(min(count, len(templates))):
            template = templates[i]
            sentence = self._fill_template(template, pattern, difficulty, topics)
            sentences.append(sentence)
        
        # Fill any remaining count with variations of the templates
        remaining = count - len(sentences)
        if remaining > 0:
            for i in range(remaining):
                template = random.choice(templates)
                sentence = self._fill_template(template, pattern, difficulty, topics)
                sentences.append(sentence)
        
        return sentences
    
    def _get_templates_for_pattern(self, pattern: str, difficulty: str) -> List[str]:
        """
        Get sentence templates appropriate for a grammar pattern.
        
        Args:
            pattern: The grammar pattern
            difficulty: Difficulty level
            
        Returns:
            List of sentence templates
        """
        # Basic templates that can work with most grammar patterns
        basic_templates = [
            "{subject}は{time_expression}に{location}で{object}を{pattern}。",
            "{subject}は{object}を{pattern}から、{result}。",
            "{time_expression}に{subject}は{pattern}。",
            "{subject}は{object}が{adjective}と{pattern}。",
            "{subject}は{adverb}{pattern}。"
        ]
        
        # Conditional templates for more complex patterns
        conditional_templates = [
            "{subject}は{condition}たら、{pattern}。",
            "{subject}が{condition}なら、{pattern}だろう。",
            "{subject}は{condition}ので、{pattern}。"
        ]
        
        # Question templates
        question_templates = [
            "{subject}は{object}を{pattern}か？",
            "どうして{subject}は{pattern}のですか？",
            "いつ{subject}は{pattern}の？"
        ]
        
        # Negative templates
        negative_templates = [
            "{subject}は{object}を{pattern}ない。",
            "{subject}は決して{pattern}ない。",
            "{subject}は{time_expression}に{pattern}なかった。"
        ]
        
        # Select templates based on pattern type and difficulty
        templates = []
        
        # Pattern categories (simplistic approach)
        is_verb_pattern = any(word in pattern for word in ["する", "ます", "です", "た", "る", "て"])
        is_adjective_pattern = any(word in pattern for word in ["い", "な", "だ"])
        is_noun_pattern = "の" in pattern
        is_conditional = any(word in pattern for word in ["たら", "なら", "ば", "と"])
        is_negative = any(word in pattern for word in ["ない", "ません", "なかった"])
        
        # Add relevant templates based on pattern type
        templates.extend(basic_templates)  # Always include basic templates
        
        if is_conditional:
            templates.extend(conditional_templates)
        
        if not is_negative and random.random() < 0.3:  # 30% chance to include negation
            templates.extend(negative_templates)
        
        if random.random() < 0.2:  # 20% chance to include questions
            templates.extend(question_templates)
        
        # Adjust based on difficulty
        if difficulty == "easy":
            # For easy, use simpler templates
            templates = [t for t in templates if t.count("{") <= 4]
        elif difficulty == "hard":
            # For hard, use more complex templates and add some complex ones
            complex_templates = [
                "{subject}は{object}を{pattern}けれども、{alternative}。",
                "{subject}が{object}を{pattern}ということは{conclusion}ということだ。",
                "{subject}は{time_expression}に{object}を{pattern}はずなのに、{unexpected_result}。"
            ]
            templates.extend(complex_templates)
        
        # Shuffle and return
        random.shuffle(templates)
        return templates
    
    def _fill_template(self, template: str, pattern: str, difficulty: str, topics: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Fill a template with appropriate vocabulary.
        
        Args:
            template: The sentence template
            pattern: The grammar pattern
            difficulty: Difficulty level
            topics: Optional topics to focus on
            
        Returns:
            Dictionary with the generated sentence
        """
        # Get vocabulary items based on difficulty
        vocabulary = self._get_vocabulary_by_difficulty(difficulty)
        
        # Filter by topics if provided
        if topics:
            # This would require topic tagging in the vocabulary data
            # For now, we'll just use the general vocabulary
            pass
        
        # Placeholders to fill
        placeholders = {
            "{subject}": self._get_random_item(vocabulary.get("subjects", [])),
            "{object}": self._get_random_item(vocabulary.get("objects", [])),
            "{location}": self._get_random_item(vocabulary.get("locations", [])),
            "{time_expression}": self._get_random_item(vocabulary.get("time_expressions", [])),
            "{adjective}": self._get_random_item(vocabulary.get("adjectives", [])),
            "{adverb}": self._get_random_item(vocabulary.get("adverbs", [])),
            "{condition}": self._get_random_item(vocabulary.get("conditions", [])),
            "{result}": self._get_random_item(vocabulary.get("results", [])),
            "{alternative}": self._get_random_item(vocabulary.get("alternatives", [])),
            "{conclusion}": self._get_random_item(vocabulary.get("conclusions", [])),
            "{unexpected_result}": self._get_random_item(vocabulary.get("unexpected_results", []))
        }
        
        # Replace the pattern placeholder with the actual pattern
        # Modify the pattern to fit grammatically if needed
        adjusted_pattern = self._adjust_pattern_for_template(pattern, template)
        placeholders["{pattern}"] = adjusted_pattern
        
        # Replace placeholders in the template
        japanese = template
        pattern_highlight = template
        
        for placeholder, value in placeholders.items():
            if placeholder in japanese:
                japanese = japanese.replace(placeholder, value)
                
                # For pattern_highlight, highlight the pattern
                if placeholder == "{pattern}":
                    pattern_highlight = pattern_highlight.replace(placeholder, f"**{value}**")
                else:
                    pattern_highlight = pattern_highlight.replace(placeholder, value)
        
        # Generate a simple English translation
        english = self._generate_simple_translation(japanese, pattern)
        
        # Use the Japanese sentence as furigana (in a real implementation, 
        # this would convert kanji to hiragana readings)
        furigana = japanese
        
        # Generate a simple explanation
        explanation = f"This sentence uses the '{pattern}' pattern to express {self._get_pattern_purpose(pattern)}."
        
        return {
            "japanese": japanese,
            "english": english,
            "furigana": furigana,
            "pattern_highlight": pattern_highlight,
            "explanation": explanation
        }
    
    def _get_vocabulary_by_difficulty(self, difficulty: str) -> Dict[str, List[str]]:
        """
        Get vocabulary appropriate for the given difficulty level.
        
        Args:
            difficulty: Difficulty level (easy, medium, hard)
            
        Returns:
            Dictionary with categorized vocabulary
        """
        # This is a simplified implementation
        # In a real implementation, vocabulary would be categorized by JLPT level
        
        # Use the vocabulary we have
        subjects = ["私", "彼", "彼女", "学生", "先生", "友達"]
        objects = ["本", "車", "食べ物", "映画", "仕事", "宿題"]
        locations = ["家", "学校", "会社", "図書館", "公園", "レストラン"]
        time_expressions = ["今日", "明日", "昨日", "来週", "先週", "午後"]
        adjectives = ["いい", "悪い", "大きい", "小さい", "面白い", "難しい"]
        adverbs = ["とても", "少し", "ゆっくり", "速く", "時々", "毎日"]
        conditions = ["行く", "食べる", "見る", "勉強する", "働く", "話す"]
        results = ["嬉しい", "疲れる", "分かる", "できる", "忙しい", "退屈"]
        alternatives = ["違うことをする", "他の選択肢がある", "別の方法がある"]
        conclusions = ["正しい", "間違い", "重要", "必要"]
        unexpected_results = ["予想外のことが起きた", "計画が変わった", "結果が違った"]
        
        # Adjust based on difficulty
        if difficulty == "easy":
            # Limit to basic vocabulary
            subjects = subjects[:3]
            objects = objects[:3]
            locations = locations[:3]
            time_expressions = time_expressions[:3]
            adjectives = adjectives[:3]
            adverbs = adverbs[:3]
            conditions = conditions[:3]
            results = results[:3]
        elif difficulty == "hard":
            # Add more complex vocabulary
            subjects.extend(["政府", "社長", "科学者", "専門家"])
            objects.extend(["問題", "環境", "経済", "技術"])
            locations.extend(["研究所", "海外", "宇宙", "世界中"])
            time_expressions.extend(["将来", "過去", "歴史上", "現代"])
            adjectives.extend(["複雑", "困難", "重要", "必要"])
            adverbs.extend(["非常に", "特に", "完全に", "実際に"])
        
        return {
            "subjects": subjects,
            "objects": objects,
            "locations": locations,
            "time_expressions": time_expressions,
            "adjectives": adjectives,
            "adverbs": adverbs,
            "conditions": conditions,
            "results": results,
            "alternatives": alternatives,
            "conclusions": conclusions,
            "unexpected_results": unexpected_results
        }
    
    def _get_random_item(self, items: List[str]) -> str:
        """
        Get a random item from a list, with fallback.
        
        Args:
            items: List of items to choose from
            
        Returns:
            A random item, or a default value if the list is empty
        """
        if not items:
            return "何か"  # "something" as a fallback
        return random.choice(items)
    
    def _adjust_pattern_for_template(self, pattern: str, template: str) -> str:
        """
        Adjust a grammar pattern to fit grammatically in a template.
        
        Args:
            pattern: The grammar pattern
            template: The sentence template
            
        Returns:
            Adjusted pattern that fits grammatically
        """
        # This is a very simplistic implementation
        # In a real implementation, this would handle various grammatical adjustments
        
        # Check if template requires a specific form
        if "ない" in template and "ない" not in pattern:
            # Convert to negative form (very simplistic)
            if pattern.endswith("る"):
                return pattern[:-1] + "ない"
            elif pattern.endswith("く"):
                return pattern + "ない"
            elif pattern.endswith("い"):
                return pattern[:-1] + "くない"
            else:
                return pattern + "ない"
        
        return pattern
    
    def _generate_simple_translation(self, japanese: str, pattern: str) -> str:
        """
        Generate a simple English translation for a Japanese sentence.
        
        Args:
            japanese: The Japanese sentence
            pattern: The grammar pattern used
            
        Returns:
            Simple English translation
        """
        # This is a very simplistic implementation
        # In a real implementation, this would use more sophisticated translation
        
        # Just return a template-based translation
        return f"English translation of a sentence using the '{pattern}' pattern."
    
    def _get_pattern_purpose(self, pattern: str) -> str:
        """
        Get a description of what a grammar pattern is used for.
        
        Args:
            pattern: The grammar pattern
            
        Returns:
            Description of the pattern's purpose
        """
        # Check for common pattern types
        if "たい" in pattern:
            return "a desire or wish to do something"
        elif "なければならない" in pattern:
            return "an obligation or necessity"
        elif "てもいい" in pattern:
            return "permission or possibility"
        elif "てはいけない" in pattern:
            return "prohibition"
        elif "たら" in pattern:
            return "a conditional situation"
        elif "ている" in pattern:
            return "ongoing action or state"
        elif "た後" in pattern:
            return "sequence of actions (after doing something)"
        elif "ために" in pattern:
            return "purpose or goal"
        elif "と思う" in pattern:
            return "thoughts or opinions"
        elif "かもしれない" in pattern:
            return "possibility"
        else:
            return "a specific grammatical function in Japanese"

    def get_all_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available grammar patterns.
        
        Returns:
            Dictionary of all patterns with their information
        """
        return self.patterns
    
    def get_patterns_by_jlpt(self, level: str) -> Dict[str, Dict[str, Any]]:
        """
        Get grammar patterns filtered by JLPT level.
        
        Args:
            level: JLPT level (N5, N4, N3, N2, N1)
            
        Returns:
            Dictionary of patterns at the specified JLPT level
        """
        return {
            name: info for name, info in self.patterns.items()
            if info.get("jlpt_level") == level
        }
    
    def add_custom_pattern(self, name: str, pattern: str, explanation: str, example: str, jlpt_level: str = "Custom") -> bool:
        """
        Add a custom grammar pattern.
        
        Args:
            name: Name of the pattern
            pattern: The grammar pattern itself
            explanation: Explanation of the pattern
            example: Example sentence using the pattern
            jlpt_level: JLPT level (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if name in self.patterns:
            return False
        
        self.patterns[name] = {
            "pattern": pattern,
            "explanation": explanation,
            "example": example,
            "jlpt_level": jlpt_level
        }
        
        return True
    
    def search_patterns(self, query: str) -> Dict[str, Dict[str, Any]]:
        """
        Search for grammar patterns.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary of matching patterns
        """
        query = query.lower()
        return {
            name: info for name, info in self.patterns.items()
            if query in name.lower() 
            or query in info.get("pattern", "").lower() 
            or query in info.get("explanation", "").lower()
        }

def render_sentence_generator_ui():
    """
    Render the UI for the sentence pattern generator.
    """
    st.title("🔄 Sentence Pattern Generator")
    
    st.markdown("""
    Generate example sentences using Japanese grammar patterns to help with your language learning.
    This tool creates sentences that demonstrate how specific grammar patterns are used in context.
    """)
    
    # Initialize the sentence generator
    global openai_client
    generator = SentenceGenerator(openai_client)
    
    # Create tabs
    tabs = st.tabs(["Generate Sentences", "Grammar Patterns", "Saved Sentences"])
    
    # Generate Sentences tab
    with tabs[0]:
        st.header("Generate Example Sentences")
        
        # Grammar pattern selection
        patterns = generator.get_all_patterns()
        pattern_names = list(patterns.keys())
        
        if not pattern_names:
            st.warning("No grammar patterns found. Please check your grammar rules configuration.")
            return
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            pattern = st.selectbox(
                "Select a Grammar Pattern",
                pattern_names,
                key="pattern_select"
            )
        
        with col2:
            # JLPT level filter
            jlpt_levels = sorted(set(info.get("jlpt_level", "N/A") for info in patterns.values()))
            jlpt_filter = st.selectbox(
                "JLPT Level Filter",
                ["All"] + jlpt_levels,
                key="jlpt_filter"
            )
            
            # If a JLPT level is selected, update the pattern list
            if jlpt_filter != "All":
                filtered_patterns = generator.get_patterns_by_jlpt(jlpt_filter)
                pattern_names = list(filtered_patterns.keys())
                
                if pattern not in pattern_names and pattern_names:
                    pattern = pattern_names[0]
        
        # Display pattern information
        if pattern and pattern in patterns:
            pattern_info = patterns[pattern]
            
            st.markdown(f"""
            **Pattern:** {pattern_info.get('pattern', 'N/A')}
            
            **Explanation:** {pattern_info.get('explanation', 'N/A')}
            
            **JLPT Level:** {pattern_info.get('jlpt_level', 'N/A')}
            
            **Example:** {pattern_info.get('example', 'N/A')}
            """)
        
        # Generation options
        st.subheader("Generation Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            count = st.number_input(
                "Number of sentences",
                min_value=1,
                max_value=10,
                value=5,
                key="sentence_count"
            )
        
        with col2:
            difficulty = st.select_slider(
                "Difficulty level",
                options=["easy", "medium", "hard"],
                value="medium",
                key="difficulty_level"
            )
        
        with col3:
            # Common topics in Japanese learning
            topics_options = [
                "Daily Life", "School", "Work", "Travel", 
                "Food", "Hobbies", "Family", "Health",
                "Culture", "Technology", "Nature", "News"
            ]
            
            topics = st.multiselect(
                "Topics (optional)",
                topics_options,
                key="topics_select"
            )
        
        # Generate button
        if st.button("Generate Sentences", key="generate_btn"):
            if pattern:
                with st.spinner(f"Generating {count} sentences with the '{pattern}' pattern..."):
                    sentences = generator.generate_sentences(
                        pattern,
                        count=count,
                        difficulty=difficulty,
                        topics=topics
                    )
                
                if not sentences:
                    st.warning("No sentences could be generated. Please try different parameters.")
                else:
                    # Display the generated sentences
                    st.subheader("Generated Sentences")
                    
                    for i, sentence in enumerate(sentences):
                        with st.expander(f"Sentence {i+1}", expanded=True):
                            # Japanese sentence with furigana
                            st.markdown(f"**Japanese:** {sentence.get('japanese', '')}")
                            
                            if sentence.get('furigana'):
                                st.markdown(f"**Reading:** {sentence.get('furigana', '')}")
                            
                            # Pattern highlight
                            if sentence.get('pattern_highlight'):
                                st.markdown(f"**Pattern Highlight:** {sentence.get('pattern_highlight', '')}")
                            
                            # English translation
                            st.markdown(f"**English:** {sentence.get('english', '')}")
                            
                            # Explanation
                            st.markdown(f"**Explanation:** {sentence.get('explanation', '')}")
                            
                            # Save button
                            if st.button("Save Sentence", key=f"save_btn_{i}"):
                                # Save to session state
                                if "saved_sentences" not in st.session_state:
                                    st.session_state.saved_sentences = []
                                
                                sentence_record = {
                                    "pattern": pattern,
                                    "jlpt_level": patterns.get(pattern, {}).get("jlpt_level", "N/A"),
                                    "difficulty": difficulty,
                                    "sentence": sentence
                                }
                                
                                st.session_state.saved_sentences.append(sentence_record)
                                st.success("Sentence saved successfully!")
            else:
                st.warning("Please select a grammar pattern.")
    
    # Grammar Patterns tab
    with tabs[1]:
        st.header("Browse Grammar Patterns")
        
        # Search box
        search_query = st.text_input(
            "Search for patterns",
            placeholder="Enter keywords to search...",
            key="pattern_search"
        )
        
        # JLPT level filter for browsing
        col1, col2 = st.columns([1, 3])
        
        with col1:
            browse_jlpt_filter = st.selectbox(
                "JLPT Level",
                ["All"] + jlpt_levels,
                key="browse_jlpt_filter"
            )
        
        # Filter patterns
        filtered_patterns = patterns
        
        if search_query:
            filtered_patterns = generator.search_patterns(search_query)
        
        if browse_jlpt_filter != "All":
            filtered_patterns = {
                name: info for name, info in filtered_patterns.items()
                if info.get("jlpt_level") == browse_jlpt_filter
            }
        
        # Display filtered patterns
        if not filtered_patterns:
            st.info("No grammar patterns match your search criteria.")
        else:
            st.write(f"Showing {len(filtered_patterns)} grammar patterns:")
            
            # Group by JLPT level
            patterns_by_level = {}
            for name, info in filtered_patterns.items():
                level = info.get("jlpt_level", "Other")
                if level not in patterns_by_level:
                    patterns_by_level[level] = []
                patterns_by_level[level].append((name, info))
            
            # Sort levels
            sorted_levels = sorted(patterns_by_level.keys())
            
            # Display each level in a separate section
            for level in sorted_levels:
                with st.expander(f"JLPT {level} Patterns ({len(patterns_by_level[level])})", expanded=level == browse_jlpt_filter):
                    for name, info in patterns_by_level[level]:
                        with st.expander(f"{name} - {info.get('pattern', '')}", expanded=False):
                            st.markdown(f"**Pattern:** {info.get('pattern', 'N/A')}")
                            st.markdown(f"**Explanation:** {info.get('explanation', 'N/A')}")
                            st.markdown(f"**Example:** {info.get('example', 'N/A')}")
                            
                            # Button to generate sentences with this pattern
                            if st.button("Generate Sentences", key=f"gen_btn_{name}"):
                                st.session_state.pattern_to_generate = name
                                st.rerun()
        
        # Custom pattern section
        with st.expander("Add Custom Grammar Pattern", expanded=False):
            st.subheader("Add Your Own Grammar Pattern")
            
            with st.form("custom_pattern_form"):
                custom_name = st.text_input(
                    "Pattern Name",
                    placeholder="e.g., Te-form + imasu",
                    key="custom_name"
                )
                
                custom_pattern = st.text_input(
                    "Grammar Pattern",
                    placeholder="e.g., ～ています",
                    key="custom_pattern"
                )
                
                custom_explanation = st.text_area(
                    "Explanation",
                    placeholder="Explain how this pattern is used...",
                    key="custom_explanation"
                )
                
                custom_example = st.text_input(
                    "Example Sentence",
                    placeholder="e.g., 今、日本語を勉強しています",
                    key="custom_example"
                )
                
                custom_jlpt = st.selectbox(
                    "JLPT Level",
                    ["N5", "N4", "N3", "N2", "N1", "Custom"],
                    key="custom_jlpt"
                )
                
                submit = st.form_submit_button("Add Pattern")
                
                if submit:
                    if custom_name and custom_pattern and custom_explanation:
                        success = generator.add_custom_pattern(
                            name=custom_name,
                            pattern=custom_pattern,
                            explanation=custom_explanation,
                            example=custom_example,
                            jlpt_level=custom_jlpt
                        )
                        
                        if success:
                            st.success(f"Added custom pattern: {custom_name}")
                            
                            # Update patterns
                            patterns = generator.get_all_patterns()
                            pattern_names = list(patterns.keys())
                            
                            # Clear the form
                            st.session_state.custom_name = ""
                            st.session_state.custom_pattern = ""
                            st.session_state.custom_explanation = ""
                            st.session_state.custom_example = ""
                        else:
                            st.error(f"Pattern name '{custom_name}' already exists. Please use a different name.")
                    else:
                        st.warning("Please fill in all required fields.")
    
    # Saved Sentences tab
    with tabs[2]:
        st.header("Your Saved Sentences")
        
        # Get saved sentences from session state
        if "saved_sentences" not in st.session_state:
            st.session_state.saved_sentences = []
        
        if not st.session_state.saved_sentences:
            st.info("You haven't saved any sentences yet. Generate and save sentences to see them here.")
        else:
            # Filter options
            filter_jlpt = st.selectbox(
                "Filter by JLPT Level",
                ["All"] + sorted(set(s["jlpt_level"] for s in st.session_state.saved_sentences)),
                key="saved_jlpt_filter"
            )
            
            filter_difficulty = st.selectbox(
                "Filter by Difficulty",
                ["All", "easy", "medium", "hard"],
                key="saved_difficulty_filter"
            )
            
            # Apply filters
            filtered_saved = st.session_state.saved_sentences
            
            if filter_jlpt != "All":
                filtered_saved = [s for s in filtered_saved if s["jlpt_level"] == filter_jlpt]
            
            if filter_difficulty != "All":
                filtered_saved = [s for s in filtered_saved if s["difficulty"] == filter_difficulty]
            
            # Show results
            if not filtered_saved:
                st.info("No saved sentences match your filter criteria.")
            else:
                st.write(f"Showing {len(filtered_saved)} saved sentences:")
                
                for i, saved in enumerate(filtered_saved):
                    pattern = saved["pattern"]
                    sentence = saved["sentence"]
                    
                    with st.expander(f"{pattern}: {sentence.get('japanese', '')[:30]}...", expanded=False):
                        # Japanese sentence with furigana
                        st.markdown(f"**Japanese:** {sentence.get('japanese', '')}")
                        
                        if sentence.get('furigana'):
                            st.markdown(f"**Reading:** {sentence.get('furigana', '')}")
                        
                        # Pattern highlight
                        if sentence.get('pattern_highlight'):
                            st.markdown(f"**Pattern Highlight:** {sentence.get('pattern_highlight', '')}")
                        
                        # English translation
                        st.markdown(f"**English:** {sentence.get('english', '')}")
                        
                        # Explanation
                        st.markdown(f"**Explanation:** {sentence.get('explanation', '')}")
                        
                        # Metadata
                        st.markdown(f"""
                        **Pattern:** {pattern}  
                        **JLPT Level:** {saved.get('jlpt_level', 'N/A')}  
                        **Difficulty:** {saved.get('difficulty', 'N/A')}
                        """)
                        
                        # Delete button
                        if st.button("Delete", key=f"delete_saved_{i}"):
                            st.session_state.saved_sentences.remove(saved)
                            st.success("Sentence removed from saved list.")
                            st.rerun()
            
            # Export/import functionality
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Export Saved Sentences"):
                    # Convert to JSON
                    json_data = json.dumps(st.session_state.saved_sentences, indent=2)
                    
                    # Create download button
                    st.download_button(
                        label="Download JSON",
                        data=json_data,
                        file_name="saved_sentences.json",
                        mime="application/json"
                    )
            
            with col2:
                if st.button("Clear All Saved Sentences"):
                    # Confirm dialog
                    if st.session_state.get("confirm_clear", False):
                        st.session_state.saved_sentences = []
                        st.success("All saved sentences have been cleared.")
                        st.session_state.confirm_clear = False
                        st.rerun()
                    else:
                        st.session_state.confirm_clear = True
                        st.warning("Are you sure? Click again to confirm.")
    
    # Handle automatic navigation to generate sentences with a selected pattern
    if hasattr(st.session_state, "pattern_to_generate"):
        pattern = st.session_state.pattern_to_generate
        del st.session_state.pattern_to_generate
        
        # Switch to the generate tab
        st.session_state.pattern_select = pattern
        st.rerun()

def generate_example_grammar_patterns():
    """
    Generate example grammar patterns for demonstration.
    
    Returns:
        Dictionary of grammar patterns
    """
    return {
        "ます form": {
            "pattern": "～ます",
            "explanation": "Polite present/future form of verbs",
            "example": "毎日日本語を勉強します。",
            "jlpt_level": "N5"
        },
        "Te-form": {
            "pattern": "～て",
            "explanation": "Used to connect actions, make requests, and form other grammatical structures",
            "example": "窓を開けて、新鮮な空気を入れてください。",
            "jlpt_level": "N5"
        },
        "Potential Form": {
            "pattern": "～ことができる",
            "explanation": "Expresses ability or possibility to do something",
            "example": "私は日本語を話すことができます。",
            "jlpt_level": "N5"
        },
        "Nai Form": {
            "pattern": "～ない",
            "explanation": "Negative form of verbs and i-adjectives",
            "example": "明日は忙しいので、行きません。",
            "jlpt_level": "N5"
        },
        "Ta Form": {
            "pattern": "～た",
            "explanation": "Past tense form of verbs",
            "example": "昨日映画を見ました。",
            "jlpt_level": "N5"
        },
        "Te iru Form": {
            "pattern": "～ている",
            "explanation": "Expresses ongoing action or state",
            "example": "彼は今テレビを見ています。",
            "jlpt_level": "N5"
        },
        "Te kudasai": {
            "pattern": "～てください",
            "explanation": "Please do something (request)",
            "example": "ここに名前を書いてください。",
            "jlpt_level": "N5"
        },
        "Tai Form": {
            "pattern": "～たい",
            "explanation": "Expresses desire to do something",
            "example": "日本に行きたいです。",
            "jlpt_level": "N5"
        },
        "Te mo ii": {
            "pattern": "～てもいい",
            "explanation": "It's okay to do something / permission",
            "example": "ここで写真を撮ってもいいですか？",
            "jlpt_level": "N4"
        },
        "Te wa ikenai": {
            "pattern": "～てはいけない",
            "explanation": "Must not do something / prohibition",
            "example": "この部屋では食べてはいけません。",
            "jlpt_level": "N4"
        },
        "Nakute wa ikenai": {
            "pattern": "～なくてはいけない",
            "explanation": "Must do something / obligation",
            "example": "明日までに宿題を終わらせなくてはいけません。",
            "jlpt_level": "N4"
        },
        "Ba Form": {
            "pattern": "～ば",
            "explanation": "If/when conditional",
            "example": "お金があれば、新しい車を買います。",
            "jlpt_level": "N4"
        },
        "Tara Form": {
            "pattern": "～たら",
            "explanation": "If/when conditional (after something happens)",
            "example": "雨が降ったら、傘を持って行きます。",
            "jlpt_level": "N4"
        },
        "Te kara": {
            "pattern": "～てから",
            "explanation": "After doing something",
            "example": "朝ご飯を食べてから、学校に行きます。",
            "jlpt_level": "N4"
        },
        "You ni naru": {
            "pattern": "～ようになる",
            "explanation": "To come to be able to / to reach a state where",
            "example": "毎日練習して、日本語が上手に話せるようになりました。",
            "jlpt_level": "N3"
        },
        "Tari Tari": {
            "pattern": "～たり～たりする",
            "explanation": "Doing things like A and B / non-exhaustive list of actions",
            "example": "週末は映画を見たり、友達と遊んだりします。",
            "jlpt_level": "N3"
        },
    }