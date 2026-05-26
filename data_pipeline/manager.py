"""
YouTube Transcript Manager Module.
Provides functionality to fetch and format transcripts from YouTube videos.

This is a utility module imported by the main pipeline. To run the full pipeline:
    source venv/bin/activate
    python data_pipeline/main.py
"""
import os
import json
import logging
import requests
from typing import List
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, RequestBlocked, IpBlocked
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class YouTubeTranscriptManager:
    """
    Manages the fetching of auto-generated Marathi transcripts from YouTube videos.
    """
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)



    def _get_video_upload_date(self, video_id: str) -> str:
        """
        Extracts the upload date from the YouTube video page html.
        """
        import re
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            match = re.search(r"\"uploadDate\":\"(.*?)\"", resp.text)
            if match:
                return match.group(1) # e.g. '2023-08-25T00:00:00-07:00'
        except Exception as e:
            logger.warning(f"[{video_id}] Failed to fetch upload date: {e}")
        return ""

    def process_videos(self, video_ids: List[str]) -> tuple[dict, dict]:
        """
        Iterates over video IDs and fetches Marathi transcripts. 
        Returns a tuple of (results_dict, stats_dict).
        """
        print(f"\n[YouTubeTranscriptManager] Starting transcript fetching pipeline for {len(video_ids)} videos.")
        results = {}
        stats = {
            "total_given": len(video_ids),
            "success": 0,
            "skipped_already_exists": 0,
            "skipped_pre2022": 0,
            "error_transcript_not_found": 0,
            "error_no_native_marathi": 0,
            "error_other": 0
        }
        
        for video_id in video_ids:
            # Idempotency check: Skip if already processed
            output_file = os.path.join(self.output_dir, f"{video_id}.json")
            if os.path.exists(output_file):
                print(f"[{video_id}] ⏩ SKIPPED: Transcript already exists locally.")
                stats["skipped_already_exists"] += 1
                continue
                
            upload_date = self._get_video_upload_date(video_id)
            if upload_date:
                try:
                    # Parse the year from the date string (e.g. "2020-05-07...")
                    year = int(upload_date.split("-")[0])
                    if year < 2022:
                        print(f"[{video_id}] ⏩ SKIPPED: Uploaded before 2022 (exact date: {upload_date}).")
                        stats["skipped_pre2022"] += 1
                        continue
                except Exception:
                    pass

            print(f"[{video_id}] Fetching transcript (Upload Date: {upload_date or 'Unknown'})...")
            try:
                # Use api.list to see all available transcripts
                api = YouTubeTranscriptApi()
                transcript_list = api.list(video_id)
                
                # First, try to find a native Marathi transcript
                try:
                    transcript = transcript_list.find_transcript(['mr'])
                except NoTranscriptFound:
                    # If not found, just print what languages exist and skip
                    available_langs = [t.language_code for t in transcript_list]
                    print(f"[{video_id}] ℹ️ Native Marathi not found. Available languages: {', '.join(available_langs)}")
                    stats["error_no_native_marathi"] += 1
                    continue
                    
                raw_transcript = transcript.fetch()
                
                # Format to match the required DRY schema
                formatted_transcript = []
                for entry in raw_transcript:
                    formatted_transcript.append({
                        "text": getattr(entry, 'text', entry.get('text') if isinstance(entry, dict) else None),
                        "start_time": getattr(entry, 'start', entry.get('start') if isinstance(entry, dict) else None),
                        "duration": getattr(entry, 'duration', entry.get('duration') if isinstance(entry, dict) else None)
                    })
                
                results[video_id] = formatted_transcript
                stats["success"] += 1
                print(f"[{video_id}] ✅ Successfully extracted transcript. Length: {len(formatted_transcript)} segments.")
                
            except Exception as e:
                if isinstance(e, TranscriptsDisabled):
                    print(f"[{video_id}] ❌ ERROR: Transcripts are completely disabled for this video.")
                    stats["error_transcript_not_found"] += 1
                elif isinstance(e, NoTranscriptFound):
                    print(f"[{video_id}] ❌ ERROR: No transcript found.")
                    stats["error_transcript_not_found"] += 1
                elif isinstance(e, (RequestBlocked, IpBlocked)):
                    print(f"[{video_id}] ❌ CRITICAL: YouTube rate limit or IP block hit! Taking a long pause...")
                    stats["error_other"] += 1
                    import time
                    time.sleep(30) # Wait 30 seconds before trying the next to cool down
                    continue
                else:
                    print(f"[{video_id}] ❌ ERROR: An unexpected error occurred: {str(e)}")
                    stats["error_other"] += 1
                    
            # Add artificial delay to avoid hammering YouTube and getting IP blocked
            import time
            import random
            sleep_duration = random.uniform(2.0, 5.0)
            time.sleep(sleep_duration)
                
        print("\n[YouTubeTranscriptManager] Transcript fetching pipeline completed.")
        return results, stats
