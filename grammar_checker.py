import re
from typing import Dict, List, Any

class GrammarChecker:
    def __init__(self, rules: Dict):
        self.rules = rules
        self.particle_patterns = rules['particles']
        self.verb_patterns = rules['verbs']
        self.grammar_patterns = rules['common_patterns']

    def check_grammar(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Perform grammar analysis on the input text
        """
        results = {
            'grammar_issues': [],
            'particle_usage': [],
            'verb_conjugations': []
        }

        # Check particles
        self._check_particles(text, results)
        
        # Check verb conjugations
        self._check_verbs(text, results)
        
        # Check general grammar patterns
        self._check_patterns(text, results)

        return results

    def _check_particles(self, text: str, results: Dict[str, List[Dict[str, str]]]):
        """
        Check particle usage in the text
        """
        for particle in self.particle_patterns:
            pattern = particle['pattern']
            if re.search(pattern, text):
                results['particle_usage'].append({
                    'particle': particle['particle'],
                    'usage': particle['usage'],
                    'context': self._get_context(text, pattern)
                })

    def _check_verbs(self, text: str, results: Dict[str, List[Dict[str, str]]]):
        """
        Check verb conjugations in the text
        """
        for verb in self.verb_patterns:
            pattern = verb['pattern']
            if re.search(pattern, text):
                results['verb_conjugations'].append({
                    'base_form': verb['base_form'],
                    'conjugation': verb['conjugation'],
                    'form': verb['form']
                })

    def _check_patterns(self, text: str, results: Dict[str, List[Dict[str, str]]]):
        """
        Check general grammar patterns
        """
        for pattern in self.grammar_patterns:
            if pattern['check_pattern'] and re.search(pattern['check_pattern'], text):
                if not re.search(pattern['correct_pattern'], text):
                    results['grammar_issues'].append({
                        'description': pattern['error_description'],
                        'suggestion': pattern['suggestion'],
                        'example': pattern['example']
                    })

    def _get_context(self, text: str, pattern: str) -> str:
        """
        Get the context around a matched pattern
        """
        match = re.search(pattern, text)
        if match:
            start = max(0, match.start() - 10)
            end = min(len(text), match.end() + 10)
            return text[start:end]
        return ""
