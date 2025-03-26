from typing import List, Dict, Optional
from database import IdiomTranslation
from mnemonic_generator import MnemonicGenerator

class IdiomTranslator:
    def __init__(self, db=None):
        self.db = db
        self.cached_idioms = {}
        self.mnemonic_generator = MnemonicGenerator()

    def add_idiom(self, idiom_data: Dict) -> IdiomTranslation:
        """Add a new idiom translation to the database"""
        return IdiomTranslation.create(self.db, idiom_data)

    def search_idioms(self, query: str) -> List[Dict]:
        """Search for idioms in both Japanese and English"""
        results = IdiomTranslation.search(self.db, query)
        return [self._format_idiom(idiom) for idiom in results]

    def get_all_idioms(self) -> List[Dict]:
        """Get all available idioms"""
        results = IdiomTranslation.get_all(self.db)
        return [self._format_idiom(idiom) for idiom in results]

    def _format_idiom(self, idiom: IdiomTranslation) -> Dict:
        """Format idiom data for display"""
        formatted_idiom = {
            'japanese': idiom.japanese_idiom,
            'literal': idiom.literal_meaning,
            'english': idiom.english_equivalent,
            'explanation': idiom.explanation,
            'example': idiom.usage_example,
            'tags': idiom.tags
        }

        # Generate mnemonic device
        mnemonic = self.mnemonic_generator.generate_mnemonic(
            idiom.japanese_idiom,
            idiom.english_equivalent
        )
        formatted_idiom['mnemonic'] = mnemonic

        return formatted_idiom

    def analyze_text_for_idioms(self, text: str) -> List[Dict]:
        """Find idioms in the given text"""
        idioms = self.get_all_idioms()
        found_idioms = []

        for idiom in idioms:
            if idiom['japanese'] in text:
                found_idioms.append({
                    **idiom,
                    'position': text.index(idiom['japanese'])
                })

        return sorted(found_idioms, key=lambda x: x['position'])