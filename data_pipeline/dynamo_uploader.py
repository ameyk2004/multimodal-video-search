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
    region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))
    dynamodb = boto3.resource('dynamodb', region_name=region)
    client = boto3.client('dynamodb', region_name=region)
    
    # Check if table exists
    try:
        client.describe_table(TableName=table_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise ValueError(
                f"\n❌ ERROR: DynamoDB table '{table_name}' does not exist!\n"
                f"Please deploy the cloud-backend stack first before uploading metadata.\n"
                f"1. Open your terminal on your local machine.\n"
                f"2. Run: cd cloud-backend && make release\n"
                f"3. Once the stack is fully deployed, run this Colab cell again."
            )
        else:
            raise

    table = dynamodb.Table(table_name)
    
    files = glob.glob(os.path.join(input_dir, "*.json"))
    if not files:
        logging.warning(f"No metadata JSON files found in {input_dir}")
        return

    logging.info(f"Found {len(files)} metadata files to upload to DynamoDB table '{table_name}'.")

    success_count = 0
    with table.batch_writer() as batch:
        for filepath in files:
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            # Strip suffixes if the file is named e.g. '9RAqjOZEOh4_meta.json'
            extracted_video_id = base_name.replace("_meta", "").replace("_enriched", "")
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Use video_id from JSON if it exists, otherwise use the filename
                final_video_id = data.get("video_id", extracted_video_id)
                
                # DynamoDB Item structure
                item = {
                    "video_id": final_video_id,
                    "topics": data.get("topics", data.get("primary_topics", [])),
                    "suggested_queries": data.get("suggested_queries", []),
                    "stories": data.get("stories_found", [])
                }
                
                batch.put_item(Item=item)
                success_count += 1
                logging.info(f"Queued upload for video: {final_video_id}")
                
            except Exception as e:
                logging.error(f"Failed to process {filepath}: {e}")
                raise

    if success_count == 0:
        logging.error("Failed to upload any records. Check the logs above.")
        raise ValueError("0 records uploaded to DynamoDB.")
        
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
