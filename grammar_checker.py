import re
from typing import Dict, List, Any, Tuple
from database import CustomGrammarRule

class GrammarChecker:
    def __init__(self, rules: Dict, db=None):
        self.rules = rules
        self.particle_patterns = rules['particles']
        self.verb_patterns = rules['verbs']
        self.grammar_patterns = rules['common_patterns']
        self.conditional_patterns = rules.get('conditional_patterns', [])
        self.db = db
        self.custom_rules = []
        if db:
            self.load_custom_rules()

    def load_custom_rules(self):
        """
        Load custom grammar rules from the database
        """
        if self.db:
            self.custom_rules = CustomGrammarRule.get_active_rules(self.db)

    def check_grammar(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Perform grammar analysis on the input text
        """
        results = {
            'grammar_issues': [],
            'particle_usage': [],
            'verb_conjugations': [],
            'advanced_patterns': [],
            'custom_patterns': []
        }

        # Check particles
        self._check_particles(text, results)

        # Check verb conjugations
        self._check_verbs(text, results)

        # Check general grammar patterns with context
        self._check_patterns_with_context(text, results)

        # Check conditional patterns
        self._check_conditional_patterns(text, results)

        # Check custom patterns
        self._check_custom_patterns(text, results)

        return results

    def _check_custom_patterns(self, text: str, results: Dict[str, List[Dict[str, str]]]):
        """
        Check custom grammar patterns
        """
        for rule in self.custom_rules:
            matches = list(re.finditer(rule.check_pattern, text))
            for match in matches:
                context = self._get_context(text, match)
                context_valid = True

                if rule.context_rules:
                    context_valid = self._validate_context_rules(
                        text, match, rule.context_rules
                    )

                if not context_valid or not re.search(rule.correct_pattern, text):
                    results['grammar_issues'].append({
                        'pattern': rule.pattern,
                        'description': rule.error_description,
                        'suggestion': rule.suggestion,
                        'example': rule.example,
                        'context': context,
                        'custom_rule': True
                    })
                else:
                    results['custom_patterns'].append({
                        'pattern': rule.pattern,
                        'usage': rule.explanation,
                        'context': context
                    })

    def _check_particles(self, text: str, results: Dict[str, List[Dict[str, str]]]):
        """
        Check particle usage in the text
        """
        for particle in self.particle_patterns:
            pattern = particle['pattern']
            matches = list(re.finditer(pattern, text))
            for match in matches:
                results['particle_usage'].append({
                    'particle': particle['particle'],
                    'usage': particle['usage'],
                    'context': self._get_context(text, match)
                })

    def _check_verbs(self, text: str, results: Dict[str, List[Dict[str, str]]]):
        """
        Check verb conjugations in the text
        """
        for verb in self.verb_patterns:
            pattern = verb['pattern']
            matches = list(re.finditer(pattern, text))
            for match in matches:
                results['verb_conjugations'].append({
                    'base_form': verb['base_form'],
                    'conjugation': verb['conjugation'],
                    'form': verb['form'],
                    'context': self._get_context(text, match)
                })

    def _check_patterns_with_context(self, text: str, results: Dict[str, List[Dict[str, str]]]):
        """
        Check grammar patterns with contextual awareness
        """
        for pattern in self.grammar_patterns:
            if pattern.get('context_rules'):
                matches = list(re.finditer(pattern['check_pattern'], text))
                for match in matches:
                    context = self._get_context(text, match)
                    context_valid = self._validate_context_rules(
                        text, match, pattern['context_rules']
                    )

                    if not context_valid:
                        results['grammar_issues'].append({
                            'pattern': pattern['pattern'],
                            'description': pattern['error_description'],
                            'suggestion': pattern['suggestion'],
                            'example': pattern['example'],
                            'context': context
                        })
                    else:
                        results['advanced_patterns'].append({
                            'pattern': pattern['pattern'],
                            'usage': pattern['explanation'],
                            'context': context
                        })

    def _check_conditional_patterns(self, text: str, results: Dict[str, List[Dict[str, str]]]):
        """
        Check conditional grammar patterns
        """
        for pattern in self.conditional_patterns:
            conditions = pattern['conditions']

            # Check for matches
            for example in pattern['examples']:
                context_matches = self._find_pattern_context(text, pattern['pattern'])

                for match, context in context_matches:
                    is_valid = self._validate_conditional_rules(
                        text, match, conditions, context
                    )

                    if not is_valid:
                        results['grammar_issues'].append({
                            'pattern': pattern['pattern'],
                            'description': f"Incorrect usage of {pattern['pattern']}",
                            'suggestion': f"See example: {example['correct']}",
                            'example': example['explanation'],
                            'context': context
                        })

    def _validate_context_rules(self, text: str, match: re.Match, rules: List[str]) -> bool:
        """
        Validate context rules for a pattern match
        """
        for rule in rules:
            if rule == "must_follow_te_form":
                if not re.search(r'て$', text[:match.start()].strip()):
                    return False
            elif rule == "end_of_sentence":
                if not re.search(r'[。\n]', text[match.end():].strip()):
                    return False
            elif rule == "must_follow_verb_or_adjective":
                if not re.search(r'(い|な)$', text[:match.start()].strip()):
                    return False
            elif rule == "requires_contrasting_clause":
                if not re.search(r'[が、けど]', text[match.end():]):
                    return False
        return True

    def _validate_conditional_rules(
        self, text: str, match: re.Match, conditions: Dict, context: str
    ) -> bool:
        """
        Validate conditional rules for a pattern
        """
        for condition_type, rules in conditions.items():
            if condition_type == "preceding":
                for rule in rules:
                    if rule == "verb_past_form":
                        if not re.search(r'た$', text[:match.start()].strip()):
                            return False
            elif condition_type == "following":
                for rule in rules:
                    if rule == "main_clause_required":
                        if not re.search(r'[、].+', text[match.end():]):
                            return False
        return True

    def _find_pattern_context(self, text: str, pattern: str) -> List[Tuple[re.Match, str]]:
        """
        Find pattern matches with their context
        """
        matches = list(re.finditer(re.escape(pattern), text))
        return [(match, self._get_context(text, match)) for match in matches]

    def _get_context(self, text: str, match: re.Match) -> str:
        """
        Get the context around a matched pattern
        """
        start = max(0, match.start() - 10)
        end = min(len(text), match.end() + 10)
        return text[start:end]