"""
Qdrant Uploader Script.
Uploads the Colab-enriched JSON files containing English translations and vectors to the Qdrant Vector Database.

To run this script:
    source venv/bin/activate
    python data_pipeline/qdrant_uploader.py
"""
import os
import json
import glob
import uuid
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

class QdrantManager:
    def __init__(self, collection_name="guru-videos", recreate_collection: bool = True):
        load_dotenv()
        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")
        
        if not url or not api_key:
            raise ValueError("Missing Qdrant credentials in .env file.")

        print("Connecting to Qdrant Cloud...")
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection_name = collection_name

        if recreate_collection:
            # Clean the Database: Delete if exists, then recreate
            if self.client.collection_exists(collection_name=self.collection_name):
                print(f"Collection {self.collection_name} already exists. Deleting it to clean the DB...")
                self.client.delete_collection(collection_name=self.collection_name)
                
            print(f"Creating fresh collection: {self.collection_name}...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            )
            print("Collection configured successfully!")
        else:
            if not self.client.collection_exists(collection_name=self.collection_name):
                print(f"Collection {self.collection_name} does not exist. Creating fresh collection...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
                )
                print("Collection configured successfully!")
            else:
                print(f"Collection {self.collection_name} already exists. Appending to existing data (no deletion).")

    def upload_data(self, input_directory: str, batch_size: int = 100):
        json_files = glob.glob(f"{input_directory}/*_enriched.json")
        if not json_files:
            print(f"No '_enriched.json' files found in {input_directory}.")
            return

        print(f"Found {len(json_files)} files. Starting upload...")

        for filepath in json_files:
            filename = os.path.basename(filepath)
            video_id = filename.replace('_enriched.json', '')
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            points = []
            
            for row in data:
                embedding = row.get('embedding_vector')
                if not embedding:
                    continue

                # Generate a deterministic UUID based on video ID and start time
                start_time = row.get('start_time', 0)
                point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{video_id}_{start_time}"))

                # Package the payload (metadata)
                payload = {
                    "video_id": video_id,
                    "type": row.get('type', 'video'),
                    "marathi_raw": row.get('marathi_raw', ''),
                    "start_time": start_time,
                    "duration": row.get('duration', 0)
                }

                points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

            # Batch upload
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
            
            print(f"Uploaded {len(points)} vectors from {filename}")

        print("All data successfully locked into Qdrant!")

if __name__ == "__main__":
    # Ensure this points to the folder containing your downloaded Colab files
    PROCESSED_JSON_DIR = "data_pipeline/enriched_json" 
    
    uploader = QdrantManager()
    uploader.upload_data(input_directory=PROCESSED_JSON_DIR)
