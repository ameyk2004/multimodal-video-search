import logging
import os
import sys
import urllib.parse as urlparse

# Ensure the root directory is in the path if running from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline import YouTubeTranscriptManager

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
        # "https://www.youtube.com/watch?v=9RAqjOZEOh4",
        "https://youtu.be/DdBv99-IWi0?si=oe-6_559ImMx_4fL"
    ]
    
    # Automatically extract IDs from the URLs
    video_ids = [extract_video_id(url) for url in video_urls]
    
    print("Initializing YouTube transcript fetching pipeline...")
    
    pipeline = YouTubeTranscriptManager(output_dir="data_pipeline/output")
    pipeline.process_videos(video_ids)
    
    print("Pipeline execution finished. Check output/ directory and ingestion.log")
