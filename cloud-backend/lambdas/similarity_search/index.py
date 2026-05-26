"""
AWS Lambda Entry Point for the Multimodal Guru Video Search Engine.
"""
import json
import os
import logging
import decimal
import re
from typing import Any

import google.generativeai as genai

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            if obj % 1 > 0:
                return float(obj)
            else:
                return int(obj)
        return super(DecimalEncoder, self).default(obj)


from embedding import HuggingFaceEmbedder
from search import QdrantSearcher

# ─── Configuration ────────────────────────────────────────────────────────────
logger = logging.getLogger()
logger.setLevel(logging.INFO)

QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
HF_API_KEY = os.environ["HF_API_KEY"]
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "sadhananandadeep-videos")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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
        "body": json.dumps(body, ensure_ascii=False, cls=DecimalEncoder),
    }

def translate_to_marathi(query: str) -> tuple[str, str]:
    """
    Translates or transliterates a query to Devanagari Marathi using Gemini.
    Returns (translated_query, error_string_if_any).
    Skips API call if the text is already pure Devanagari (no English letters).
    """
    if not GEMINI_API_KEY:
        return query, "Missing API Key"
        
    # If there are no English letters, assume it's already in native script
    if not re.search(r'[a-zA-Z]', query):
        logger.info("Skipping translation (pure Marathi detected).")
        return query, ""
        
    try:
        logger.info("Translating query via Gemini: %s", query)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = (
            f"You are an expert translator for a spiritual Marathi application about Sant Tukaram and Shri Pethekaka. "
            f"If the following input is fully in Devanagari script, return it exactly as is. "
            f"If it is in English or Romanized Marathi (Hinglish), translate/transliterate it into natural Devanagari Marathi. "
            f"Output ONLY the resulting Devanagari text. Do not add quotes, explanations, or conversational text.\n\n"
            f"Query: {query}"
        )
        
        # We do NOT restrict max_output_tokens, per user request, to handle long queries gracefully.
        response = model.generate_content(prompt)
        translated = response.text.strip()
        
        if translated:
            logger.info("Translated query: %s -> %s", query, translated)
            return translated, ""
    except Exception as e:
        logger.error("Gemini translation failed: %s. Falling back to original query.", e)
        return query, str(e)
        
    return query, "Unknown fallback"

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
    
    # ── Step 0: Translate Query ──────────────────────────────────────────────
    processed_query, translation_error = translate_to_marathi(query)

    try:
        # ── Step 1: Generate embedding ───────────────────────────────────
        embedder = _get_embedder()
        vector = embedder.generate_embedding(processed_query)
        logger.info("Embedding generated (%d dimensions)", len(vector))

        # ── Step 2: Semantic search ──────────────────────────────────────
        searcher = _get_searcher()
        results = searcher.search(vector, query_text=processed_query, top_k=5)
        logger.info("Found %d results", len(results))

        # ── Step 3: Fetch Related Queries using Qdrant (3:1:1 Exploration Mix) ──
        related_queries_structured = []
        try:
            # Fetch top 20 nearest neighbors
            queries_response = searcher.client.query_points(
                collection_name="sadhananandadeep-queries",
                query=vector,
                limit=20,
                with_payload=True
            ).points
            
            # Extract unique queries to avoid duplicates
            seen_queries = set()
            unique_queries = []
            for hit in queries_response:
                q = hit.payload.get("query")
                if q and q not in seen_queries:
                    seen_queries.add(q)
                    unique_queries.append(q)
            
            # 1. Direct (Top 3)
            direct_pool = unique_queries[:3]
            for q in direct_pool:
                related_queries_structured.append({"query": q, "type": "direct"})
                
            # 2. Tangential (1 random from the rest)
            tangential_pool = unique_queries[3:]
            if tangential_pool:
                import random
                tangential_q = random.choice(tangential_pool)
                related_queries_structured.append({"query": tangential_q, "type": "tangential"})
                seen_queries.add(tangential_q)
                
            # 3. Wildcard (1 completely random)
            # Generate random vector to jump out of the local cluster
            import random
            random_vector = [random.uniform(-1.0, 1.0) for _ in range(1024)]
            wildcard_response = searcher.client.query_points(
                collection_name="sadhananandadeep-queries",
                query=random_vector,
                limit=5, # Fetch a few in case top is a duplicate
                with_payload=True
            ).points
            
            for hit in wildcard_response:
                q = hit.payload.get("query")
                if q and q not in seen_queries:
                    related_queries_structured.append({"query": q, "type": "wildcard"})
                    break
                    
        except Exception as e:
            logger.error("Failed to fetch related queries from Qdrant: %s", e)

        # Build response via Pydantic model
        from models.response import SearchResponse, SearchResultItem
        
        search_results = [
            SearchResultItem(
                video_id=r["video_id"],
                marathi_raw=r.get("marathi_raw", ""),
                start_time=r.get("start_time", 0.0),
                score=r.get("score", 0.0)
            ) for r in results if "video_id" in r
        ]

        # Use structured related queries
        response_model = SearchResponse(
            query=query,
            translated_query=processed_query,
            translation_error=translation_error,
            results=search_results,
            related_queries=related_queries_structured
        )

        return _build_response(200, response_model.model_dump())

    except ConnectionError as exc:
        logger.error("HuggingFace API connection error: %s", exc)
        return _build_response(502, {"error": "Embedding service returned an error."})

    except TimeoutError:
        logger.error("HuggingFace API timed out for query: %s", query)
        return _build_response(504, {"error": "Embedding service timed out."})

    except Exception as exc:
        logger.exception("Unexpected error during search")
        return _build_response(500, {"error": f"Internal server error: {str(exc)}"})
