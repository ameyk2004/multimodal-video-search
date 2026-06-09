import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models

load_dotenv()
client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))

res = client.scroll(
    collection_name="sadhananandadeep-books",
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(key="book_name", match=models.MatchValue(value="Jeevanjidnyasa")),
        ]
    ),
    limit=5,
    with_payload=True,
    with_vectors=False
)
print([p.payload.get("chunk_index") for p in res[0]])
