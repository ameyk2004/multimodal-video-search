import os
import json
import math
import re
import sys
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models

try:
    from huggingface_hub import InferenceClient
except ImportError:
    print("Please install huggingface_hub: pip install huggingface_hub")
    sys.exit(1)

load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")
COLLECTION_NAME = "guru-videos-hybrid"

def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return [t.strip() for t in text.split() if t.strip()]

def get_bm25_vector(text: str, vocab: dict, idf_map: dict) -> models.SparseVector:
    tokens = tokenize(text)
    # For a query, the term frequency is simple. We just count tokens.
    tf = {}
    for token in tokens:
        if token in vocab:
            token_id = vocab[token]
            tf[token_id] = tf.get(token_id, 0) + 1
            
    indices = []
    values = []
    # In many systems query weight is just IDF * tf (or simply tf if IDF is applied to doc)
    # Qdrant's sparse vector dot product will do: sum(query_weight * doc_weight).
    # Since our doc_weight already contains IDF and TF components, 
    # we just need to pass tf (or 1.0) as the query weight.
    for token_id, count in tf.items():
        indices.append(token_id)
        values.append(float(count)) # Just pass query frequency, Qdrant does dot product!
        
    return models.SparseVector(indices=indices, values=values)

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_hybrid_search.py '<marathi_query>'")
        sys.exit(1)
        
    query_text = sys.argv[1]
    
    # 1. Load BM25 vocab
    vocab_path = "cloud-backend/lambdas/similarity_search/vocab_idf.json"
    if not os.path.exists(vocab_path):
        print(f"Vocab file not found at {vocab_path}")
        sys.exit(1)
        
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab_data = json.load(f)
        
    # Convert keys back to int because JSON makes them strings
    idf_map = {int(k): v for k, v in vocab_data["idf"].items()}
    vocab = vocab_data["vocab"]
    
    # 2. Get dense vector
    print("Generating dense embedding via HuggingFace...")
    hf_client = InferenceClient(token=HF_API_KEY, timeout=25)
    embedding = hf_client.feature_extraction(text=query_text, model="BAAI/bge-m3")
    dense_vec = embedding.tolist()
    if isinstance(dense_vec, list) and len(dense_vec) > 0 and isinstance(dense_vec[0], list):
        dense_vec = dense_vec[0]
        
    # 3. Get sparse vector
    sparse_vec = get_bm25_vector(query_text, vocab, idf_map)
    print(f"Sparse vector active tokens: {len(sparse_vec.indices)}")
    
    # 4. Search
    print(f"Querying Qdrant '{COLLECTION_NAME}' with Hybrid Search (RRF)...")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            models.Prefetch(query=dense_vec, using="", limit=10),
            models.Prefetch(query=sparse_vec, using="bm25", limit=10),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        with_payload=True,
        limit=5
    )
    
    print("\n=== TOP 5 HYBRID SEARCH RESULTS ===")
    for i, point in enumerate(results.points):
        text = point.payload.get("marathi_raw", "").replace("\n", " ")
        print(f"\n{i+1}. Score: {point.score:.4f} | Video: {point.payload.get('video_id')}")
        print(f"Text: {text[:150]}...")

if __name__ == "__main__":
    main()
