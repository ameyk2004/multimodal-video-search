import os
import logging
import yt_dlp

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    """
    Handles downloading YouTube videos and extracting their audio track.
    """
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def download_audio(self, url: str) -> str:
        """
        Downloads audio from a given YouTube URL.
        Returns the absolute path to the downloaded .mp3 file.
        """
        logger.info(f"Starting download for {url}")
        
        # Configure yt-dlp to extract audio and convert to mp3
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.output_dir, '%(id)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get the video ID
                info_dict = ydl.extract_info(url, download=True)
                video_id = info_dict.get('id', None)
                
                if not video_id:
                    raise Exception("Failed to extract video ID.")
                    
                file_path = os.path.join(self.output_dir, f"{video_id}.mp3")
                logger.info(f"Successfully downloaded audio to {file_path}")
                return file_path
                
        except Exception as e:
            logger.error(f"Error downloading {url}: {str(e)}")
            raise
