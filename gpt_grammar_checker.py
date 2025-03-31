import os
import json
from typing import Dict, List, Any

# Try to import OpenAI, but gracefully handle if not installed
OPENAI_AVAILABLE = False
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    pass

class GPTGrammarChecker:
    def __init__(self):
        """Initialize the GPT grammar checker with OpenAI API"""
        if not OPENAI_AVAILABLE:
            self.openai_error = "OpenAI package is not installed. Please install it with: pip install openai"
            self.client = None
        else:
            self.openai_error = None
            self.api_key = os.environ.get("OPENAI_API_KEY")
            if not self.api_key:
                self.openai_error = "OPENAI_API_KEY environment variable is not set"
                self.client = None
            else:
                self.client = OpenAI(api_key=self.api_key)
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
    
    def check_grammar(self, text: str) -> Dict[str, Any]:
        """
        Analyze Japanese text grammar using OpenAI's GPT model
        
        Args:
            text: Japanese text to analyze
            
        Returns:
            Dictionary with grammar analysis results
        """
        # Check if OpenAI is available
        if not OPENAI_AVAILABLE or self.client is None:
            return {
                "error": True,
                "message": self.openai_error or "OpenAI client not initialized",
                "grammar_issues": [],
                "particle_usage": [],
                "verb_conjugations": [],
                "honorific_polite_speech": [],
                "overall_assessment": {
                    "naturalness": 0,
                    "formality": 0,
                    "clarity": 0
                },
                "improved_text": text
            }
            
        system_prompt = """
        あなたは日本語文法の専門家です。以下の日本語テキストの文法をチェックしてください。
        結果は常に以下のJSONフォーマットで返してください：
        {
            "grammar_issues": [
                {
                    "error_text": "誤った表現",
                    "correct_text": "正しい表現",
                    "explanation": "なぜ間違いなのかの説明",
                    "rule": "適用される文法規則"
                }
            ],
            "particle_usage": [
                {
                    "particle": "使われている助詞",
                    "usage_context": "文脈中の使用方法",
                    "correct": true/false,
                    "suggestion": "改善案（誤りの場合）"
                }
            ],
            "verb_conjugations": [
                {
                    "verb": "使われている動詞",
                    "form": "活用形（辞書形、テ形、タ形など）",
                    "correct": true/false,
                    "suggestion": "改善案（誤りの場合）"
                }
            ],
            "honorific_polite_speech": [
                {
                    "expression": "敬語/丁寧語表現",
                    "type": "種類（謙譲語、尊敬語、丁寧語）",
                    "level": "フォーマリティレベル（カジュアル、標準、フォーマル、非常にフォーマル）",
                    "alternative": "別の言い方の提案（あれば）"
                }
            ],
            "overall_assessment": {
                "naturalness": 1-5,
                "formality": 1-5,
                "clarity": 1-5
            },
            "improved_text": "提案された改善文"
        }
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            # Return error information if API call fails
            return {
                "error": True,
                "message": f"Error in GPT analysis: {str(e)}",
                "grammar_issues": [],
                "particle_usage": [],
                "verb_conjugations": [],
                "honorific_polite_speech": [],
                "overall_assessment": {
                    "naturalness": 0,
                    "formality": 0,
                    "clarity": 0
                },
                "improved_text": text
            }
    
    def get_detailed_explanation(self, issue: str, original_text: str) -> str:
        """
        Get a detailed explanation for a specific grammar issue
        
        Args:
            issue: The grammar issue to explain
            original_text: The original text for context
            
        Returns:
            Detailed explanation of the grammar rule and how to use it correctly
        """
        # Check if OpenAI is available
        if not OPENAI_AVAILABLE or self.client is None:
            return self.openai_error or "OpenAI client not initialized"
            
        try:
            prompt = f"""
            以下の日本語文法のポイントについて、詳しく説明してください：
            
            文法ポイント：{issue}
            
            元のテキスト：{original_text}
            
            説明には以下を含めてください：
            1. この文法規則の基本的な説明
            2. 正しい使い方の例（少なくとも3つ）
            3. よくある間違いとその修正方法
            4. 似ている表現との違い（あれば）
            5. 学習者向けのアドバイス
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"エラーが発生しました: {str(e)}"
    
    def generate_practice_examples(self, grammar_point: str, difficulty: str = "中級") -> List[Dict[str, str]]:
        """
        Generate practice examples for a specific grammar point
        
        Args:
            grammar_point: The grammar point to generate examples for
            difficulty: Difficulty level (初級, 中級, 上級)
            
        Returns:
            List of practice examples with questions and answers
        """
        # Check if OpenAI is available
        if not OPENAI_AVAILABLE or self.client is None:
            return [{"error": self.openai_error or "OpenAI client not initialized"}]
            
        try:
            prompt = f"""
            以下の日本語文法ポイントの練習問題を{difficulty}レベルで3つ作成してください：
            
            文法ポイント：{grammar_point}
            
            結果は以下のJSONフォーマットで返してください：
            [
                {{
                    "question": "問題文（空欄あり）",
                    "options": ["選択肢1", "選択肢2", "選択肢3", "選択肢4"],
                    "correct_answer": "正解の選択肢",
                    "explanation": "解説"
                }}
            ]
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            return [{"error": f"エラーが発生しました: {str(e)}"}]