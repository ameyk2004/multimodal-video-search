import os
import json
import math
import re
from collections import defaultdict
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models

load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OLD_COLLECTION = os.getenv("COLLECTION_NAME", "guru-videos")
NEW_COLLECTION = "guru-videos-hybrid"

K1 = 1.2
B = 0.75

def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = [t.strip() for t in text.split() if t.strip()]
    return tokens

def main():
    print(f"Connecting to Qdrant at {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60)
    
    print(f"1. Fetching ALL points (including dense vectors) from {OLD_COLLECTION}...")
    points = []
    offset = None
    while True:
        response, offset = client.scroll(
            collection_name=OLD_COLLECTION,
            limit=500,
            with_payload=True,
            with_vectors=True, # Critical: we need the existing dense vectors!
            offset=offset
        )
        points.extend(response)
        if offset is None:
            break
            
    N = len(points)
    print(f"Fetched {N} chunks with dense vectors.")
    if N == 0:
        return

    print("2. Building BM25 Vocabulary and IDF...")
    df = defaultdict(int)
    doc_lengths = []
    tokenized_docs = []
    
    for point in points:
        text = point.payload.get("marathi_raw", "")
        tokens = tokenize(text)
        tokenized_docs.append(tokens)
        doc_lengths.append(len(tokens))
        for token in set(tokens):
            df[token] += 1
            
    avgdl = sum(doc_lengths) / N if N > 0 else 0
    
    vocab = {}
    idf_map = {}
    for token_id, (token, doc_freq) in enumerate(df.items()):
        vocab[token] = token_id
        idf = math.log(1 + (N - doc_freq + 0.5) / (doc_freq + 0.5))
        idf_map[token_id] = max(idf, 0)
        
    vocab_idf_path = "cloud-backend/lambdas/similarity_search/vocab_idf.json"
    os.makedirs(os.path.dirname(vocab_idf_path), exist_ok=True)
    with open(vocab_idf_path, "w", encoding="utf-8") as f:
        json.dump({"vocab": vocab, "idf": idf_map, "avgdl": avgdl}, f, ensure_ascii=False)
    print(f"Saved vocabulary to {vocab_idf_path}")

    print(f"3. Creating new Hybrid collection: {NEW_COLLECTION}...")
    if client.collection_exists(collection_name=NEW_COLLECTION):
        client.delete_collection(collection_name=NEW_COLLECTION)
        
    client.create_collection(
        collection_name=NEW_COLLECTION,
        vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
        sparse_vectors_config={"bm25": models.SparseVectorParams()}
    )

    print("4. Computing BM25 and uploading everything to the new collection...")
    batch_size = 100
    for i in range(0, N, batch_size):
        batch_points = points[i:i+batch_size]
        batch_tokens = tokenized_docs[i:i+batch_size]
        
        new_points = []
        for point, tokens in zip(batch_points, batch_tokens):
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
                
            sparse_vector = models.SparseVector(indices=indices, values=values)
            
            # The existing vector might be returned as a list or a VectorStruct depending on Qdrant version.
            # Usually it's a list if unnamed.
            dense_vec = point.vector
            if isinstance(dense_vec, dict) and "" in dense_vec:
                dense_vec = dense_vec[""]
                
            new_points.append(
                models.PointStruct(
                    id=point.id,
                    vector={
                        "": dense_vec,
                        "bm25": sparse_vector
                    },
                    payload=point.payload
                )
            )
            
        client.upsert(collection_name=NEW_COLLECTION, points=new_points)
        print(f"Migrated {min(i+batch_size, N)} / {N} points...")

    print("✅ Migration Complete! Update your .env / Lambda to use COLLECTION_NAME=guru-videos-hybrid")

if __name__ == "__main__":
    main()
