import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models

load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "sadhananandadeep-books")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
client.create_payload_index(
    collection_name=COLLECTION_NAME,
    field_name="page_number",
    field_schema=models.PayloadSchemaType.INTEGER
)
print("Index created successfully!")
