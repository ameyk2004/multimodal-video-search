"""
dynamo_uploader.py

Uploads enriched video metadata from local JSON files to the NEW DynamoDB
single-table schema (`sadhananandadeep-metadata`).

Schema written:
  VIDEO#<id>  / METADATA          — video-level metadata (topics, queries, etc.)
  BOOK#<id>   / METADATA          — book-level metadata
  SAINT#<nm>  / METADATA          — saint profile (created only if not present)
  SAINT#<nm>  / STORY#<uuid>      — individual story segment
  SAINT#<nm>  / MUSIC#<uuid>      — individual musical segment

GSI1PK values  : VIDEOS | BOOKS | SAINTS | STORIES | MUSIC
GSI2 key       : video_id (hash) + SK (range)  → fetch all content for a video

Idempotency:
  • VIDEO / BOOK items: put_item overwrites on same PK+SK — safe upsert.
  • SAINT METADATA:     written with ConditionExpression so existing hand-crafted
                        bios / imageUrls are NEVER overwritten.
  • STORY / MUSIC:      UUIDs are deterministic (uuid5 of "video_id:start_time")
                        so re-running produces the same IDs and overwrites safely.
"""

import json
import decimal
import os
import glob
import uuid
import logging
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

NEW_TABLE_NAME = "sadhananandadeep-metadata"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _to_decimal(obj):
    """Recursively convert float → Decimal (required by boto3 for DynamoDB)."""
    if isinstance(obj, float):
        return decimal.Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_decimal(v) for v in obj]
    return obj


def _deterministic_id(video_id: str, discriminator: str) -> str:
    """
    Generate a stable UUID from (video_id, discriminator).
    Same inputs always produce the same UUID, so re-runs are idempotent.
    """
    key = f"{video_id}:{discriminator}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


def _ensure_saint(table, saint_name: str, processed_saints: set, batch):
    """
    Write a placeholder SAINT METADATA item if one doesn't already exist.
    Uses ConditionExpression so existing hand-crafted bios are never touched.
    We can't use condition expressions inside a batch_writer, so this is a
    direct put_item call done outside the batch.
    """
    if saint_name in processed_saints:
        return
    try:
        table.put_item(
            Item={
                "PK":      f"SAINT#{saint_name}",
                "SK":      "METADATA",
                "GSI1PK":  "SAINTS",
                "GSI1SK":  saint_name,
                "name":    saint_name,
                "quote":   "Tap to explore teachings.",
                "tradition": "Various",
                "era":     "Unknown Era",
                "learnings": [],
                "fullBio": "",
                "imageUrl": "",
            },
            ConditionExpression="attribute_not_exists(PK)",  # never overwrite existing bios
        )
        logging.info(f"  ✨ Created saint profile for: {saint_name}")
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise  # unexpected error — re-raise
        # Saint already exists — fine, do nothing
    finally:
        processed_saints.add(saint_name)


# ─────────────────────────────────────────────────────────────────────────────
# Main upload function
# ─────────────────────────────────────────────────────────────────────────────

