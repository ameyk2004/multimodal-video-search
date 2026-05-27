# 🚀 SadhanaNandadeep Data Pipeline Guide

This document explains the step-by-step process for ingesting new YouTube videos, extracting their metadata using AI, generating embeddings, and syncing them to AWS DynamoDB and Qdrant Cloud.

---

## 📌 Phase 1: Local Mac Execution (Fetching & Metadata Enrichment)

Because downloading transcripts from Google Colab usually hits a YouTube IP block, we run the initial fetching and metadata extraction steps locally on your Mac.

### Step 1: Clean Old Data (Crucial)
Before running the pipeline on new videos, delete your old data to avoid re-processing or mixing formats.
```bash
rm -rf data_pipeline/output/
```

### Step 2: Fetch Raw YouTube Transcripts (Local)
Fetches fine-grained (2-5 second) Marathi transcripts for the URLs listed in `data_pipeline/main.py`.
```bash
python data_pipeline/main.py
```
*   **What it does:** Reads URLs from `main.py`, fetches transcripts using `youtube-transcript-api`, and saves the raw, fine-grained fragments directly.
*   **Saves to:** `data_pipeline/output/<video_id>.json`
*   **Accuracy Note:** We no longer chunk at this stage! Preserving the raw 2-5s fragments ensures sub-second accuracy for Qdrant and DynamoDB.

### Step 3: AI Video Enrichment (Local)
Uses Google Gemini to extract stories, topics, queries, and actionable spiritual practices from the raw transcripts.
```bash
python -m data_pipeline.video_enricher
```
*   **What it does:** Scans `data_pipeline/output/` for raw transcripts and runs them through Gemini. It then maps the extracted stories/music to the highly accurate 2-5s timestamps.
*   **Saves to:** `data_pipeline/enriched_metadata/<video_id>_meta.json`

### Step 4: Sync Metadata to AWS DynamoDB (Local)
Uploads the structural metadata (topics, stories, etc.) to your AWS DynamoDB tables.
```bash
python scripts/dynamo_uploader.py
```

### Step 5: Embed & Upload Search Queries to Qdrant (Local)
Processes queries uploaded to DynamoDB, embeds them, and syncs them to Qdrant.
```bash
python scripts/embed_queries.py
```
*   **Idempotent:** It queries Qdrant first and skips any queries that are already present in the collection.

---

## 📦 Phase 2: Move Data to Google Drive

Instead of manually uploading zip files to Colab every time, we will use your Google Drive. This acts as a permanent, safe backup and makes the Colab pipeline incredibly simple.

1. Open **Google Drive** in your browser.
2. Create a folder named `SadhanaNandadeep_Data`.
3. Inside `SadhanaNandadeep_Data`, create two empty folders:
   - `output`
   - `enriched_metadata`
4. Copy the `.json` files from your Mac's `data_pipeline/output/` folder into the Drive `output` folder.
5. Copy the `.json` files from your Mac's `data_pipeline/enriched_metadata/` folder into the Drive `enriched_metadata` folder.

*Now your data is safely backed up in the cloud, and Colab can read it directly!*

---

## ☁️ Phase 3: Run the Colab Notebook

Google Colab provides the GPU needed to run the `BAAI/bge-m3` embedding model for your video chunks. 

Open your Colab notebook and follow the `COLAB_PIPELINE.md` instructions. The Colab notebook has been updated to mount your Google Drive automatically, meaning you don't have to upload or unzip anything manually anymore!
