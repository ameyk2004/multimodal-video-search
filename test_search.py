import os
from dotenv import load_dotenv
load_dotenv()
from cloud_backend.lambdas.similarity_search.search import QdrantSearcher
from cloud_backend.lambdas.similarity_search.embedding import HuggingFaceEmbedder

url = os.environ.get("QDRANT_URL")
api_key = os.environ.get("QDRANT_API_KEY")
hf_key = os.environ.get("HF_API_KEY")

searcher = QdrantSearcher(url, api_key)
embedder = HuggingFaceEmbedder(hf_key)

q = "ध्यान मार्ग"
vec = embedder.generate_embedding(q)

hits = searcher.search(vec, query_text=q, top_k=5, min_score=0.0)
for h in hits:
    print(h)
