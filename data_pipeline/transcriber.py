import whisper
import torch
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class WhisperTranscriber:
    """
    Handles transcribing audio files using the local Whisper model.
    Optimized to use Apple MPS (Metal) if available.
    """
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.device = self._get_device()
        
        logger.info(f"Loading Whisper '{self.model_size}' model on {self.device}...")
        try:
            # Note: We pass standard fp16=False for CPU to avoid warnings, but it's handled internally usually.
            self.model = whisper.load_model(self.model_size, device=self.device)
            logger.info("Whisper model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            raise

    def _get_device(self) -> str:
        """Determines the best available processing device."""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def transcribe(self, audio_path: str) -> List[Dict]:
        """
        Transcribes the audio file and returns a structured list of sentences.
        """
        logger.info(f"Starting transcription for {audio_path}")
        
        try:
            # We enforce fp16=False if running on CPU to avoid warnings, but mps supports it
            fp16 = True if self.device != "cpu" else False
            result = self.model.transcribe(audio_path, fp16=fp16)
            
            structured_data = []
            for segment in result['segments']:
                structured_data.append({
                    "start_time": segment['start'],
                    "end_time": segment['end'],
                    "original_text": segment['text'].strip()
                })
                
            logger.info(f"Transcription complete for {audio_path}. Found {len(structured_data)} segments.")
            return structured_data
            
        except Exception as e:
            logger.error(f"Error transcribing {audio_path}: {str(e)}")
            raise
