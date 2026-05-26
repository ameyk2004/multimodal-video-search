# 🚀 SadhanaNandadeep Data Pipeline Guide

This document explains the step-by-step process for ingesting new YouTube videos, extracting their metadata using AI, and pushing them to your cloud infrastructure.

## 📌 Overview of the Pipeline Steps
1. **Download Transcripts:** Fetch native transcripts from YouTube.
2. **AI Enrichment:** Pass the transcripts to Gemini to extract stories, bhajan segments, topics, etc.
3. **Colab / Local Embeddings:** Generate vector embeddings for Qdrant and upload everything to AWS DynamoDB.

---

## Step 1: Download & Chunk Transcripts
This step fetches the Marathi transcripts for all URLs listed in `main.py` and saves them locally.

**How to run:**
```bash
python data_pipeline/main.py
```
- **What it does:** Reads URLs from `video_urls` in `main.py`, fetches transcripts, chunks them, and saves raw JSON files.
- **Where it saves:** `data_pipeline/output/<video_id>.json`
- **Notes:** It automatically skips videos that have already been downloaded or were uploaded before 2022. It will print a full execution summary when finished.

---

## Step 2: AI Video Enrichment (Gemini)
This step runs the raw transcripts through Google Gemini to extract structural metadata (Stories, Queries, Topics, Actionable Practices, etc.).

**How to run:**
```bash
python -m data_pipeline.video_enricher
```
- **What it does:** Scans `data_pipeline/output/` for all downloaded transcripts and asks Gemini to analyze them.
- **Where it saves:** `data_pipeline/enriched_metadata/<video_id>_meta.json`
- **Notes:** This step is idempotent. If a video is already enriched, it will skip it instantly. It also has a built-in rate-limit protection. It will print a detailed execution summary when finished.

---

## Step 3: Embeddings & Cloud Sync (Colab/Local)
Now that we have the raw transcripts and the enriched metadata, we need to generate dense vectors for semantic search and push all the data to AWS DynamoDB and Qdrant.

**If running locally:**
```bash
python data_pipeline/dynamo_uploader.py
```
*(Make sure your `.env` contains AWS credentials, Qdrant URL/API Keys, and HuggingFace tokens).*

**If running in Google Colab (Recommended for speed):**
1. Zip the `data_pipeline/output/` and `data_pipeline/enriched_metadata/` folders.
2. Upload them to your Colab environment.
3. Run your Colab notebook that uses the `HuggingFaceBgeEmbeddings` model to generate vectors and upload them to Qdrant/DynamoDB.

---

## 🛠️ Troubleshooting

- **YouTube IP Blocked (`RequestBlocked`):** If YouTube blocks your IP during Step 1, the script will automatically pause for 30 seconds. If the block persists, try running the script again after 10 minutes, or switch your Wi-Fi/Mobile Hotspot to get a fresh IP address.
- **Gemini Rate Limits (429 Error):** Step 2 includes artificial randomized delays to prevent rate limits. If Gemini servers are completely overloaded (503 Error), the script will automatically back off exponentially (10s, 20s, 40s) and retry.
