"""
Transcript Chunker Module.
Aggregates fragmented word-level transcripts into rich, semantic chunks.

This is a utility module imported by the main pipeline. To run the full pipeline:
    source venv/bin/activate
    python data_pipeline/main.py
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TranscriptChunker:
    """
    Groups small, word-level or fragmented transcript JSON segments into larger, 
    semantically meaningful chunks based on minimum duration and pause detection.
    """
    
    def __init__(self, min_chunk_duration: float = 30.0, max_chunk_duration: float = 60.0, pause_threshold: float = 1.0, overlap_duration: float = 10.0):
        """
        Args:
            min_chunk_duration (float): Minimum duration (in seconds) a chunk must reach before it can be closed.
            max_chunk_duration (float): Maximum duration (in seconds) before a chunk is forcibly closed, even without a pause.
            pause_threshold (float): Minimum silence (in seconds) between words to be considered a valid break boundary.
            overlap_duration (float): Number of seconds the next chunk should overlap with the previous chunk.
        """
        self.min_chunk_duration = min_chunk_duration
        self.max_chunk_duration = max_chunk_duration
        self.pause_threshold = pause_threshold
        self.overlap_duration = overlap_duration

    def process(self, raw_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes a list of raw transcript segments and returns a list of aggregated chunks with a sliding window overlap.
        
        Expected input format: [{"text": "...", "start_time": float, "duration": float}, ...]
        Returns: [{"text": "...", "start_time": float, "duration": float}, ...]
        """
        if not raw_segments:
            logger.warning("Empty segments list provided to TranscriptChunker.")
            return []
            
        # Filter empty segments first to simplify logic
        segments = [s for s in raw_segments if s.get('text', '').strip()]
        if not segments:
            return []

        logger.info(f"Chunking {len(segments)} segments (Target: {self.min_chunk_duration}s - {self.max_chunk_duration}s, Overlap: {self.overlap_duration}s)")

        chunked_data = []
        start_idx = 0
        n = len(segments)

        while start_idx < n:
            current_chunk_start = segments[start_idx].get('start_time', 0.0)
            end_idx = start_idx
            
            # Find the end of this chunk
            while end_idx < n:
                seg = segments[end_idx]
                current_end_time = seg.get('start_time', 0.0) + seg.get('duration', 0.0)
                accumulated_duration = current_end_time - current_chunk_start
                
                # If we are at the last segment, break and close the chunk
                if end_idx == n - 1:
                    break
                    
                next_seg = segments[end_idx + 1]
                next_start_time = next_seg.get('start_time', 0.0)
                pause_duration = next_start_time - current_end_time
                
                # Check boundary conditions
                if accumulated_duration >= self.max_chunk_duration:
                    break
                elif accumulated_duration >= self.min_chunk_duration and pause_duration >= self.pause_threshold:
                    break
                    
                end_idx += 1
                
            # Build the chunk
            chunk_text = [segments[i].get('text', '').strip() for i in range(start_idx, end_idx + 1)]
            final_end_time = segments[end_idx].get('start_time', 0.0) + segments[end_idx].get('duration', 0.0)
            
            chunked_data.append(self._build_chunk(chunk_text, current_chunk_start, final_end_time))
            
            # If we reached the very end, we are done
            if end_idx == n - 1:
                break
                
            # Slide the window forward: Find the new start_idx for the next chunk
            # We want the new chunk to start roughly `overlap_duration` seconds BEFORE the end of the current chunk.
            target_start_time = max(current_chunk_start, final_end_time - self.overlap_duration)
            
            new_start_idx = end_idx
            while new_start_idx > start_idx:
                if segments[new_start_idx].get('start_time', 0.0) <= target_start_time:
                    break
                new_start_idx -= 1
                
            # Ensure we always make forward progress
            if new_start_idx <= start_idx:
                new_start_idx = start_idx + 1
                
            start_idx = new_start_idx

        logger.info(f"Successfully created {len(chunked_data)} aggregated chunks.")
        return chunked_data

    def _build_chunk(self, text_list: List[str], start_time: float, end_time: float) -> Dict[str, Any]:
        """Helper to construct the final chunk dictionary."""
        return {
            "text": " ".join(text_list),
            "start_time": round(start_time, 3),
            "duration": round(end_time - start_time, 3),
            "type": "video"
        }
