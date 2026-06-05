# Multimodal Video Search Engine

This project aims to build a robust multimodal search engine that can search across different videos, extract context, and provide deep learnings and understandings from video content.

## Project Structure
The project is built with a modular, service-oriented architecture:
- `docs/`: Contains detailed documentation for each module.
- `data_pipeline/`: Contains the source code for the data ingestion pipeline module and its output.

## Step-by-step Setup on MacBook Air (Apple Silicon)

1. **Setup Python Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Python Packages**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Videos Pipeline
To run the data ingestion pipeline for YouTube videos:
```bash
python data_pipeline/videos/main.py
```
This will read a list of YouTube URLs and automatically fetch the auto-generated Marathi transcripts directly from YouTube, saving them into clean JSON files in the `data_pipeline/videos/output/` directory.

### 2. Books Pipeline
To run the data extraction pipeline for PDF books:
```bash
python data_pipeline/books/books_main.py
```
Place your PDF books in `data_pipeline/books/input_books/` before running. This parses PDFs, chunks them with page mapping, and enriches them via Gemini.

*Note: For the full end-to-end processing including embeddings and Qdrant database upload, see `data_pipeline/colab/pipeline.ipynb`.*

## Current Modules
- **Module 1**: Audio Ingestion Pipeline (See `docs/01-data-pipeline.md`)
