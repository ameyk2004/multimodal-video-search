# Data Ingestion Pipeline

## Overview
The Data Ingestion Pipeline is the first module of the Multimodal Search Engine. Its core responsibility is to efficiently fetch Marathi transcripts directly from YouTube and convert them into a structured, timestamped textual format.

## Logic and Architecture

We prioritize **reliability and scalability** over pure speed, specifically tailoring this pipeline to run stably on consumer hardware like a MacBook Air.

### 1. Transcript Fetching (`youtube-transcript-api`)
We use `youtube-transcript-api` to directly pull auto-generated or manually uploaded Marathi (`mr`) subtitles from YouTube.
- **Why use API over local STT?** Local Speech-To-Text models like Whisper can struggle with complex accents, background music, or non-English languages, leading to hallucinations. Fetching transcripts directly from YouTube is exponentially faster, requires zero local compute, and provides highly accurate native Devanagari text.

### 2. Scalability Strategy
- **Lightweight & Fast**: Because we rely entirely on API calls rather than downloading gigabytes of audio and running heavy AI models, processing 100+ videos takes seconds instead of hours. The pipeline is fully equipped with error handling to skip videos without Marathi transcripts or gracefully exit if rate limits are hit.

### 4. Structured Output
The output is a DRY (Don't Repeat Yourself), clean JSON file per video. It contains exactly what we need for the next contextual step:
```json
[
  {
    "text": "जागृत",
    "start_time": 1.92,
    "duration": 4.56
  }
]
```
This structure makes it trivial to map specific search results or learnings back to the exact timestamp in the original video.
