from typing import Dict, List, Tuple, Union
import re
import json

class MnemonicGenerator:
    def __init__(self):
        self.kanji_meanings = {
            '手': 'hand',
            '目': 'eye',
            '口': 'mouth',
            '心': 'heart',
            '耳': 'ear',
            '足': 'foot',
            # Add more common kanji meanings
        }

        self.sound_patterns = {
            'たい': 'tie',
            'かい': 'kai (like "sky")',
            'せい': 'say',
            'とう': 'toe',
            # Add more sound patterns
        }

    def generate_mnemonic(self, idiom: str, meaning: str) -> Dict[str, Union[str, List[Dict[str, str]], List[str]]]:
        """Generate a mnemonic device for a Japanese idiom"""
        components = self._break_down_idiom(idiom)
        sound_similarities = self._find_sound_similarities(idiom)
        visual_cues = self._identify_visual_elements(components)

        # Create the mnemonic story
        mnemonic = self._create_mnemonic_story(
            components,
            sound_similarities,
            visual_cues,
            meaning
        )

        return {
            'original_idiom': idiom,
            'components': components,
            'sound_hints': sound_similarities,
            'visual_cues': visual_cues,
            'mnemonic_story': mnemonic,
            'practice_tip': self._generate_practice_tip(idiom, meaning)
        }

    def _break_down_idiom(self, idiom: str) -> List[Dict[str, str]]:
        """Break down the idiom into meaningful components"""
        components = []
        current_component = ''

        for char in idiom:
            if self._is_kanji(char):
                if current_component:
                    components.append({
                        'text': current_component,
                        'type': 'kana'
                    })
                    current_component = ''
                components.append({
                    'text': char,
                    'type': 'kanji',
                    'meaning': self.kanji_meanings.get(char, 'unknown')
                })
            else:
                current_component += char

        if current_component:
            components.append({
                'text': current_component,
                'type': 'kana'
            })

        return components

    def _find_sound_similarities(self, idiom: str) -> List[Dict[str, str]]:
        """Find similar-sounding English words"""
        similarities = []

        for jp_sound, en_sound in self.sound_patterns.items():
            if jp_sound in idiom:
                similarities.append({
                    'japanese': jp_sound,
                    'english': en_sound,
                    'position': idiom.index(jp_sound)
                })

        return sorted(similarities, key=lambda x: x['position'])

    def _identify_visual_elements(self, components: List[Dict[str, str]]) -> List[str]:
        """Identify visual elements that can aid memory"""
        visual_cues = []

        for component in components:
            if component['type'] == 'kanji':
                if component['meaning'] != 'unknown':
                    visual_cues.append(f"'{component['text']}' looks like {component['meaning']}")

        return visual_cues

    def _create_mnemonic_story(
        self,
        components: List[Dict[str, str]],
        sound_similarities: List[Dict[str, str]],
        visual_cues: List[str],
        meaning: str
    ) -> str:
        """Create a memorable story combining all elements"""
        story_parts = []

        # Add sound-based hints
        if sound_similarities:
            sound_part = "Sounds like: " + ", ".join(
                f"'{s['japanese']}' sounds like '{s['english']}'"
                for s in sound_similarities
            )
            story_parts.append(sound_part)

        # Add visual cues
        if visual_cues:
            story_parts.append("Visual hints: " + ", ".join(visual_cues))

        # Create a narrative connecting to the meaning
        meaning_connection = f"Think of it this way: {meaning}"
        story_parts.append(meaning_connection)

        return "\n".join(story_parts)

    def _generate_practice_tip(self, idiom: str, meaning: str) -> str:
        """Generate a practice tip for remembering the idiom"""
        return (
            f"Try creating a mental image that connects '{idiom}' with its meaning: '{meaning}'. "
            "Practice using it in a sentence and try to recall the visual and sound hints."
        )

    def _is_kanji(self, char: str) -> bool:
        """Check if a character is a kanji"""
        return '\u4e00' <= char <= '\u9fff'