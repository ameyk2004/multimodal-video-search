import os
import json
import glob
import time
import uuid
import sys
import boto3
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "sadhananandadeep-content")

COLLECTION_NAME = "sadhananandadeep-queries"
MODEL_ID = "BAAI/bge-m3"
VECTOR_DIMENSION = 1024

def get_embeddings(texts: List[str]) -> List[List[float]]:
    client = InferenceClient(token=HF_API_KEY, timeout=60)
    
    # Try batch extraction first (highly efficient, 1 request instead of 50)
    for attempt in range(3):
        try:
            emb = client.feature_extraction(text=texts, model=MODEL_ID)
            result = emb.tolist() if hasattr(emb, 'tolist') else list(emb)
            if len(result) == len(texts):
                return result
            else:
                print(f"Warning: expected {len(texts)} embeddings, got {len(result)}. Retrying individually...")
                break
        except Exception as e:
            print(f"HuggingFace batch embedding error (attempt {attempt + 1}/3): {e}")
            if attempt < 2:
                time.sleep(3)
            else:
                print("Batch embedding failed. Falling back to individual embedding...")
                
    # Fallback: process one by one
    embeddings = []
    for text in texts:
        success = False
        for attempt in range(5):
            try:
                emb = client.feature_extraction(text=text, model=MODEL_ID)
                result = emb.tolist() if hasattr(emb, 'tolist') else list(emb)
                if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
                    result = result[0]
                embeddings.append(result)
                success = True
                break
            except Exception as e:
                print(f"HuggingFace API individual error for '{text}' (attempt {attempt + 1}/5): {e}")
                if attempt < 4:
                    time.sleep(2)
        if not success:
            raise Exception(f"Failed to generate embedding for text: {text}")
            
    return embeddings

def get_queries_from_dynamodb(table_name: str) -> List[tuple[str, str]]:
    region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))
    print(f"Connecting to DynamoDB in region '{region}'...")
    try:
        dynamodb = boto3.resource('dynamodb', region_name=region)
        table = dynamodb.Table(table_name)
        
        print(f"Scanning DynamoDB table '{table_name}' for query metadata...")
        all_queries = []
        
        response = table.scan(
            ProjectionExpression="video_id, queries"
        )
        items = response.get('Items', [])
        
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ProjectionExpression="video_id, queries",
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
            
        for item in items:
            video_id = item.get('video_id')
            queries = item.get('queries', [])
            for q in queries:
                if q and isinstance(q, str):
                    all_queries.append((q.strip(), video_id))
                    
        return all_queries
    except Exception as e:
        print(f"❌ Error scanning DynamoDB: {e}")
        print("Please verify your AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) and AWS_DEFAULT_REGION.")
        raise

def main():
    if not all([QDRANT_URL, QDRANT_API_KEY, HF_API_KEY]):
        print("Missing required API keys (QDRANT_URL, QDRANT_API_KEY, HF_API_KEY) in .env")
        return

    # 1. Fetch queries from DynamoDB
    try:
        all_queries = get_queries_from_dynamodb(DYNAMODB_TABLE)
    except Exception:
        print("Failed to retrieve queries. Exiting.")
        return

    # Deduplicate queries, keeping the first video_id mapping
    unique_queries: Dict[str, str] = {}
    for q, vid in all_queries:
        if q not in unique_queries:
            unique_queries[q] = vid
            
    print(f"\n📊 DynamoDB Scan Results:")
    print(f"Total query mappings found: {len(all_queries)}")
    print(f"Total unique queries:       {len(unique_queries)}")
    
    if not unique_queries:
        print("No queries found in DynamoDB. Exiting.")
        return

    # 2. Ask the user if they want to proceed with embedding and uploading
    if "--yes" in sys.argv:
        print("\nAuto-proceeding with upload (non-interactive mode).")
        recreate_collection = False
    else:
        try:
            user_input = input("\nDo you want to generate embeddings and upload these queries to Qdrant? (y/n) [y]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled by user.")
            return
            
        if user_input not in ('', 'y', 'yes'):
            print("Operation cancelled by user.")
            return

        # Ask the user if they want to clean up / recreate the Qdrant collection
        try:
            cleanup_input = input("Do you want to clear/recreate the existing query collection in Qdrant first? (y/n) [n]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled by user.")
            return
            
        recreate_collection = cleanup_input in ('y', 'yes')

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60.0)
    
    # Create or recreate collection based on user preference
    print(f"\nChecking collection '{COLLECTION_NAME}' in Qdrant...")
    if recreate_collection:
        print(f"Recreating collection '{COLLECTION_NAME}' (deleting existing data)...")
        if client.collection_exists(collection_name=COLLECTION_NAME):
            client.delete_collection(collection_name=COLLECTION_NAME)
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )
    else:
        if not client.collection_exists(collection_name=COLLECTION_NAME):
            print(f"Creating collection '{COLLECTION_NAME}'...")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            )
        else:
            print(f"Collection '{COLLECTION_NAME}' already exists. New queries will be appended.")

    # Generate deterministic UUIDs for all queries
    query_to_id = {q: str(uuid.uuid5(uuid.NAMESPACE_URL, q)) for q in unique_queries}
    all_ids = list(query_to_id.values())
    
    # Check Qdrant for existing IDs in batches of 100
    print("Checking Qdrant for existing query embeddings...")
    existing_ids = set()
    for j in range(0, len(all_ids), 100):
        batch_ids = all_ids[j:j+100]
        try:
            retrieved = client.retrieve(
                collection_name=COLLECTION_NAME,
                ids=batch_ids,
                with_payload=False,
                with_vectors=False
            )
            for point in retrieved:
                existing_ids.add(str(point.id))
        except Exception as e:
            print(f"Warning during Qdrant check: {e}")
            
    # Filter out queries that are already embedded and uploaded
    queries_to_process = []
    for q, vid in unique_queries.items():
        q_id = query_to_id[q]
        if q_id not in existing_ids:
            queries_to_process.append((q, vid))
            
    print(f"Skipping {len(unique_queries) - len(queries_to_process)} queries already present in Qdrant.")
    print(f"Need to embed and upload {len(queries_to_process)} new queries.")
    
    if not queries_to_process:
        print("✅ All queries are already up-to-date in Qdrant! Done.")
        return

    # Process only the new queries in batches of 50
    batch_size = 50
    
    for i in range(0, len(queries_to_process), batch_size):
        batch = queries_to_process[i:i+batch_size]
        texts = [item[0] for item in batch]
        
        print(f"Generating embeddings for batch {i//batch_size + 1}...")
        embeddings = get_embeddings(texts)
        
        points = []
        for (query_text, vid), emb in zip(batch, embeddings):
            # Generate deterministic UUID based on the query text to prevent duplicates in Qdrant
            point_id = query_to_id[query_text]
            
            points.append(
                PointStruct(
                    id=point_id,
                    vector=emb,
                    payload={"query": query_text, "video_id": vid}
                )
            )
            
        print(f"Uploading batch {i//batch_size + 1} to Qdrant...")
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
    
    print("✅ New queries successfully embedded and stored in Qdrant!")

if __name__ == "__main__":
    main()
