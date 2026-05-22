import logging
from typing import Any
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)

class QdrantSearcher:
    """
    Handles semantic search queries against a Qdrant collection.
    """
    def __init__(self, url: str, api_key: str, collection_name: str = "guru-videos"):
        self.collection_name = collection_name
        self.client = QdrantClient(url=url, api_key=api_key)
        logger.info("QdrantSearcher initialised for collection '%s'", self.collection_name)

    def search(self, vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        """
        Searches the Qdrant collection using the given vector and returns formatted results.
        """
        hits = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=top_k,
            with_payload=True,
        ).points

        results = []
        for hit in hits:
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
