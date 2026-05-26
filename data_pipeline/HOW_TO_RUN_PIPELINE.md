# 🚀 SadhanaNandadeep Data Pipeline Guide

This document explains the step-by-step process for ingesting new YouTube videos, extracting their metadata using AI, generating embeddings, and syncing them to AWS DynamoDB and Qdrant Cloud.

---

## 📌 Phase 1: Local Mac Execution (Fetching & Metadata Enrichment)

Because downloading transcripts can hit IP blocks and query extraction is lightweight, we run these initial metadata steps locally on your Mac.

### Step 1: Fetch YouTube Transcripts (Local)
Fetches Marathi transcripts for the URLs listed in `data_pipeline/main.py`.
```bash
python data_pipeline/main.py
```
*   **What it does:** Reads URLs from `main.py`, fetches transcripts using `youtube-transcript-api`, chunks them, and saves raw JSON files.
*   **Saves to:** `data_pipeline/output/<video_id>.json`
*   **IP Block Note:** If YouTube blocks your IP (you see `youtube_transcript_api._errors.IpBlocked`), wait a few minutes, restart your router/mobile hotspot for a fresh IP, or simply proceed to the next steps with whichever files were successfully fetched.

### Step 2: AI Video Enrichment (Local)
Uses Google Gemini to extract stories, topics, queries, and actionable spiritual practices from the raw transcripts.
```bash
python -m data_pipeline.video_enricher
```
*   **What it does:** Scans `data_pipeline/output/` for raw transcripts and runs them through Gemini.
*   **Saves to:** `data_pipeline/enriched_metadata/<video_id>_meta.json`
*   **Notes:** This step is idempotent. Already-enriched videos are skipped automatically.

### Step 3: Sync Metadata to AWS DynamoDB (Local)
Uploads the structural metadata (topics, stories, etc.) to your AWS DynamoDB tables.
```bash
python data_pipeline/dynamo_uploader.py
```
*   **What it does:** Scans `data_pipeline/enriched_metadata/` and syncs them to DynamoDB.

### Step 4: Embed & Upload Search Queries to Qdrant (Local)
Processes queries uploaded to DynamoDB, embeds them, and syncs them to Qdrant.
```bash
python scripts/embed_queries.py
```
*   **What it does:** Scans your live DynamoDB table (`sadhananandadeep-content`) to retrieve all uploaded queries, prints the total unique count, prompts you for confirmation, calls the Hugging Face API to generate embeddings, and uploads them to the `sadhananandadeep-queries` collection in Qdrant.
*   **Idempotent:** It queries Qdrant first and skips any queries that are already present in the collection, saving time and Hugging Face API quota.

---

## 📦 Phase 2: Zip & Move to Google Colab (GPU Chunk Embedding)

Generating vector embeddings for thousands of individual video chunks using `BAAI/bge-m3` requires a GPU (doing this on a Mac CPU is extremely slow). Therefore, we perform the chunk-level vectorization in Google Colab.

### Step 1: Zip the Local Transcripts
On your Mac, zip your raw transcripts folder:
```bash
zip -r output.zip data_pipeline/output/
```
*(Run this command from the project root directory. This creates `output.zip` containing your local transcript JSONs).*

### Step 2: Upload to Colab
1. Open your Google Colab notebook.
2. Click the **📁 Folder icon** in the left sidebar.
3. Drag and drop the `output.zip` file directly into the `/content` folder (outside the `repo` folder).

---

## ☁️ Phase 3: Run the Colab Notebook

Follow this checklist to run the notebook cells top-to-bottom:

1.  **Run Cell 1 (Install Dependencies):** Installs PyTorch, Qdrant client, SentenceTransformers, etc.
2.  **Run Cell 2 (Clone Repo & Load Secrets):** Clones your private GitHub repo and sets up API keys and AWS credentials.
3.  **Run the Unzip Code Cell:**
    Create a new code cell in Colab (below Cell 2 and above Cell 4), paste the following Python script, and run it to extract your uploaded transcripts:
    ```python
    import zipfile
    import os
    import shutil

    zip_path = '/content/output.zip'
    dest_dir = '/content/repo/data_pipeline/output'

    if os.path.exists(zip_path):
        print(f"Found {zip_path}, extracting...")
        temp_dir = '/content/temp_extract'
        os.makedirs(temp_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Recursively find all JSON files and copy them to dest_dir
        json_count = 0
        os.makedirs(dest_dir, exist_ok=True)
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.json'):
                    src = os.path.join(root, file)
                    dst = os.path.join(dest_dir, file)
                    shutil.copy2(src, dst)
                    json_count += 1
                    
        shutil.rmtree(temp_dir)
        print(f"✅ Successfully extracted and moved {json_count} transcript JSON files to {dest_dir}!")
    else:
        print(f"❌ Error: {zip_path} not found. Please drag and drop it into Colab's left sidebar.")
    ```
4.  **⏭️ SKIP Cell 3 (Fetch YouTube Transcripts):** Since you uploaded your local transcripts in the zip file, you do not need to download them again in Colab.
5.  **Run Cell 4 (VideoEnricher):** Uses Gemini to generate enrichment metadata on Colab.
    *   *Note:* Running this on Colab is fast and fine. (Alternatively, if you also zipped and uploaded your local `enriched_metadata/` folder, you can skip this cell).
6.  **Run Cell 5 (Load GPU Model):** Loads the `BAAI/bge-m3` embedding model onto the Colab T4 GPU.
7.  **Run Cell 6 (Chunk & Embed):** Generates dense vector embeddings for all video chunks using the GPU and saves them to `enriched_json/`.
8.  **Run Cell 7 (Upload to Qdrant Cloud):** Uploads the chunk vectors to your main `guru-videos` collection in Qdrant.
9.  **⏭️ SKIP Cell 8 (Upload Metadata to DynamoDB):** You can skip this since you already uploaded your metadata to DynamoDB from your local Mac in Phase 1 (Step 3).

🎉 **Finally Done!** Your video search database is now fully updated and live!
