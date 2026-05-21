"""
AWS Lambda Entry Point for the Multimodal Guru Video Search Engine.
"""
import json
import os
import logging
from typing import Any


from embedding import HuggingFaceEmbedder
from search import QdrantSearcher

# ─── Configuration ────────────────────────────────────────────────────────────
logger = logging.getLogger()
logger.setLevel(logging.INFO)

QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
HF_API_KEY = os.environ["HF_API_KEY"]
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "guru-videos")

# CORS headers applied to every response
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
}

# ─── Global Instances (reused across warm invocations) ───────────────────────
_embedder: HuggingFaceEmbedder | None = None
_searcher: QdrantSearcher | None = None

def _get_embedder() -> HuggingFaceEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = HuggingFaceEmbedder(api_key=HF_API_KEY)
    return _embedder

def _get_searcher() -> QdrantSearcher:
    global _searcher
    if _searcher is None:
        _searcher = QdrantSearcher(url=QDRANT_URL, api_key=QDRANT_API_KEY, collection_name=COLLECTION_NAME)
    return _searcher

# ─── Helper utilities ────────────────────────────────────────────────────────

def _build_response(status_code: int, body: dict[str, Any]) -> dict:
    """Build a properly formatted API Gateway proxy response with CORS."""
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, ensure_ascii=False),
    }

# ─── Lambda entry point ─────────────────────────────────────────────────────

def lambda_handler(event: dict, context: Any) -> dict:
    """
    GET /search?q=<query>
    """
    logger.info("Received event: %s", json.dumps(event, default=str))

    # ── Extract query ────────────────────────────────────────────────────
    params = event.get("queryStringParameters") or {}
    query = params.get("q", "").strip()

    if not query:
        return _build_response(400, {"error": "Missing required query parameter 'q'."})

    logger.info("Processing query: %s", query)

    try:
        # ── Step 1: Generate embedding ───────────────────────────────────
        embedder = _get_embedder()
        vector = embedder.generate_embedding(query)
        logger.info("Embedding generated (%d dimensions)", len(vector))

        # ── Step 2: Semantic search ──────────────────────────────────────
        searcher = _get_searcher()
        results = searcher.search(vector, top_k=5)
        logger.info("Found %d results", len(results))

        return _build_response(200, {"query": query, "results": results})

    except ConnectionError as exc:
        logger.error("HuggingFace API connection error: %s", exc)
        return _build_response(502, {"error": "Embedding service returned an error."})

    except TimeoutError:
        logger.error("HuggingFace API timed out for query: %s", query)
        return _build_response(504, {"error": "Embedding service timed out."})

    except Exception as exc:
        logger.exception("Unexpected error during search")
        return _build_response(500, {"error": f"Internal server error: {str(exc)}"})
