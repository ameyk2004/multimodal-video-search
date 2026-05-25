import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models

load_dotenv()
client = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
)

collection_name = os.environ.get("COLLECTION_NAME", "guru-videos")
print(f"Collection: {collection_name}")

# Check current configuration
info = client.get_collection(collection_name)
print("Config:", info.config.params)
