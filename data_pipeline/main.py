import logging
import os
import sys

# Ensure the root directory is in the path if running from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline import IngestionPipeline

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ingestion.log")
    ]
)

if __name__ == "__main__":
    video_urls = [
        "https://youtu.be/9RAqjOZEOh4?si=bF4sg4TQWnmtJLRI",
        "https://youtu.be/UL0CUMswqBY?si=qGD2S2Na8TU6_Rl1"
    ]
    
    print("Initializing pipeline...")
    print("This may take a moment to load the Whisper model into memory.")
    
    pipeline = IngestionPipeline(output_dir="data_pipeline/output")
    pipeline.process_videos(video_urls)
    
    print("Pipeline execution finished. Check output/ directory and ingestion.log")
