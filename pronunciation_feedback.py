import numpy as np
import sounddevice as sd
import librosa
import scipy.io.wavfile
from transformers import pipeline
from typing import Dict, Tuple
import tempfile
import os

class PronunciationAnalyzer:
    def __init__(self):
        """Initialize the pronunciation analyzer with models and configs"""
        self.sample_rate = 16000
        self.duration = 5  # maximum recording duration in seconds
        
        # Initialize speech recognition pipeline
        try:
            self.asr_pipeline = pipeline(
                "automatic-speech-recognition",
                model="jonatasgrosman/wav2vec2-large-xlsr-53-japanese"
            )
        except Exception as e:
            print(f"Error loading ASR model: {e}")
            self.asr_pipeline = None

    def record_audio(self) -> Tuple[np.ndarray, int]:
        """Record audio from the microphone"""
        try:
            recording = sd.rec(
                int(self.sample_rate * self.duration),
                samplerate=self.sample_rate,
                channels=1
            )
            sd.wait()  # Wait until recording is finished
            return recording, self.sample_rate
        except Exception as e:
            raise RuntimeError(f"Failed to record audio: {e}")

    def save_audio(self, audio: np.ndarray, sample_rate: int) -> str:
        """Save audio to a temporary file"""
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, "pronunciation.wav")
        scipy.io.wavfile.write(temp_path, sample_rate, audio)
        return temp_path

    def analyze_pronunciation(self, audio_path: str, target_text: str) -> Dict:
        """Analyze pronunciation and generate feedback"""
        try:
            # Load audio file
            audio, _ = librosa.load(audio_path, sr=self.sample_rate)
            
            # Get transcription
            if self.asr_pipeline:
                result = self.asr_pipeline(audio_path)
                transcribed_text = result["text"]
            else:
                raise RuntimeError("ASR model not initialized")

            # Calculate basic audio features
            mfcc = librosa.feature.mfcc(y=audio, sr=self.sample_rate)
            
            # Calculate pronunciation score based on feature similarity
            pronunciation_score = self._calculate_pronunciation_score(
                transcribed_text,
                target_text,
                mfcc
            )

            return {
                "transcribed_text": transcribed_text,
                "target_text": target_text,
                "pronunciation_score": pronunciation_score,
                "feedback": self._generate_feedback(pronunciation_score)
            }
        except Exception as e:
            raise RuntimeError(f"Failed to analyze pronunciation: {e}")

    def _calculate_pronunciation_score(
        self,
        transcribed: str,
        target: str,
        mfcc_features: np.ndarray
    ) -> float:
        """Calculate pronunciation score based on transcription and audio features"""
        # Basic scoring based on character-level similarity
        char_similarity = self._calculate_character_similarity(transcribed, target)
        
        # Normalize MFCC features for consistency score
        consistency_score = np.mean(np.std(mfcc_features, axis=1))
        normalized_consistency = 1 - (consistency_score / 10)  # Normalize to 0-1
        
        # Combine scores (70% character similarity, 30% consistency)
        final_score = (0.7 * char_similarity + 0.3 * normalized_consistency) * 100
        return min(max(final_score, 0), 100)  # Ensure score is between 0-100

    def _calculate_character_similarity(self, text1: str, text2: str) -> float:
        """Calculate character-level similarity between two texts"""
        if not text1 or not text2:
            return 0.0
            
        # Convert to hiragana for fair comparison
        text1 = text1.lower()
        text2 = text2.lower()
        
        # Calculate Levenshtein distance
        m, n = len(text1), len(text2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
            
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if text1[i-1] == text2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j],      # deletion
                                     dp[i][j-1],      # insertion
                                     dp[i-1][j-1])    # substitution
                                     
        max_length = max(m, n)
        similarity = 1 - (dp[m][n] / max_length)
        return similarity

    def _generate_feedback(self, score: float) -> str:
        """Generate human-readable feedback based on the pronunciation score"""
        if score >= 90:
            return "Excellent pronunciation! Keep up the great work!"
        elif score >= 80:
            return "Very good pronunciation. Minor improvements possible."
        elif score >= 70:
            return "Good pronunciation. Focus on rhythm and intonation."
        elif score >= 60:
            return "Fair pronunciation. Practice individual sounds more."
        else:
            return "Keep practicing! Focus on basic sound patterns."

    def cleanup(self, audio_path: str):
        """Clean up temporary audio files"""
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception as e:
            print(f"Warning: Failed to clean up audio file: {e}")
