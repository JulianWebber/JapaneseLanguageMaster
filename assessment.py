from typing import Dict, List, Tuple
import json

class LanguageLevelAssessor:
    def __init__(self):
        self.difficulty_levels = {
            'beginner': ['basic_particles', 'simple_verbs', 'basic_adjectives'],
            'intermediate': ['te_form', 'potential_form', 'conditional_forms'],
            'advanced': ['keigo', 'passive_causative', 'complex_compounds']
        }
        
        self.grammar_categories = {
            'particles': ['は', 'が', 'を', 'に', 'で', 'へ', 'から', 'まで'],
            'verb_forms': ['ます形', 'て形', '可能形', '受身形', '使役形'],
            'adjectives': ['い形容詞', 'な形容詞', '連体形'],
            'conditionals': ['たら', 'ば', 'なら', 'と'],
            'honorifics': ['謙譲語', '尊敬語', '丁寧語'],
            'compounds': ['〜ている', '〜てある', '〜ておく', '〜てしまう']
        }

    def calculate_comfort_level(self, comfort_ratings: Dict[str, int]) -> str:
        """Calculate overall comfort level based on self-assessment ratings"""
        avg_rating = sum(comfort_ratings.values()) / len(comfort_ratings)
        if avg_rating < 2:
            return 'beginner'
        elif avg_rating < 4:
            return 'intermediate'
        else:
            return 'advanced'

    def analyze_strengths_weaknesses(
        self, comfort_ratings: Dict[str, int]
    ) -> Tuple[List[str], List[str]]:
        """Identify strong and weak areas based on comfort ratings"""
        strong_areas = []
        weak_areas = []
        
        for category, rating in comfort_ratings.items():
            if rating >= 4:
                strong_areas.append(category)
            elif rating <= 2:
                weak_areas.append(category)
                
        return strong_areas, weak_areas

    def get_recommended_materials(self, level: str, weak_areas: List[str]) -> Dict:
        """Get recommended study materials based on level and weak areas"""
        recommendations = {
            'grammar_points': [],
            'practice_areas': [],
            'suggested_patterns': []
        }

        # Basic recommendations based on level
        if level == 'beginner':
            recommendations['grammar_points'] = [
                'Basic particle usage (は, が, を)',
                'Simple verb conjugations',
                'Basic adjective forms'
            ]
        elif level == 'intermediate':
            recommendations['grammar_points'] = [
                'て-form combinations',
                'Conditional forms',
                'Complex particle usage'
            ]
        else:  # advanced
            recommendations['grammar_points'] = [
                'Honorific language',
                'Complex compound forms',
                'Advanced writing styles'
            ]

        # Add specific recommendations for weak areas
        for area in weak_areas:
            if area in self.grammar_categories:
                recommendations['practice_areas'].append(
                    f"Focus on {area}: {', '.join(self.grammar_categories[area])}"
                )

        return recommendations

    def evaluate_test_results(self, test_answers: Dict[str, bool]) -> Dict:
        """Evaluate test results and provide a detailed analysis"""
        correct_count = sum(1 for answer in test_answers.values() if answer)
        total_questions = len(test_answers)
        score_percentage = (correct_count / total_questions) * 100

        return {
            'score': score_percentage,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'mastery_level': 'advanced' if score_percentage >= 80 else 
                           'intermediate' if score_percentage >= 60 else 
                           'beginner'
        }
