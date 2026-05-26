# 🕉️ Pethe Kaka — Complete Data Pipeline (100% Google Colab)

No local Mac work required. Open Colab, run 8 cells top-to-bottom, done.

---

## 🔑 Part 1: One-Time Credential Setup

Generate these four credentials once. You will add them to Colab Secrets (never hardcode them in code).

### 1. GitHub Personal Access Token (PAT)
Colab needs this to clone your private repository.

1. **GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. Click **"Generate new token (classic)"**
3. Name: `colab-pipeline` | Expiry: `90 days` | Scope: tick only ✅ **`repo`**
4. Click **Generate** → **Copy immediately** (shown only once)

### 2. Gemini API Key
Used by `VideoEnricher` to extract topics, queries, and stories.

1. Go to → **[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)**
2. Click **"Create API key"** → Copy it

### 3. Qdrant Cloud URL + API Key
1. Go to → **[cloud.qdrant.io](https://cloud.qdrant.io)** → Create a free cluster
2. From your cluster dashboard copy:
   - **Cluster URL** e.g. `https://xxxx.us-east4-0.gcp.cloud.qdrant.io`
   - **API Key** → Access → API Keys → Create Key → Copy

### 4. AWS Access Keys
Colab needs this to upload the extracted metadata to DynamoDB.
1. **AWS Console → IAM → Users** → Select your user → **Security credentials**
2. Click **"Create access key"** (CLI use case) → Copy **Access Key ID** and **Secret Access Key**
3. Keep track of your default region (e.g., `us-east-1`).

---

## ☁️ Part 2: Colab One-Time Setup (Do This Once Per Colab Session)

### Step A: Enable GPU
**Runtime → Change runtime type → T4 GPU → Save**

### Step B: Add Secrets to Colab
Click the 🔑 **key icon** in the left sidebar:

| Secret Name | Value |
|---|---|
| `GITHUB_TOKEN` | Your GitHub PAT |
| `GEMINI_API_KEY` | Your Gemini API Key |
| `QDRANT_URL` | Your Qdrant Cluster URL |
| `QDRANT_API_KEY` | Your Qdrant API Key |
| `AWS_ACCESS_KEY_ID` | Your AWS Access Key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS Secret Key |
| `AWS_DEFAULT_REGION` | Your AWS Region (e.g., us-east-1) |

Enable the toggle "Notebook access" for each secret after adding it.

---

## 🚀 Part 3: Run the Pipeline (Top to Bottom)

Open a fresh notebook at **[colab.research.google.com](https://colab.research.google.com)**.

---

### 🟦 Cell 1 — Install All Dependencies
```python
# Colab pre-installs google-cloud-aiplatform and google-adk which both require
# google-genai<2.0.0 — pin explicitly to avoid resolver conflicts
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

print("✅ Done")
```

---

### 🟦 Cell 2 — Clone Repo & Load Secrets
```python
import os
import shutil
from google.colab import userdata

# Load secrets into environment
os.environ["GEMINI_API_KEY"] = userdata.get("GEMINI_API_KEY")
os.environ["QDRANT_URL"]     = userdata.get("QDRANT_URL")
os.environ["QDRANT_API_KEY"] = userdata.get("QDRANT_API_KEY")

os.environ["AWS_ACCESS_KEY_ID"]     = userdata.get("AWS_ACCESS_KEY_ID")
os.environ["AWS_SECRET_ACCESS_KEY"] = userdata.get("AWS_SECRET_ACCESS_KEY")
os.environ["AWS_DEFAULT_REGION"]    = userdata.get("AWS_DEFAULT_REGION")

# 1. Backup any existing processed data
dirs_to_preserve = [
    "/content/repo/data_pipeline/output",
    "/content/repo/data_pipeline/enriched_json",
    "/content/repo/data_pipeline/enriched_metadata"
]

for d in dirs_to_preserve:
    if os.path.exists(d):
        backup_path = f"/content/backup_{os.path.basename(d)}"
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
        shutil.copytree(d, backup_path)
        print(f"📦 Backed up existing data: {os.path.basename(d)}")

# Step out of /content/repo FIRST before deleting it —
# otherwise the kernel loses its cwd and git/pip break.
%cd /content
!rm -rf /content/repo

token = userdata.get("GITHUB_TOKEN")
!git clone https://{token}@github.com/ameyk2004/multimodal-video-search.git /content/repo --quiet

# 2. Restore processed data
for d in dirs_to_preserve:
    backup_path = f"/content/backup_{os.path.basename(d)}"
    if os.path.exists(backup_path):
        if os.path.exists(d):
            shutil.rmtree(d)
        shutil.copytree(backup_path, d)
        print(f"♻️ Restored data: {os.path.basename(d)}")

# Install the data_pipeline package in editable mode.
# This registers it with Python's import system — no sys.path needed.
!pip install -q -e /content/repo

%cd /content/repo
print("✅ Repo cloned, data restored, package installed, secrets loaded")
```

---

### 🟦 Cell 3 — Fetch YouTube Transcripts
*Runs YouTubeTranscriptManager directly in Colab. No Mac needed.*

> 💡 **Have an existing `output.zip` from your local machine?**
> You can skip fetching from YouTube entirely by uploading your zip file:
> 1. In Colab, click the **📁 Folder icon** on the left sidebar.
> 2. Drag and drop your `output.zip` file directly into the `/content` folder.
> 3. Add a new code cell above Cell 4 and run this foolproof extraction code:
>    ```python
>    import zipfile
>    import os
>    import shutil
> 
>    zip_path = '/content/output.zip'
>    dest_dir = '/content/repo/data_pipeline/output'
> 
>    if os.path.exists(zip_path):
>        print(f"Found {zip_path}, extracting...")
>        temp_dir = '/content/temp_extract'
>        os.makedirs(temp_dir, exist_ok=True)
>        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
>            zip_ref.extractall(temp_dir)
>        
>        # Recursively find all JSON files and copy them to dest_dir
>        json_count = 0
>        os.makedirs(dest_dir, exist_ok=True)
>        for root, _, files in os.walk(temp_dir):
>            for file in files:
>                if file.endswith('.json'):
>                    src = os.path.join(root, file)
>                    dst = os.path.join(dest_dir, file)
>                    shutil.copy2(src, dst)
>                    json_count += 1
>                    
>        shutil.rmtree(temp_dir)
>        print(f"✅ Successfully extracted and moved {json_count} transcript JSON files to {dest_dir}!")
>    else:
>        print(f"❌ Error: {zip_path} not found. Please drag and drop it into Colab's left sidebar.")
>    ```
> You can now skip Cell 3 completely!

```python
from data_pipeline.manager import YouTubeTranscriptManager
import json, os

# Add or remove video URLs here as needed
VIDEO_URLS = [
    "https://www.youtube.com/watch?v=9RAqjOZEOh4",
    "https://youtu.be/DdBv99-IWi0",
    "https://youtu.be/bb6ip0m6_CA",
    "https://youtu.be/BewB6S4JYqo",
    "https://youtu.be/Y4D15z9Z9nU",
    "https://youtu.be/Q263c-YZJmA",
]

import urllib.parse as urlparse

def extract_video_id(url):
    parsed = urlparse.urlparse(url)
    if parsed.hostname == "youtu.be":
        return parsed.path[1:].split("?")[0]
    if "youtube.com" in (parsed.hostname or ""):
        return urlparse.parse_qs(parsed.query).get("v", [url])[0]
    return url

video_ids = [extract_video_id(u) for u in VIDEO_URLS]

RAW_DIR = "/content/repo/data_pipeline/output"
manager = YouTubeTranscriptManager(output_dir=RAW_DIR)
transcripts = manager.process_videos(video_ids)

# Save raw transcripts
os.makedirs(RAW_DIR, exist_ok=True)
for video_id, data in transcripts.items():
    path = os.path.join(RAW_DIR, f"{video_id}.json")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {video_id}.json ({len(data)} fragments)")
    else:
        print(f"  Skipped (exists): {video_id}.json")

print(f"✅ {len(transcripts)} transcripts ready")
```

---

### 🟦 Cell 4 — Run VideoEnricher (LLM Metadata Extraction)
*Gemini analyses the full transcript once per video. Idempotent — safely re-run if Colab disconnects.*
```python
from data_pipeline.video_enricher import VideoEnricher

enricher = VideoEnricher(
    input_dir="/content/repo/data_pipeline/output",
    output_dir="/content/repo/data_pipeline/enriched_metadata",
)
results = enricher.process_all()
print(f"✅ Enriched {len(results)} videos")
```

---

### 🟦 Cell 5 — Load GPU Model (BGE-M3)
*Takes ~1 minute. Run once per Colab session.*
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

### 🟦 Cell 6 — Chunk & Embed (Zero-Drift Timestamps)
*TranscriptProcessor handles exact timestamp mapping. Saves enriched JSONs locally.*
```python
import json, os, glob
from data_pipeline.transcript_processor import TranscriptProcessor

ENRICHED_DIR = "/content/repo/data_pipeline/enriched_json"
os.makedirs(ENRICHED_DIR, exist_ok=True)

processor = TranscriptProcessor()

for filepath in glob.glob("/content/repo/data_pipeline/output/*.json"):
    video_id = os.path.splitext(os.path.basename(filepath))[0]
    out_path = os.path.join(ENRICHED_DIR, f"{video_id}_enriched.json")

    if os.path.exists(out_path):
        print(f"⏭️  Skipping {video_id} — already processed")
        continue

    print(f"🔄 Processing {video_id}...")
    chunks, char_map, full_text = processor.process_file(filepath, video_id)

    for chunk in chunks:
        # Embed natively in Marathi — no translation needed
        chunk["embedding_vector"] = embedder.encode(chunk["marathi_raw"]).tolist()

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"  ✅ {len(chunks)} chunks → {os.path.basename(out_path)}")

print("🎉 All videos processed!")
```

---

### 🟦 Cell 7 — Upload to Qdrant Cloud
*Cleans the collection and re-uploads everything fresh.*
```python
import sys
sys.path.insert(0, "/content/repo")

# Point the uploader to Colab's local enriched_json dir
import data_pipeline.qdrant_uploader as uploader_module

from data_pipeline.qdrant_uploader import QdrantManager

qdrant = QdrantManager()
qdrant.upload_data(input_directory="/content/repo/data_pipeline/enriched_json")
print("✅ Upload complete — Qdrant is live!")
```

---

### 🟦 Cell 8 — Upload Metadata to DynamoDB
*Uploads topics, stories, and queries to your deployed AWS backend.*
```python
import sys
sys.path.insert(0, "/content/repo")

from data_pipeline.dynamo_uploader import upload_metadata

# This will automatically check if your AWS stack is deployed.
# If not, it will throw an error telling you to deploy it first.
upload_metadata(input_dir="/content/repo/data_pipeline/enriched_metadata")
print("✅ DynamoDB upload complete!")
```

---

### 🟦 Cell 9 (Optional) — Backup to Google Drive
*Run this if you want to preserve your enriched files across Colab sessions.*
```python
from google.colab import drive
import shutil, glob

drive.mount("/content/drive")

BACKUP_DIR = "/content/drive/MyDrive/Guru_Project/Processed_JSON"
os.makedirs(BACKUP_DIR, exist_ok=True)

for f in glob.glob("/content/repo/data_pipeline/enriched_json/*_enriched.json"):
    shutil.copy(f, BACKUP_DIR)
    print(f"  Backed up: {os.path.basename(f)}")

for f in glob.glob("/content/repo/data_pipeline/enriched_metadata/*.json"):
    shutil.copy(f, BACKUP_DIR)
    print(f"  Backed up metadata: {os.path.basename(f)}")

print("✅ Backup complete")
```

---

## ⚡ Re-Running After a Disconnect

Colab sessions expire after ~12 hours. If it disconnects mid-run:

1. Re-run **Cell 1** (install deps)
2. Re-run **Cell 2** (clone + secrets)
3. Re-run **Cell 5** (reload GPU models)
4. Skip to **Cell 6 or 7** — all steps are idempotent, already-processed videos are skipped automatically.

> **Tip:** If you ran Cell 8 (Drive backup), restore your files at the start of a new session:
> ```python
> !cp /content/drive/MyDrive/Guru_Project/Processed_JSON/*.json /content/repo/data_pipeline/enriched_json/
> ```

---

## ✅ Final Checklist

- [ ] Colab runtime set to **T4 GPU**
- [ ] All 4 secrets added to Colab Secrets panel with "Notebook access" toggled on
- [ ] Cells 1–7 run top to bottom without errors
- [ ] Qdrant dashboard shows correct vector count after Cell 7
