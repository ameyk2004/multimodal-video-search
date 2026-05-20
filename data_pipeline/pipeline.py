import os
import json
import logging
import concurrent.futures
from typing import List

from .downloader import YouTubeDownloader
from .transcriber import WhisperTranscriber

logger = logging.getLogger(__name__)

class IngestionPipeline:
    """
    Orchestrates the entire ingestion process: downloading concurrently and
    transcribing sequentially to manage memory on consumer hardware.
    """
    def __init__(self, output_dir: str = "output", max_concurrent_downloads: int = 3):
        self.output_dir = output_dir
        self.max_concurrent_downloads = max_concurrent_downloads
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.downloader = YouTubeDownloader(output_dir=self.output_dir)
        self.transcriber = WhisperTranscriber(model_size="base")

    def _save_json(self, video_id: str, data: List[dict]):
        json_path = os.path.join(self.output_dir, f"{video_id}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved transcription to {json_path}")

    def process_videos(self, urls: List[str]):
        """
        Process a list of YouTube URLs.
        Downloads are concurrent, transcription is sequential.
        """
        logger.info(f"Starting ingestion pipeline for {len(urls)} videos.")
        
        # Step 1: Download all audio files concurrently
        audio_files = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_downloads) as executor:
            future_to_url = {executor.submit(self.downloader.download_audio, url): url for url in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    audio_path = future.result()
                    audio_files.append(audio_path)
                except Exception as exc:
                    logger.error(f"{url} generated an exception during download: {exc}")

        logger.info(f"Successfully downloaded {len(audio_files)} audio files. Starting transcription...")

        # Step 2: Transcribe sequentially to avoid OOM
        for audio_path in audio_files:
            try:
                # Get the video ID from the filename
                filename = os.path.basename(audio_path)
                video_id = os.path.splitext(filename)[0]
                
                # Transcribe
                structured_data = self.transcriber.transcribe(audio_path)
                
                # Save to JSON
                self._save_json(video_id, structured_data)
                
                # Clean up the mp3 file to save disk space
                os.remove(audio_path)
                logger.info(f"Cleaned up temporary audio file: {audio_path}")
                
            except Exception as e:
                logger.error(f"Failed processing transcription for {audio_path}: {e}")
                
        logger.info("Ingestion pipeline completed.")
