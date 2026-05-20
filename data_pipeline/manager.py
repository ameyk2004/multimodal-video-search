import os
import json
import logging
from typing import List
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, RequestBlocked, IpBlocked

logger = logging.getLogger(__name__)

class YouTubeTranscriptManager:
    """
    Manages the fetching of auto-generated Marathi transcripts from YouTube videos.
    """
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)



    def process_videos(self, video_ids: List[str]) -> dict:
        """
        Iterates over video IDs and fetches Marathi transcripts. Returns a dict mapping video_id to transcript data.
        """
        logger.info(f"Starting transcript fetching pipeline for {len(video_ids)} videos.")
        results = {}
        
        for video_id in video_ids:
            logger.info(f"Fetching transcript for video ID: {video_id}")
            try:
                # Fetch explicitly requesting Marathi
                api = YouTubeTranscriptApi()
                raw_transcript_obj = api.fetch(video_id, languages=['mr'])
                raw_transcript = raw_transcript_obj.fetch() if hasattr(raw_transcript_obj, 'fetch') else raw_transcript_obj
                
                # Format to match the required DRY schema
                formatted_transcript = []
                for entry in raw_transcript:
                    formatted_transcript.append({
                        "text": getattr(entry, 'text', entry.get('text') if isinstance(entry, dict) else None),
                        "start_time": getattr(entry, 'start', entry.get('start') if isinstance(entry, dict) else None),
                        "duration": getattr(entry, 'duration', entry.get('duration') if isinstance(entry, dict) else None)
                    })
                
                results[video_id] = formatted_transcript
                
            except TranscriptsDisabled:
                logger.error(f"Transcripts are disabled for video {video_id}. Skipping.")
            except NoTranscriptFound:
                logger.error(f"No Marathi transcript found for video {video_id}. Skipping.")
            except (RequestBlocked, IpBlocked):
                logger.error(f"YouTube rate limit or block hit while fetching {video_id}. Stopping pipeline.")
                break
            except Exception as e:
                logger.error(f"An unexpected error occurred for video {video_id}: {str(e)}")
                
        logger.info("Transcript fetching pipeline completed.")
        return results
