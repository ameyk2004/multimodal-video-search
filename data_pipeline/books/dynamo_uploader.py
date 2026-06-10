import json
import decimal
import os
import glob
import boto3
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def upload_book_metadata(input_dir: str, table_name: str = "sadhananandadeep-content"):
    """
    Reads all JSON files in the input_dir and uploads them to the specified DynamoDB table.
    Ensures that type="book" is set and video_id is uniquely prefixed.
    """
    region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))
    dynamodb = boto3.resource('dynamodb', region_name=region)
    client = boto3.client('dynamodb', region_name=region)
    
    try:
        client.describe_table(TableName=table_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise ValueError(
                f"\n❌ ERROR: DynamoDB table '{table_name}' does not exist!\n"
            )
        else:
            raise

    table = dynamodb.Table(table_name)
    
    files = glob.glob(os.path.join(input_dir, "*.json"))
    if not files:
        logging.warning(f"No metadata JSON files found in {input_dir}")
        return

    logging.info(f"Found {len(files)} books metadata files to upload to DynamoDB table '{table_name}'.")

    success_count = 0
    with table.batch_writer() as batch:
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f, parse_float=decimal.Decimal)
                
                book_name = data.get("book_name")
                if not book_name:
                    base_name = os.path.splitext(os.path.basename(filepath))[0]
                    book_name = base_name.replace("_meta", "")
                
                # To coexist with videos, we prefix the ID
                video_id = f"book_{book_name}"
                
                item = {
                    "video_id": video_id,
                    "type": "book",
                    "title": book_name,
                    "author": data.get("author", "अज्ञात"),
                    "date_written": data.get("date_written", "अज्ञात"),
                    "summary": data.get("summary", ""),
                    "questions": data.get("questions", []),
                    "key_learnings": data.get("key_learnings", []),
                    "for_whom": data.get("for_whom", ""),
                    "mood": data.get("mood", ""),
                    "topics": data.get("topics", []),
                    "structure_type": data.get("structure_type", "")
                }
                
                batch.put_item(Item=item)
                success_count += 1
                logging.info(f"Queued upload for book: {book_name} (ID: {video_id})")
                
            except Exception as e:
                logging.error(f"Failed to process {filepath}: {e}")
                raise

    if success_count == 0:
        logging.error("Failed to upload any records.")
    else:
        logging.info(f"Successfully uploaded {success_count} books to DynamoDB.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_directory = os.path.join(base_dir, "books_enriched_metadata")
    
    target_table = os.environ.get("DYNAMODB_TABLE", "sadhananandadeep-content")
    
    upload_book_metadata(input_directory, target_table)
