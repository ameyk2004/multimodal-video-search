import boto3
import logging
import os
import glob
import json
import sys
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "sadhananandadeep-content")

# =========================
# CONFIGURATION
# =========================
# I will populate these variables based on your instructions in the chat!

BHAJANS_TO_DELETE = {
    "अज्ञात",
    "जानकी स्मरण जय जय राम",
    "जानकी जीवन स्मरण जय जय राम",
    "जानकी जीवन स्मरण",
    "जानकी जीवनस्मरण जय जय राम",
    "जानकी अनुस्मरणे जय राम",
    "जानकीस्मरण जय जय राम",
    "जय जय राम",
}

BHAJANS_TO_RENAME = {
    # e.g., "wrong_name_1": "correct_name_1",
}

# =========================
# DYNAMODB SETUP
# =========================

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

# =========================
# HELPERS
# =========================

def scan_all_items():
    items = []
    response = table.scan()
    items.extend(response.get("Items", []))
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))
    return items

def clean_item(item):
    """
    Cleans up the musical_segments in-place based on the DELETE and RENAME config.
    Returns True if the item was changed.
    """
    changed = False
    video_id = item.get("video_id", "?")
    
    original_segments = item.get("musical_segments", [])
    if not original_segments:
        return False
        
    new_segments = []
    
    for seg in original_segments:
        name = seg.get("name")
        
        if not name:
            logging.info(f"[DELETE] video={video_id} - Removing hallucinated segment with EMPTY title")
            changed = True
            continue
            
        # Exception for Raghupati Raghav Rajaram
        if "रघुपति" in name or "रघुपती" in name:
            if video_id != "fLPku9IH4UA":
                logging.info(f"[DELETE] video={video_id} - Removing Raghupati Raghav variation: {name!r}")
                changed = True
                continue
            
        # 1. Handle Deletions
        if name in BHAJANS_TO_DELETE:
            logging.info(f"[DELETE] video={video_id} - Removing hallucinated bhajan: {name!r}")
            changed = True
            continue # skip adding it to new_segments
            
        # 2. Handle Renames
        if name in BHAJANS_TO_RENAME:
            new_name = BHAJANS_TO_RENAME[name]
            logging.info(f"[RENAME] video={video_id} - {name!r} → {new_name!r}")
            seg["name"] = new_name
            changed = True
            
        new_segments.append(seg)
        
    if changed:
        item["musical_segments"] = new_segments
        
    return changed

def clean_local_files(directory="data_pipeline/enriched_metadata", dry_run=False):
    """
    Reads all local JSON files, applies deletions/renames, and rewrites them if changed.
    """
    json_files = glob.glob(os.path.join(directory, "*.json"))
    updated_files = 0
    
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                item = json.load(f)
                
            if clean_item(item):
                if not dry_run:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(item, f, ensure_ascii=False, indent=2)
                updated_files += 1
        except Exception as e:
            logging.error(f"Failed to clean local file {filepath}: {e}")
            
    action = "Would update" if dry_run else "Updated"
    logging.info(f"Done local cleaning. {action} {updated_files} JSON files.")

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        logging.info("=========================================")
        logging.info("🏃 DRY RUN MODE - No files will be saved")
        logging.info("=========================================")

    if not BHAJANS_TO_DELETE and not BHAJANS_TO_RENAME:
        logging.warning("No bhajans configured for deletion or renaming! Exiting.")
        sys.exit(0)

    # 1. Clean local JSON files
    logging.info("Starting cleanup of local JSON files...")
    clean_local_files(dry_run=dry_run)
    
    # 2. Clean DynamoDB
    logging.info("Starting cleanup of DynamoDB...")
    try:
        items = scan_all_items()
        logging.info(f"Total Items Scanned from DynamoDB: {len(items)}")
    
        updated_count = 0
        for item in items:
            if clean_item(item):
                video_id = item["video_id"]
                updated_count += 1
                if not dry_run:
                    try:
                        table.update_item(
                            Key={"video_id": video_id},
                            UpdateExpression="SET musical_segments = :ms",
                            ExpressionAttributeValues={
                                ":ms": item.get("musical_segments", []),
                            },
                        )
                    except Exception as e:
                        logging.error(f"Failed to update {video_id} in DynamoDB: {e}")
    
        action = "Would update" if dry_run else "Total Updated"
        logging.info(f"Done. {action} Items in DynamoDB: {updated_count}")
        
    except Exception as e:
        logging.error(f"Failed to scan or update DynamoDB: {e}")
        logging.info("Local files were still updated.")
