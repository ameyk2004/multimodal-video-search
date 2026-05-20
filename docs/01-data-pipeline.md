# Data Ingestion Pipeline

## Overview
The Data Ingestion Pipeline is the first module of the Multimodal Search Engine. Its core responsibility is to extract audio from YouTube videos and convert it into a structured, timestamped textual format.

## Logic and Architecture

We prioritize **reliability and scalability** over pure speed, specifically tailoring this pipeline to run stably on consumer hardware like a MacBook Air.

### 1. Audio Extraction (`yt-dlp`)
We use `yt-dlp` because it is the most robust and actively maintained open-source YouTube downloader.
- **Why audio only?** Video processing is heavy. Since we primarily care about what is being *spoken* to extract context and learnings, we extract only the audio track, downmixing it to MP3. This saves significant bandwidth and local storage.

### 2. Transcription (`Whisper`)
We use OpenAI's open-source `Whisper` model running locally.
- **Why local?** Running it locally ensures zero recurring API costs for hour-long videos and ensures data privacy. 
- **Hardware Optimization**: On a MacBook Air (Apple Silicon), the code automatically detects `mps` (Metal Performance Shaders) if available via PyTorch, falling back to `cpu`. 

### 3. Scalability Strategy
Handling up to 100 hour-long videos requires careful resource management:
- **Concurrent Downloads**: We download the audio for multiple videos concurrently (I/O bound task) using thread pools.
- **Sequential Transcription**: Transcribing a 1-hour video with Whisper uses a significant amount of RAM/VRAM. To prevent the MacBook Air from crashing (OOM errors), transcribing is done *sequentially*. The pipeline acts as a queue: it downloads fast, but transcribes one by one.

### 4. Structured Output
The output is a DRY (Don't Repeat Yourself), clean JSON file per video. It contains exactly what we need for the next contextual step:
```json
[
  {
    "start_time": 0.0,
    "end_time": 5.2,
    "text": "Hello, welcome to this video about multimodal search."
  }
]
```
This structure makes it trivial to map specific search results or learnings back to the exact timestamp in the original video.
