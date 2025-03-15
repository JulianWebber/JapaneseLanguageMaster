import json
from typing import Dict

def load_grammar_rules() -> Dict:
    """
    Load grammar rules from the JSON file
    """
    with open('grammar_rules.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_text(text: str) -> Dict:
    """
    Analyze Japanese text for basic properties
    """
    return {
        'length': len(text),
        'has_kanji': any(is_kanji(char) for char in text),
        'has_hiragana': any(is_hiragana(char) for char in text),
        'has_katakana': any(is_katakana(char) for char in text)
    }

def is_kanji(char: str) -> bool:
    """
    Check if a character is a kanji
    """
    return '\u4e00' <= char <= '\u9fff'

def is_hiragana(char: str) -> bool:
    """
    Check if a character is hiragana
    """
    return '\u3040' <= char <= '\u309f'

def is_katakana(char: str) -> bool:
    """
    Check if a character is katakana
    """
    return '\u30a0' <= char <= '\u30ff'
