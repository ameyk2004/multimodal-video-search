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



    def process_videos(self, video_ids: List[str]) -> dict:
        """
        Iterates over video IDs and fetches Marathi transcripts. Returns a dict mapping video_id to transcript data.
        """
        print(f"\n[YouTubeTranscriptManager] Starting transcript fetching pipeline for {len(video_ids)} videos.")
        results = {}
        
        for video_id in video_ids:
            # Idempotency check: Skip if already processed
            output_file = os.path.join(self.output_dir, f"{video_id}.json")
            if os.path.exists(output_file):
                print(f"[{video_id}] ⏩ SKIPPED: Transcript already exists locally.")
                continue
                
            print(f"[{video_id}] Fetching transcript...")
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
                print(f"[{video_id}] ✅ Successfully extracted transcript (Local API). Length: {len(formatted_transcript)} segments.")
                
            except Exception as e:
                # Fallback to TranscriptAPI.com
                api_key = os.getenv("TRANSCRIPT_API_KEY")
                if api_key:
                    print(f"[{video_id}] ⚠️ Local fetch failed ({type(e).__name__}). Attempting TranscriptAPI fallback...")
                    try:
                        url = f"https://transcriptapi.com/api/v2/youtube/transcript?video_url=https://www.youtube.com/watch?v={video_id}&format=json"
                        headers = {"Authorization": f"Bearer {api_key}"}
                        response = requests.get(url, headers=headers)
                        
                        if response.status_code == 200:
                            data = response.json()
                            if 'segments' in data:
                                formatted_transcript = []
                                for entry in data['segments']:
                                    formatted_transcript.append({
                                        "text": entry.get('text'),
                                        "start_time": entry.get('start'),
                                        "duration": entry.get('duration', 0.0) # Might not be provided by fallback
                                    })
                                results[video_id] = formatted_transcript
                                print(f"[{video_id}] ✅ Successfully extracted transcript (API Fallback). Length: {len(formatted_transcript)} segments.")
                            else:
                                print(f"[{video_id}] ❌ ERROR: Fallback API returned no segments.")
                        else:
                            print(f"[{video_id}] ❌ ERROR: Fallback API request failed with status {response.status_code}: {response.text}")
                    except Exception as fallback_e:
                        print(f"[{video_id}] ❌ ERROR: Fallback API exception: {str(fallback_e)}")
                else:
                    if isinstance(e, TranscriptsDisabled):
                        print(f"[{video_id}] ❌ ERROR: Transcripts are disabled for this video. (No fallback API key provided)")
                    elif isinstance(e, NoTranscriptFound):
                        print(f"[{video_id}] ❌ ERROR: No Marathi transcript found. (No fallback API key provided)")
                    elif isinstance(e, (RequestBlocked, IpBlocked)):
                        print(f"[{video_id}] ❌ CRITICAL: YouTube rate limit or IP block hit! Stopping pipeline. (No fallback API key provided)")
                        break
                    else:
                        print(f"[{video_id}] ❌ ERROR: An unexpected error occurred: {str(e)} (No fallback API key provided)")
                
        print("\n[YouTubeTranscriptManager] Transcript fetching pipeline completed.")
        return results
