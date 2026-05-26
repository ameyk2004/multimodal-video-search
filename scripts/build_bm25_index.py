import os
import json
import math
import re
from collections import defaultdict
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models

# ─── Configuration ────────────────────────────────────────────────────────────
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "sadhananandadeep-videos")

# BM25 Parameters
K1 = 1.2
B = 0.75

def tokenize(text: str) -> list[str]:
    """
    Very basic tokenizer for Marathi:
    Lowercase, remove punctuation, split by spaces.
    """
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = [t.strip() for t in text.split() if t.strip()]
    return tokens

def main():
    print(f"Connecting to Qdrant at {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    # 1. Ensure the collection has a sparse vector named 'bm25'
    print(f"Updating collection '{COLLECTION_NAME}' to support sparse vectors...")
    try:
        client.update_collection(
            collection_name=COLLECTION_NAME,
            sparse_vectors_config={
                "bm25": models.SparseVectorParams()
            }
        )
        print("Sparse vector config added/verified.")
    except Exception as e:
        print(f"Note: Could not update collection config (might already be configured): {e}")

    # 2. Fetch all points from Qdrant
    print("Fetching all existing points from Qdrant...")
    points = []
    offset = None
    while True:
        response, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=1000,
            with_payload=True,
            with_vectors=False, # We don't need the dense vectors
            offset=offset
        )
        points.extend(response)
        if offset is None:
            break
    
    N = len(points)
    print(f"Fetched {N} chunks.")

    if N == 0:
        print("No points found. Exiting.")
        return

    # 3. Build Vocabulary and compute Document Frequencies (DF)
    print("Building vocabulary and computing corpus statistics...")
    doc_lengths = []
    df = defaultdict(int)
    
    # Store tokenized docs so we don't re-tokenize
    tokenized_docs = []
    
    for point in points:
        text = point.payload.get("marathi_raw", "")
        tokens = tokenize(text)
        tokenized_docs.append(tokens)
        doc_lengths.append(len(tokens))
        
        # Unique tokens in this document
        unique_tokens = set(tokens)
        for token in unique_tokens:
            df[token] += 1
            
    avgdl = sum(doc_lengths) / N if N > 0 else 0
    print(f"Vocabulary size: {len(df)}")
    print(f"Average document length: {avgdl:.2f} tokens")

    # 4. Compute IDF for each token and build mapping (token -> id)
    vocab = {} # token -> token_id
    idf_map = {} # token_id -> idf_value
    
    for token_id, (token, doc_freq) in enumerate(df.items()):
        vocab[token] = token_id
        # Standard BM25 IDF formula
        idf = math.log(1 + (N - doc_freq + 0.5) / (doc_freq + 0.5))
        idf_map[token_id] = max(idf, 0) # Ensure no negative IDF
        
    # Save vocabulary and IDF mapping for the Lambda to use at query time
    vocab_idf_path = "cloud-backend/lambdas/similarity_search/vocab_idf.json"
    os.makedirs(os.path.dirname(vocab_idf_path), exist_ok=True)
    with open(vocab_idf_path, "w", encoding="utf-8") as f:
        json.dump({"vocab": vocab, "idf": idf_map, "avgdl": avgdl}, f, ensure_ascii=False)
    print(f"Saved vocabulary and IDF to {vocab_idf_path}")

    # 5. Compute sparse vectors for all points and upload them
    print("Computing BM25 sparse vectors and updating Qdrant...")
    batch_size = 100
    for i in range(0, N, batch_size):
        batch_points = points[i:i+batch_size]
        batch_tokens = tokenized_docs[i:i+batch_size]
        
        update_operations = []
        for point, tokens in zip(batch_points, batch_tokens):
            if not tokens:
                continue
                
            # Term Frequencies for this doc
            tf = defaultdict(int)
            for token in tokens:
                tf[vocab[token]] += 1
                
            dl = len(tokens)
            
            # Compute BM25 weights
            indices = []
            values = []
            for token_id, count in tf.items():
                idf = idf_map[token_id]
                numerator = count * (K1 + 1)
                denominator = count + K1 * (1 - B + B * dl / avgdl)
                score = idf * (numerator / denominator)
                
                indices.append(token_id)
                values.append(score)
                
            # Create update operation for just the sparse vector
            sparse_vector = models.SparseVector(indices=indices, values=values)
            update_operations.append(
                models.PointVectors(
                    id=point.id,
                    vector={
                        "bm25": sparse_vector
                    }
                )
            )
            
        if update_operations:
            client.update_vectors(
                collection_name=COLLECTION_NAME,
                points=update_operations
            )
            print(f"Updated {i + len(update_operations)} / {N} points...")

    print("Successfully built BM25 index and updated Qdrant!")

if __name__ == "__main__":
    main()
