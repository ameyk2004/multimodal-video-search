import json
import os
import glob
import boto3
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def upload_metadata(input_dir: str, table_name: str = "guru-video-metadata"):
    """
    Reads all JSON files in the input_dir and uploads them to the specified DynamoDB table.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    files = glob.glob(os.path.join(input_dir, "*.json"))
    if not files:
        logging.warning(f"No metadata JSON files found in {input_dir}")
        return

    logging.info(f"Found {len(files)} metadata files to upload to DynamoDB table '{table_name}'.")

    success_count = 0
    with table.batch_writer() as batch:
        for filepath in files:
            video_id = os.path.splitext(os.path.basename(filepath))[0]
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # DynamoDB Item structure
                item = {
                    "video_id": video_id,
                    "topics": data.get("topics", []),
                    "suggested_queries": data.get("suggested_queries", []),
                    "stories": data.get("stories", [])
                }
                
                batch.put_item(Item=item)
                success_count += 1
                logging.info(f"Queued upload for video: {video_id}")
                
            except Exception as e:
                logging.error(f"Failed to process {filepath}: {e}")

    logging.info(f"Successfully uploaded {success_count} records to DynamoDB.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Path to enriched metadata
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_directory = os.path.join(base_dir, "enriched_metadata")
    
    # User can override table name via env var, defaults to what we deployed
    target_table = os.environ.get("DYNAMODB_TABLE", "guru-video-metadata")
    
    upload_metadata(input_directory, target_table)
