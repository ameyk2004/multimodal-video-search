# 🕉️ Pethe Kaka — Complete Data Pipeline (Google Colab)

This document contains the exact code cells to run in Google Colab to generate GPU embeddings and upload to Qdrant. By using Google Drive, we ensure your data is permanently backed up and you never lose it if Colab disconnects.

---

## 🔑 Part 1: Colab Setup & Google Drive Mount

Open a fresh notebook at **[colab.research.google.com](https://colab.research.google.com)**. Change the runtime to **T4 GPU** (`Runtime → Change runtime type`).

### 🟦 Cell 1 — Mount Google Drive & Set up Folders
*This mounts your Google Drive so we can read your local files and write backups directly to the cloud.*
```python
from google.colab import drive
import os

# 1. Mount Google Drive
drive.mount('/content/drive')

# 2. Define the permanent Drive folder structure
DRIVE_ROOT = '/content/drive/MyDrive/SadhanaNandadeep_Data'
DRIVE_OUTPUT = os.path.join(DRIVE_ROOT, 'output')
DRIVE_META = os.path.join(DRIVE_ROOT, 'enriched_metadata')
DRIVE_JSON = os.path.join(DRIVE_ROOT, 'enriched_json')

# 3. Create folders if they don't exist
for d in [DRIVE_ROOT, DRIVE_OUTPUT, DRIVE_META, DRIVE_JSON]:
    os.makedirs(d, exist_ok=True)

print(f"✅ Google Drive mounted! Data will be read from and saved to: {DRIVE_ROOT}")
```
> ⚠️ **Prerequisite**: Ensure you have uploaded your local `output/` and `enriched_metadata/` files to your Google Drive `SadhanaNandadeep_Data` folders before continuing.

---

### 🟦 Cell 2 — Install Dependencies & Load Secrets
```python
# Install required libraries
!pip install -q \
    "google-genai>=1.66.0,<2.0.0" \
    langchain==1.3.1 \
    langchain-text-splitters==1.1.2 \
    langchain-core==1.4.0 \
    sentence-transformers \
    torch \
    qdrant-client==1.18.0 \
    youtube-transcript-api \
    python-dotenv \
    tenacity \
    boto3

import os
from google.colab import userdata

# Load secrets into environment (ensure these are added in Colab's 🔑 sidebar)
os.environ["QDRANT_URL"]     = userdata.get("QDRANT_URL")
os.environ["QDRANT_API_KEY"] = userdata.get("QDRANT_API_KEY")

print("✅ Dependencies installed and secrets loaded")
```

---

### 🟦 Cell 3 — Clone the Repository
*Clones your codebase so Colab can run your pipeline scripts.*
```python
import os
from google.colab import userdata

%cd /content
!rm -rf /content/repo

token = userdata.get("GITHUB_TOKEN")
!git clone https://{token}@github.com/ameyk2004/multimodal-video-search.git /content/repo --quiet

# Install the data_pipeline package in editable mode
!pip install -q -e /content/repo

%cd /content/repo
print("✅ Repo cloned and package installed")
```

---

## 🚀 Part 2: GPU Embedding & Upload

### 🟦 Cell 4 — Load GPU Model (BGE-M3)
*Takes ~1 minute. Loads the model onto the T4 GPU.*
```python
import torch
from sentence_transformers import SentenceTransformer

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

print("Loading BGE-M3 embedder...")
embedder = SentenceTransformer("BAAI/bge-m3", device=device)

print("✅ Embedder ready")
```

---

### 🟦 Cell 5 — Chunk & Embed (High-Precision Timestamps)
*Reads raw 2-5s fragments from Google Drive, creates semantic 700-character chunks, adds high-precision timestamps, generates GPU embeddings, and saves the final JSON back to Google Drive.*
```python
import json, os, glob
from data_pipeline.transcript_processor import TranscriptProcessor

processor = TranscriptProcessor()

# Read raw transcripts directly from Google Drive
raw_files = glob.glob(os.path.join(DRIVE_OUTPUT, "*.json"))
print(f"Found {len(raw_files)} raw transcripts to process.")

for filepath in raw_files:
    video_id = os.path.splitext(os.path.basename(filepath))[0]
    out_path = os.path.join(DRIVE_JSON, f"{video_id}_enriched.json")

    # Idempotent: skips if already embedded in Google Drive
    if os.path.exists(out_path):
        print(f"⏭️  Skipping {video_id} — already embedded")
        continue

    print(f"🔄 Processing {video_id}...")
    chunks, char_map, full_text = processor.process_file(filepath, video_id)

    # Embed natively in Marathi
    for chunk in chunks:
        chunk["embedding_vector"] = embedder.encode(chunk["marathi_raw"]).tolist()

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
        
    print(f"  ✅ Saved embedded chunks to Google Drive: {video_id}_enriched.json")

print("\n🎉 Chunking and Embedding complete! All backups saved to Google Drive.")
```

---

### 🟦 Cell 6 — Upload Hybrid Vectors to Qdrant Cloud
*Builds the sparse BM25 vocabulary, configures Qdrant, and uploads both dense and sparse vectors directly from Google Drive.*
```python
from scripts.qdrant_uploader_hybrid import QdrantHybridManager

print("Initializing Qdrant Hybrid Uploader...")
qdrant = QdrantHybridManager(recreate_collection=True)

# Point the uploader directly to the Google Drive folder
print(f"Uploading vectors from {DRIVE_JSON}...")
qdrant.upload_data(input_directory=DRIVE_JSON)

print("\n✅ Qdrant hybrid upload complete! Database is live.")
```

*(Note: We skip the VideoEnricher and DynamoDB steps in Colab because you already ran those locally on your Mac!)*
