import logging
import os
import sys
import json
import urllib.parse as urlparse

# Ensure the root directory is in the path if running from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline import YouTubeTranscriptManager, TranscriptChunker

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ingestion.log")
    ]
)

def extract_video_id(url: str) -> str:
    """Extracts the YouTube video ID from a standard YouTube URL."""
    try:
        parsed = urlparse.urlparse(url)
        if parsed.hostname == 'youtu.be':
            return parsed.path[1:]
        if parsed.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
            if parsed.path == '/watch':
                return urlparse.parse_qs(parsed.query)['v'][0]
    except Exception as e:
        logging.error(f"Failed to parse URL {url}: {e}")
    # If parsing fails or it's already an ID, just return the original string
    return url

if __name__ == "__main__":
    # You can now paste full YouTube URLs here!
    video_urls = [
        "https://www.youtube.com/watch?v=9RAqjOZEOh4",
        "https://youtu.be/DdBv99-IWi0?si=oe-6_559ImMx_4fL",
        "https://youtu.be/bb6ip0m6_CA?si=hec0eBpTfEhNCU58",
        "https://youtu.be/BewB6S4JYqo?si=Fat2jbOQPLaESqHr",
        "https://youtu.be/Y4D15z9Z9nU?si=7-Uijpk-vb46Tvm7"
    ]
    
    # Automatically extract IDs from the URLs
    video_ids = [extract_video_id(url) for url in video_urls]
    
    print("Initializing YouTube transcript fetching pipeline...")
    
    manager = YouTubeTranscriptManager(output_dir="data_pipeline/output")
    raw_transcripts = manager.process_videos(video_ids)
    
    print("Initializing chunking pipeline...")
    chunker = TranscriptChunker(min_chunk_duration=30.0, pause_threshold=1.0)
    
    for video_id, raw_data in raw_transcripts.items():
        output_path = f"data_pipeline/output/{video_id}.json"
        
        chunked_data = chunker.process(raw_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunked_data, f, indent=4, ensure_ascii=False)
        print(f"Saved directly chunked transcript for {video_id} to {output_path}")
        
    print("Pipeline execution finished. Check output/ directory and ingestion.log")
