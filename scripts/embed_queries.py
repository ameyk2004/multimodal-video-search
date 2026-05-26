import os
import json
import glob
import time
import uuid
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

COLLECTION_NAME = "sadhananandadeep-queries"
MODEL_ID = "BAAI/bge-m3"
VECTOR_DIMENSION = 1024

def get_embeddings(texts: List[str]) -> List[List[float]]:
    client = InferenceClient(token=HF_API_KEY, timeout=60)
    
    embeddings = []
    # Process texts one by one to avoid large payload errors, 
    # InferenceClient is fast enough
    for text in texts:
        for attempt in range(5):
            try:
                emb = client.feature_extraction(text=text, model=MODEL_ID)
                result = emb.tolist() if hasattr(emb, 'tolist') else list(emb)
                if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
                    result = result[0]
                embeddings.append(result)
                break
            except Exception as e:
                print(f"HuggingFace API error: {e}")
                if attempt < 4:
                    time.sleep(2)
                else:
                    raise
    return embeddings

def main():
    if not all([QDRANT_URL, QDRANT_API_KEY, HF_API_KEY]):
        print("Missing required API keys in .env")
        return

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60.0)
    
    # Create collection only if it does not exist (enables safe appending)
    print(f"Checking collection '{COLLECTION_NAME}'...")
    if not client.collection_exists(collection_name=COLLECTION_NAME):
        print(f"Creating collection '{COLLECTION_NAME}'...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists. New queries will be appended.")

    # Read all enriched metadata
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    metadata_dir = os.path.join(base_dir, "data_pipeline", "enriched_metadata")
    files = glob.glob(os.path.join(metadata_dir, "*.json"))
    
    all_queries = [] # List of tuples: (query_text, video_id)
    
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            vid = data.get("video_id", os.path.basename(fpath).split("_")[0])
            queries = data.get("queries", [])
            for q in queries:
                if q and isinstance(q, str):
                    all_queries.append((q, vid))
                    
    # Deduplicate queries, keeping the first video_id mapping
    unique_queries: Dict[str, str] = {}
    for q, vid in all_queries:
        if q not in unique_queries:
            unique_queries[q] = vid
            
    print(f"Found {len(unique_queries)} unique queries across {len(files)} videos.")
    
    if not unique_queries:
        print("No queries found. Exiting.")
        return

    # Generate deterministic UUIDs for all queries
    query_to_id = {q: str(uuid.uuid5(uuid.NAMESPACE_URL, q)) for q in unique_queries}
    all_ids = list(query_to_id.values())
    
    # Check Qdrant for existing IDs in batches of 100
    print("Checking Qdrant for existing query embeddings...")
    existing_ids = set()
    for j in range(0, len(all_ids), 100):
        batch_ids = all_ids[j:j+100]
        try:
            retrieved = client.retrieve(
                collection_name=COLLECTION_NAME,
                ids=batch_ids,
                with_payload=False,
                with_vectors=False
            )
            for point in retrieved:
                existing_ids.add(str(point.id))
        except Exception as e:
            print(f"Warning during Qdrant check: {e}")
            
    # Filter out queries that are already embedded and uploaded
    queries_to_process = []
    for q, vid in unique_queries.items():
        q_id = query_to_id[q]
        if q_id not in existing_ids:
            queries_to_process.append((q, vid))
            
    print(f"Skipping {len(unique_queries) - len(queries_to_process)} queries already present in Qdrant.")
    print(f"Need to embed and upload {len(queries_to_process)} new queries.")
    
    if not queries_to_process:
        print("✅ All queries are already up-to-date in Qdrant! Done.")
        return

    # Process only the new queries in batches of 50
    batch_size = 50
    
    for i in range(0, len(queries_to_process), batch_size):
        batch = queries_to_process[i:i+batch_size]
        texts = [item[0] for item in batch]
        
        print(f"Generating embeddings for batch {i//batch_size + 1}...")
        embeddings = get_embeddings(texts)
        
        points = []
        for (query_text, vid), emb in zip(batch, embeddings):
            # Generate deterministic UUID based on the query text to prevent duplicates in Qdrant
            point_id = query_to_id[query_text]
            
            points.append(
                PointStruct(
                    id=point_id,
                    vector=emb,
                    payload={"query": query_text, "video_id": vid}
                )
            )
            
        print(f"Uploading batch {i//batch_size + 1} to Qdrant...")
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
    
    print("✅ New queries successfully embedded and stored in Qdrant!")

if __name__ == "__main__":
    main()
