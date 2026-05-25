import json
import re
import os
import logging
from typing import Any
from qdrant_client import QdrantClient
from qdrant_client.http import models

logger = logging.getLogger(__name__)

class QdrantSearcher:
    """
    Handles semantic search queries against a Qdrant collection.
    """
    def __init__(self, url: str, api_key: str, collection_name: str = "guru-videos"):
        self.collection_name = collection_name
        self.client = QdrantClient(url=url, api_key=api_key, timeout=20.0)
        logger.info("QdrantSearcher initialised for collection '%s'", self.collection_name)
        self._load_vocab()

    def _load_vocab(self):
        vocab_path = os.path.join(os.path.dirname(__file__), "vocab_idf.json")
        try:
            with open(vocab_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.vocab = data.get("vocab", {})
                self.idf_map = {int(k): v for k, v in data.get("idf", {}).items()}
            logger.info("Loaded BM25 vocab with %d terms", len(self.vocab))
        except Exception as e:
            logger.warning("Could not load BM25 vocab: %s", e)
            self.vocab = {}
            self.idf_map = {}
            
        stopwords_path = os.path.join(os.path.dirname(__file__), "marathi_stopwords.json")
        try:
            with open(stopwords_path, "r", encoding="utf-8") as f:
                self.stop_words = set(json.load(f))
            logger.info("Loaded %d Marathi stop words", len(self.stop_words))
        except Exception as e:
            logger.warning("Could not load Marathi stopwords: %s", e)
            self.stop_words = set()

    def _get_sparse_vector(self, text: str) -> models.SparseVector | None:
        if not self.vocab:
            return None
            
        # Robust Marathi Stop Words to prevent BM25 from over-indexing on conversational words
        stop_words = self.stop_words
        
        # Basic tokenizer
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        raw_tokens = [t.strip() for t in text.split() if t.strip()]
        
        # Filter stop words
        tokens = [t for t in raw_tokens if t not in stop_words]
        
        # If the user typed a long conversational question and all important keywords 
        # were stripped, or if the original query is conversational (>3 words),
        # BM25 Keyword matching becomes risky (it grabs onto random remaining verbs).
        # In these cases, it's safer to fallback to purely Semantic Dense Search.
        if len(raw_tokens) > 3:
            logger.info("Conversational query detected (%d words). Dropping BM25 to rely purely on Dense Meaning.", len(raw_tokens))
            return None
        
        tf = {}
        for token in tokens:
            if token in self.vocab:
                token_id = self.vocab[token]
                tf[token_id] = tf.get(token_id, 0) + 1
                
        if not tf:
            return None
            
        indices = []
        values = []
        for token_id, count in tf.items():
            indices.append(token_id)
            values.append(float(count)) # Query weight is just frequency
            
        return models.SparseVector(indices=indices, values=values)

    def search(self, vector: list[float], query_text: str = "", top_k: int = 5, min_score: float = 0.35) -> list[dict[str, Any]]:
        """
        Searches the Qdrant collection using Hybrid Search (Dense + BM25) and applies a minimum score threshold.
        """
        sparse_vec = self._get_sparse_vector(query_text) if query_text else None

        if sparse_vec:
            # Hybrid Search using RRF
            hits = self.client.query_points(
                collection_name=self.collection_name,
                prefetch=[
                    models.Prefetch(query=vector, using="", limit=top_k * 2),
                    models.Prefetch(query=sparse_vec, using="bm25", limit=top_k * 2),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=top_k,
                with_payload=True,
            ).points
        else:
            # Fallback to pure dense search
            hits = self.client.query_points(
                collection_name=self.collection_name,
                query=vector,
                limit=top_k,
                with_payload=True,
            ).points

        results = []
        for hit in hits:
            # Layer 2 Robustness: Hard cutoff to drop completely unrelated chunks
            if hit.score < min_score:
                logger.info("Dropping hit due to low score: %.4f < %.4f", hit.score, min_score)
                continue
                
            results.append(
                {
                    "score": round(hit.score, 4),
                    "video_id": hit.payload.get("video_id", ""),
                    "start_time": hit.payload.get("start_time", 0),
                    "duration": hit.payload.get("duration", 0),
                    "marathi_raw": hit.payload.get("marathi_raw", ""),
                }
            )

        return results
