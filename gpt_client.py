import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

class OpenAIClient:
    """
    A simple client for using OpenAI APIs without requiring the openai package.
    Uses urllib.request instead of requests to minimize dependencies.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def check_api_key(self) -> bool:
        """Check if the API key is available"""
        return bool(self.api_key)
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4o", 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a chat completion using the OpenAI API
        
        Args:
            messages: List of message objects with role and content
            model: The model to use (default: gpt-4o which was released after Claude's training)
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens to generate
            response_format: Optional format specifier (e.g., {"type": "json_object"})
            
        Returns:
            API response as a dictionary
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if response_format:
            payload["response_format"] = response_format
        
        try:
            # Convert payload to JSON string
            data = json.dumps(payload).encode('utf-8')
            
            # Create request object
            req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")
            
            # Make the request
            with urllib.request.urlopen(req) as response:
                # Read and decode the response
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except urllib.error.HTTPError as e:
            # Handle HTTP errors
            error_message = f"HTTP Error: {e.code} - {e.reason}"
            try:
                error_data = json.loads(e.read().decode('utf-8'))
                if 'error' in error_data:
                    error_message = f"API Error: {error_data['error']['message']}"
            except:
                pass
                
            return {
                "error": True,
                "message": error_message
            }
        except urllib.error.URLError as e:
            # Handle URL errors (connection problems)
            return {
                "error": True,
                "message": f"Connection Error: {str(e.reason)}"
            }
        except Exception as e:
            # Handle other exceptions
            return {
                "error": True,
                "message": f"API request failed: {str(e)}"
            }
    
    def extract_content(self, response: Dict[str, Any]) -> str:
        """Extract content from an API response"""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return ""
    
    def check_grammar(self, text: str) -> Dict[str, Any]:
        """
        Analyze Japanese text grammar using GPT model
        
        Args:
            text: Japanese text to analyze
            
        Returns:
            Dictionary with grammar analysis results
        """
        if not self.check_api_key():
            return {
                "error": True,
                "message": "OpenAI API key is not available. Please set the OPENAI_API_KEY environment variable."
            }
        
        # System prompt for grammar checking
        system_prompt = """
        You are a Japanese language teacher specializing in grammar analysis. 
        Analyze the following Japanese text and provide detailed feedback on:

        1. Grammar issues and corrections
        2. Particle usage (が, は, を, etc.)
        3. Verb conjugations
        4. Advanced patterns (conditional forms, passive voice, etc.)
        5. Natural phrasing suggestions
        6. Honorific/polite speech analysis (if applicable)

        Provide an improved version of the text if there are issues.
        
        Format your response as a JSON object with the following structure:
        {
          "grammar_issues": [{"issue": "description", "correction": "suggestion"}],
          "particle_usage": [{"particle": "が/は/を/etc", "usage": "correct/incorrect", "explanation": "why"}],
          "verb_conjugations": [{"verb": "verb", "form": "form used", "correctness": "correct/incorrect", "suggestion": "correction if needed"}],
          "advanced_patterns": [{"pattern": "pattern used", "usage": "correct/incorrect", "explanation": "explanation"}],
          "improved_text": "corrected version of the full text",
          "natural_phrasing": [{"original": "original phrase", "suggestion": "more natural phrasing"}],
          "honorific_polite_speech": [{"expression": "expression", "type": "casual/polite/honorific", "level": "appropriate/too formal/too casual", "alternative": "alternative if needed"}]
        }
        """
        
        # Create messages for the API request
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        
        # Request to use JSON format
        response_format = {"type": "json_object"}
        
        # Make API call
        response = self.chat_completion(
            messages=messages,
            temperature=0.3,  # Lower temperature for more consistent results
            response_format=response_format
        )
        
        # Check for API errors
        if response.get("error", False):
            return {
                "error": True,
                "message": response.get("message", "Unknown error occurred during analysis.")
            }
        
        # Extract and parse the content
        try:
            content = self.extract_content(response)
            return json.loads(content)
        except (json.JSONDecodeError, TypeError) as e:
            return {
                "error": True,
                "message": f"Failed to parse response: {str(e)}"
            }
    
    def generate_practice_examples(self, grammar_point: str, difficulty: str = "中級") -> List[Dict[str, str]]:
        """
        Generate practice examples for a specific grammar point
        
        Args:
            grammar_point: The grammar point to generate examples for
            difficulty: Difficulty level (初級, 中級, 上級)
            
        Returns:
            List of practice examples with questions and answers
        """
        if not self.check_api_key():
            return [{"error": "OpenAI API key is not available."}]
        
        system_prompt = f"""
        You are a Japanese language teacher creating practice examples for the grammar point: {grammar_point}.
        Create {5} practice examples at the {difficulty} difficulty level.
        
        Format your response as a JSON array with the following structure for each example:
        [
          {{
            "japanese_question": "Fill-in-the-blank question in Japanese",
            "english_translation": "English translation of the question",
            "options": ["option1", "option2", "option3", "option4"],
            "correct_answer": "correct option",
            "explanation": "Explanation of why this is correct"
          }},
          ...
        ]
        """
        
        # Create messages for the API request
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create practice examples for {grammar_point} at {difficulty} level."}
        ]
        
        # Request to use JSON format
        response_format = {"type": "json_object"}
        
        # Make API call
        response = self.chat_completion(
            messages=messages,
            temperature=0.7,
            response_format=response_format
        )
        
        # Check for API errors
        if response.get("error", False):
            return [{"error": response.get("message", "Unknown error occurred.")}]
        
        # Extract and parse the content
        try:
            content = self.extract_content(response)
            return json.loads(content)
        except (json.JSONDecodeError, TypeError) as e:
            return [{"error": f"Failed to parse response: {str(e)}"}]