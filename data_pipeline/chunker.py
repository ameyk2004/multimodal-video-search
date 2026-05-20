import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TranscriptChunker:
    """
    Groups small, word-level or fragmented transcript JSON segments into larger, 
    semantically meaningful chunks based on minimum duration and pause detection.
    """
    
    def __init__(self, min_chunk_duration: float = 30.0, max_chunk_duration: float = 60.0, pause_threshold: float = 1.0):
        """
        Args:
            min_chunk_duration (float): Minimum duration (in seconds) a chunk must reach before it can be closed.
            max_chunk_duration (float): Maximum duration (in seconds) before a chunk is forcibly closed, even without a pause.
            pause_threshold (float): Minimum silence (in seconds) between words to be considered a valid break boundary.
        """
        self.min_chunk_duration = min_chunk_duration
        self.max_chunk_duration = max_chunk_duration
        self.pause_threshold = pause_threshold

    def process(self, raw_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes a list of raw transcript segments and returns a list of aggregated chunks.
        
        Expected input format: [{"text": "...", "start_time": float, "duration": float}, ...]
        Returns: [{"text": "...", "start_time": float, "duration": float}, ...]
        """
        if not raw_segments:
            logger.warning("Empty segments list provided to TranscriptChunker.")
            return []
            
        logger.info(f"Chunking {len(raw_segments)} raw segments (Target: {self.min_chunk_duration}s - {self.max_chunk_duration}s, Pause: >{self.pause_threshold}s)")

        chunked_data = []
        
        current_chunk_text = []
        current_chunk_start = raw_segments[0].get('start_time', 0.0)
        current_chunk_end = current_chunk_start + raw_segments[0].get('duration', 0.0)

        for i, segment in enumerate(raw_segments):
            text = segment.get('text', '').strip()
            start_time = segment.get('start_time', 0.0)
            duration = segment.get('duration', 0.0)
            end_time = start_time + duration
            
            # Skip empty text
            if not text:
                continue

            # Append the current segment to the chunk
            current_chunk_text.append(text)
            current_chunk_end = end_time

            # If this is the last segment, we must close the chunk
            if i == len(raw_segments) - 1:
                chunked_data.append(self._build_chunk(current_chunk_text, current_chunk_start, current_chunk_end))
                break

            # Look ahead to see if we should split
            next_segment = raw_segments[i + 1]
            next_start_time = next_segment.get('start_time', 0.0)
            
            # Calculate the pause between the end of this word and start of the next
            pause_duration = next_start_time - current_chunk_end
            
            # Calculate how long our current chunk has been accumulating
            accumulated_duration = current_chunk_end - current_chunk_start
            
            # Boundary Condition: Are we past the max duration, OR (past the min duration AND hit a natural pause)?
            if accumulated_duration >= self.max_chunk_duration or (accumulated_duration >= self.min_chunk_duration and pause_duration >= self.pause_threshold):
                # Close out the current chunk
                chunked_data.append(self._build_chunk(current_chunk_text, current_chunk_start, current_chunk_end))
                
                # Reset for the next chunk
                current_chunk_text = []
                current_chunk_start = next_start_time
                
        logger.info(f"Successfully created {len(chunked_data)} aggregated chunks.")
        return chunked_data

    def _build_chunk(self, text_list: List[str], start_time: float, end_time: float) -> Dict[str, Any]:
        """Helper to construct the final chunk dictionary."""
        return {
            "text": " ".join(text_list),
            "start_time": round(start_time, 3),
            "duration": round(end_time - start_time, 3)
        }
