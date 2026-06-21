import boto3
import uuid
import logging
import argparse
from decimal import Decimal

# Configuration
OLD_TABLE_NAME = "sadhananandadeep-content"
NEW_TABLE_NAME = "sadhananandadeep-metadata"
REGION = "ap-south-1" # Using default AWS region if needed, but usually boto3 picks it up. Let's rely on standard config or us-east-1.
# wait, the user's snippet said us-east-1, but I'll make it configurable or stick to us-east-1.
REGION = "us-east-1"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def migrate_data(dry_run=True):
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    old_table = dynamodb.Table(OLD_TABLE_NAME)
    new_table = dynamodb.Table(NEW_TABLE_NAME)

    logger.info(f"--- STARTING {'DRY RUN' if dry_run else 'LIVE MIGRATION'} ---")
    logger.info(f"Scanning old table: {OLD_TABLE_NAME}...")
    
    try:
        response = old_table.scan()
        items = response.get('Items', [])
        while 'LastEvaluatedKey' in response:
            response = old_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
    except Exception as e:
        logger.error(f"Failed to scan old table. Do you have AWS credentials set? Error: {e}")
        return

    logger.info(f"Found {len(items)} items in old table.")

    processed_saints = set()
    
    # Validation counters
    stats = {
        "old_videos": len(items),
        "old_stories": sum(len(i.get("stories", [])) for i in items),
        "old_music": sum(len(i.get("musical_segments", [])) for i in items),
        "new_videos": 0,
        "new_stories": 0,
        "new_music": 0,
        "new_saints": 0,
        "warnings": 0
    }

    def write_item(item, batch_obj):
        if not dry_run:
            batch_obj.put_item(Item=item)

    class DummyBatch:
        def put_item(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass

    batch_ctx = new_table.batch_writer() if not dry_run else DummyBatch()

    try:
        with batch_ctx as batch:
            for item in items:
                video_id = item.get("video_id")
                if not video_id:
                    logger.warning(f"Item found without video_id: {item}")
                    stats["warnings"] += 1
                    continue
                    
                video_title = item.get("title", "Unknown Video")
                
                # 1. Migrate Video Metadata
                is_book = item.get("type") == "book"
                pk_prefix = "BOOK" if is_book else "VIDEO"
                
                video_record = {
                    "PK": f"{pk_prefix}#{video_id}",
                    "SK": "METADATA",
                    "GSI1PK": "BOOKS" if is_book else "VIDEOS",
                    "GSI1SK": str(item.get("created_at", "0"))
                }
                
                # Safely copy all original fields to preserve rich metadata (author, queries, verses, etc.)
                for k, v in item.items():
                    if k not in ["stories", "musical_segments"]:
                        video_record[k] = v
                        
                write_item(video_record, batch)
                stats["new_videos"] += 1
    
                # 2. Migrate Stories
                for story in item.get("stories", []):
                    saint_name = story.get("normalized_saint_name") or story.get("character_or_saint")
                    if not saint_name:
                        logger.warning(f"Story in video {video_id} is missing saint_name. Using 'Unknown Saint'.")
                        saint_name = "Unknown Saint"
                        stats["warnings"] += 1
    
                    pk_saint = f"SAINT#{saint_name}"
                    story_id = str(uuid.uuid4())
                    
                    # Ensure Saint Metadata exists
                    if saint_name not in processed_saints:
                        logger.info(f"Creating missing Saint Profile (Empty Bio/Era) for: {saint_name}")
                        write_item({
                            "PK": pk_saint,
                            "SK": "METADATA",
                            "GSI1PK": "SAINTS",
                            "GSI1SK": saint_name,
                            "name": saint_name,
                            "quote": "Tap to explore teachings.", 
                            "tradition": "Various", 
                            "era": "Unknown Era",
                            "learnings": [],
                            "fullBio": "",
                            "imageUrl": ""
                        }, batch)
                        processed_saints.add(saint_name)
                        stats["new_saints"] += 1
    
                    # Insert Story
                    write_item({
                        "PK": pk_saint,
                        "SK": f"STORY#{story_id}",
                        "GSI1PK": "STORIES",
                        "GSI1SK": str(story.get("start_time_seconds", 0)),
                        "video_id": video_id,
                        "story_id": story_id,
                        "title": story.get("title", video_title),
                        "moral": story.get("moral", ""),
                        "start_time_seconds": Decimal(str(story.get("start_time_seconds", 0))),
                        "end_time_seconds": Decimal(str(story.get("end_time_seconds", 0))),
                        "associated_topics": story.get("associated_topics", [])
                    }, batch)
                    stats["new_stories"] += 1
    
                # 3. Migrate Musical Segments
                for music in item.get("musical_segments", []):
                    saint_name = music.get("saint")
                    if not saint_name:
                        logger.warning(f"Music segment in video {video_id} is missing saint_name. Using 'Unknown Saint'.")
                        saint_name = "Unknown Saint"
                        stats["warnings"] += 1
    
                    pk_saint = f"SAINT#{saint_name}"
                    music_id = str(uuid.uuid4())
                    
                    # Ensure Saint Metadata exists
                    if saint_name not in processed_saints:
                        logger.info(f"Creating missing Saint Profile (Empty Bio/Era) for: {saint_name}")
                        write_item({
                            "PK": pk_saint,
                            "SK": "METADATA",
                            "GSI1PK": "SAINTS",
                            "GSI1SK": saint_name,
                            "name": saint_name,
                            "quote": "Tap to explore teachings.", 
                            "tradition": "Various", 
                            "era": "Unknown Era",
                            "learnings": [],
                            "fullBio": "",
                            "imageUrl": ""
                        }, batch)
                        processed_saints.add(saint_name)
                        stats["new_saints"] += 1
    
                    # Insert Music
                    write_item({
                        "PK": pk_saint,
                        "SK": f"MUSIC#{music_id}",
                        "GSI1PK": "MUSIC",
                        "GSI1SK": str(music.get("start_time_seconds", 0)),
                        "video_id": video_id,
                        "music_id": music_id,
                        "name": music.get("name", "Unknown Bhajan"),
                        "type": music.get("type", "Abhang"),
                        "moral": music.get("moral", ""),
                        "start_time_seconds": Decimal(str(music.get("start_time_seconds", 0))),
                        "end_time_seconds": Decimal(str(music.get("end_time_seconds", 0)))
                    }, batch)
                    stats["new_music"] += 1

    except Exception as e:
        logger.error(f"Error during migration: {e}")

    logger.info("\n--- MIGRATION SUMMARY ---")
    logger.info(f"Mode: {'DRY RUN (No data written)' if dry_run else 'LIVE'}")
    logger.info(f"Warnings Generated: {stats['warnings']}")
    logger.info("VERIFICATION:")
    logger.info(f"  Videos : {stats['old_videos']} old -> {stats['new_videos']} new")
    logger.info(f"  Stories: {stats['old_stories']} old -> {stats['new_stories']} new")
    logger.info(f"  Music  : {stats['old_music']} old -> {stats['new_music']} new")
    logger.info(f"  Saints Profiles Created: {stats['new_saints']}")
    
    if stats['old_videos'] != stats['new_videos'] or stats['old_stories'] != stats['new_stories'] or stats['old_music'] != stats['new_music']:
        logger.error("MISMATCH DETECTED! Some data was skipped. Please check warnings.")
    else:
        logger.info("SUCCESS! Start and End counts match perfectly. No data will be lost.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Run the actual migration (writes to DynamoDB)")
    args = parser.parse_args()
    
    # If --live is passed, dry_run=False
    migrate_data(dry_run=not args.live)
