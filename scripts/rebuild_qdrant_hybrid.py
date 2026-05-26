import os
import json
import math
import glob
import uuid
import re
from collections import defaultdict
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models

load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "sadhananandadeep-videos")
PROCESSED_JSON_DIR = os.getenv("ENRICHED_JSON_DIR", "data_pipeline/enriched_json")

# BM25 Parameters
K1 = 1.2
B = 0.75

def tokenize(text: str) -> list[str]:
    """Basic tokenizer for Marathi"""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = [t.strip() for t in text.split() if t.strip()]
    return tokens

def main():
    if not QDRANT_URL or not QDRANT_API_KEY:
        raise ValueError("Missing Qdrant credentials in .env file.")

    json_files = glob.glob(f"{PROCESSED_JSON_DIR}/*_enriched.json")
    if not json_files:
        print(f"No '_enriched.json' files found in {PROCESSED_JSON_DIR}. Run the pipeline first.")
        return

    print("=== PASS 1: Building BM25 Vocabulary and IDF ===")
    N = 0
    df = defaultdict(int)
    doc_lengths = []
    
    for filepath in json_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for row in data:
                text = row.get('marathi_raw', '')
                if not text: continue
                
                tokens = tokenize(text)
                N += 1
                doc_lengths.append(len(tokens))
                
                unique_tokens = set(tokens)
                for token in unique_tokens:
                    df[token] += 1
                    
    avgdl = sum(doc_lengths) / N if N > 0 else 0
    print(f"Total Chunks: {N}, Vocab Size: {len(df)}, Avg Doc Length: {avgdl:.2f}")

    vocab = {}
    idf_map = {}
    for token_id, (token, doc_freq) in enumerate(df.items()):
        vocab[token] = token_id
        idf = math.log(1 + (N - doc_freq + 0.5) / (doc_freq + 0.5))
        idf_map[token_id] = max(idf, 0)

    # Save to lambda directory
    vocab_idf_path = "cloud-backend/lambdas/similarity_search/vocab_idf.json"
    os.makedirs(os.path.dirname(vocab_idf_path), exist_ok=True)
    with open(vocab_idf_path, "w", encoding="utf-8") as f:
        json.dump({"vocab": vocab, "idf": idf_map, "avgdl": avgdl}, f, ensure_ascii=False)
    print(f"Saved vocabulary and IDF to {vocab_idf_path}")

    print("\n=== PASS 2: Recreating Qdrant Collection ===")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    if client.collection_exists(collection_name=COLLECTION_NAME):
        print(f"Deleting old collection {COLLECTION_NAME}...")
        client.delete_collection(collection_name=COLLECTION_NAME)
        
    print(f"Creating fresh collection {COLLECTION_NAME} with Hybrid config...")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
        sparse_vectors_config={
            "bm25": models.SparseVectorParams()
        }
    )

    print("\n=== PASS 3: Uploading Dense + Sparse Vectors ===")
    batch_size = 100
    for filepath in json_files:
        filename = os.path.basename(filepath)
        video_id = filename.replace('_enriched.json', '')
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        points = []
        for row in data:
            embedding = row.get('embedding_vector')
            text = row.get('marathi_raw', '')
            if not embedding or not text:
                continue

            tokens = tokenize(text)
            tf = defaultdict(int)
            for token in tokens:
                tf[vocab[token]] += 1
                
            dl = len(tokens)
            indices = []
            values = []
            
            for token_id, count in tf.items():
                idf = idf_map[token_id]
                numerator = count * (K1 + 1)
                denominator = count + K1 * (1 - B + B * dl / avgdl)
                score = idf * (numerator / denominator)
                indices.append(token_id)
                values.append(score)

            start_time = row.get('start_time', 0)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{video_id}_{start_time}"))

            payload = {
                "video_id": video_id,
                "type": row.get('type', 'video'),
                "marathi_raw": text,
                "start_time": start_time,
                "duration": row.get('duration', 0)
            }

            sparse_vector = models.SparseVector(indices=indices, values=values)
            
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector={
                        "": embedding,
                        "bm25": sparse_vector
                    },
                    payload=payload
                )
            )

        for i in range(0, len(points), batch_size):
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points[i:i + batch_size]
            )
        print(f"Uploaded {len(points)} Hybrid vectors from {filename}")

    print("\nAll data successfully locked into Qdrant with Hybrid Search enabled!")

if __name__ == "__main__":
    main()