def upload_metadata(input_dir: str, table_name: str = NEW_TABLE_NAME):
    """
    Reads all *_meta.json files in input_dir and upserts them into the new
    DynamoDB single-table design.
    """
    region   = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))
    dynamodb = boto3.resource("dynamodb", region_name=region)
    client   = boto3.client("dynamodb", region_name=region)

    # Verify table exists before starting
    try:
        client.describe_table(TableName=table_name)
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ResourceNotFoundException":
            raise ValueError(
                f"\n❌ ERROR: DynamoDB table '{table_name}' does not exist!\n"
                f"Please deploy the cloud-backend stack first.\n"
                f"  cd cloud-backend && make release\n"
                f"Then re-run this cell."
            )
        raise

    table = dynamodb.Table(table_name)

    files = sorted(glob.glob(os.path.join(input_dir, "*_meta.json")))
    if not files:
        logging.warning(f"No *_meta.json files found in {input_dir}")
        return

    logging.info(f"Found {len(files)} enriched metadata files → uploading to '{table_name}'")

    processed_saints: set = set()
    stats = {"videos": 0, "stories": 0, "music": 0, "saints": 0, "errors": 0}

    with table.batch_writer() as batch:
        for filepath in files:
            base   = os.path.splitext(os.path.basename(filepath))[0]
            f_vid  = base.replace("_meta", "").replace("_enriched", "")

            try:
                with open(filepath, "r", encoding="utf-8") as fh:
                    data = json.load(fh, parse_float=decimal.Decimal)
            except Exception as exc:
                logging.error(f"Failed to read {filepath}: {exc}")
                stats["errors"] += 1
                continue

            video_id  = data.get("video_id", f_vid)
            is_book   = data.get("type") == "book"
            pk_prefix = "BOOK" if is_book else "VIDEO"
            gsi1pk    = "BOOKS" if is_book else "VIDEOS"

            # ── 1. Upsert VIDEO / BOOK METADATA item ─────────────────────────
            video_record: dict = {
                "PK":      f"{pk_prefix}#{video_id}",
                "SK":      "METADATA",
                "GSI1PK":  gsi1pk,
                "GSI1SK":  str(data.get("created_at", "0")),
                "video_id": video_id,
            }
            # Copy all non-nested fields
            skip_keys = {"stories", "musical_segments", "stories_found"}
            for k, v in data.items():
                if k not in skip_keys:
                    video_record[k] = _to_decimal(v)

            batch.put_item(Item=video_record)
            stats["videos"] += 1
            logging.info(
                f"  📹 Queued VIDEO#{video_id} — "
                f"topics={len(data.get('topics', []))}, "
                f"queries={len(data.get('queries', []))}"
            )

            if is_book:
                continue  # books have no stories / musical segments

            # ── 2. Upsert Stories ─────────────────────────────────────────────
            stories = data.get("stories", data.get("stories_found", []))
            for story in stories:
                saint_name = (
                    story.get("normalized_saint_name")
                    or story.get("character_or_saint")
                    or "Unknown Saint"
                )
                start    = story.get("start_time_seconds", 0)
                story_id = _deterministic_id(video_id, str(start))

                _ensure_saint(table, saint_name, processed_saints, batch)
                if saint_name not in processed_saints:
                    stats["saints"] += 1

                batch.put_item(Item={
                    "PK":     f"SAINT#{saint_name}",
                    "SK":     f"STORY#{story_id}",
                    "GSI1PK": "STORIES",
                    "GSI1SK": str(start),
                    # GSI2 access: fetch all stories for a video
                    "video_id":                    video_id,
                    "story_id":                    story_id,
                    "title":                       story.get("title", data.get("title", "प्रवचन")),
                    "title_english":               story.get("title_english", ""),
                    "moral":                       story.get("moral", ""),
                    "character_or_saint":          story.get("character_or_saint", saint_name),
                    "normalized_saint_name":       saint_name,
                    "normalized_saint_name_english": story.get("normalized_saint_name_english", ""),
                    "associated_topics":           story.get("associated_topics", []),
                    "exact_start_text":            story.get("exact_start_text", ""),
                    "start_time_seconds":          _to_decimal(start),
                    "end_time_seconds":            _to_decimal(story.get("end_time_seconds", 0)),
                })
                stats["stories"] += 1

            # ── 3. Upsert Musical Segments ────────────────────────────────────
            for music in data.get("musical_segments", []):
                saint_name = music.get("saint") or "Unknown Saint"
                start      = music.get("start_time_seconds", 0)
                music_id   = _deterministic_id(video_id, f"music_{start}")

                _ensure_saint(table, saint_name, processed_saints, batch)
                if saint_name not in processed_saints:
                    stats["saints"] += 1

                batch.put_item(Item={
                    "PK":     f"SAINT#{saint_name}",
                    "SK":     f"MUSIC#{music_id}",
                    "GSI1PK": "MUSIC",
                    "GSI1SK": str(start),
                    "video_id":           video_id,
                    "music_id":           music_id,
                    "name":               music.get("name", "Unknown Bhajan"),
                    "name_english":       music.get("name_english", ""),
                    "type":               music.get("type", "Abhang"),
                    "saint":              saint_name,
                    "saint_english":      music.get("saint_english", ""),
                    "exact_start_text":   music.get("exact_start_text", ""),
                    "start_time_seconds": _to_decimal(start),
                    "end_time_seconds":   _to_decimal(music.get("end_time_seconds", 0)),
                })
                stats["music"] += 1

    logging.info("\n" + "=" * 55)
    logging.info(f"  UPLOAD COMPLETE → {table_name}")
    logging.info("=" * 55)
    logging.info(f"  Videos/Books   : {stats['videos']}")
    logging.info(f"  Stories        : {stats['stories']}")
    logging.info(f"  Music segments : {stats['music']}")
    logging.info(f"  Saint profiles : {stats['saints']} created")
    logging.info(f"  Errors         : {stats['errors']}")
    logging.info("=" * 55)

    if stats["errors"] > 0:
        raise RuntimeError(f"{stats['errors']} file(s) failed to upload. Check logs above.")


# ─────────────────────────────────────────────────────────────────────────────
# Local / CLI entry-point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    base_dir       = os.path.dirname(os.path.abspath(__file__))
    input_directory = os.path.join(base_dir, "enriched_metadata")
    target_table   = os.environ.get("DYNAMODB_TABLE", NEW_TABLE_NAME)

    upload_metadata(input_directory, target_table)
