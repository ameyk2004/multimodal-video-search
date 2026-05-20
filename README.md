# Multimodal Video Search Engine

This project aims to build a robust multimodal search engine that can search across different videos, extract context, and provide deep learnings and understandings from video content.

## Project Structure
The project is built with a modular, service-oriented architecture:
- `docs/`: Contains detailed documentation for each module.
- `data_pipeline/`: Contains the source code for the data ingestion pipeline module and its output.

## Step-by-step Setup on MacBook Air (Apple Silicon)

1. **Install System Dependencies**
   The audio pipeline requires `ffmpeg`. Install it via Homebrew:
   ```bash
   brew install ffmpeg
   ```

2. **Setup Python Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python Packages**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the data ingestion pipeline (Module 1):
```bash
python data_pipeline/main.py
```
This will read a list of YouTube URLs, download their audio, and use the local Whisper model to transcribe them into clean JSON files in the `data_pipeline/output/` directory.

## Current Modules
- **Module 1**: Audio Ingestion Pipeline (See `docs/01-data-pipeline.md`)
