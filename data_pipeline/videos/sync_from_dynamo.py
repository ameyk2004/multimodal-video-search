"""
sync_from_dynamo.py

Pulls the CORRECT `stories` and `musical_segments` data from the NEW DynamoDB
single-table (`sadhananandadeep-metadata`) and writes it back into the local
enriched_metadata JSON files.

Access patterns used:
  • GSI1 (GSI1PK = "VIDEOS") → discover all video_ids
  • GSI2 (video_id = <id>)   → fetch every STORY# and MUSIC# item for that video

Two cases handled:
  1. Local *_meta.json EXISTS  → update stories & musical_segments from DynamoDB
  2. Local *_meta.json MISSING → create a new <video_id>_meta.json from DynamoDB

Run locally:
    python data_pipeline/videos/sync_from_dynamo.py

Or use the Colab version in:
    data_pipeline/colab/cell_3_5_sync_from_dynamo.py
"""

import json
import os
import decimal
import glob
import logging
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

NEW_TABLE_NAME = "sadhananandadeep-metadata"


def decimal_to_native(obj):
    """Recursively convert Decimal objects to int/float for JSON serialisation."""
    if isinstance(obj, list):
        return [decimal_to_native(v) for v in obj]
    if isinstance(obj, dict):
        return {k: decimal_to_native(v) for k, v in obj.items()}
    if isinstance(obj, decimal.Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


def _fetch_all_pages(query_fn, **kwargs) -> list:
    """Run a paginated DynamoDB query/scan and return all items."""
    response = query_fn(**kwargs)
    items = list(response.get("Items", []))
    while "LastEvaluatedKey" in response:
        response = query_fn(ExclusiveStartKey=response["LastEvaluatedKey"], **kwargs)
        items.extend(response.get("Items", []))
    return items


def _story_item_to_dict(item: dict) -> dict:
    """Convert a STORY# DynamoDB item into the legacy nested story format."""
    return {
        "title":                       item.get("title", ""),
        "title_english":               item.get("title_english", ""),
        "moral":                       item.get("moral", ""),
        "character_or_saint":          item.get("character_or_saint", ""),
        "normalized_saint_name":       item.get("normalized_saint_name", ""),
        "normalized_saint_name_english": item.get("normalized_saint_name_english", ""),
        "associated_topics":           decimal_to_native(item.get("associated_topics", [])),
        "exact_start_text":            item.get("exact_start_text", ""),
        "start_time_seconds":          decimal_to_native(item.get("start_time_seconds", 0)),
        "end_time_seconds":            decimal_to_native(item.get("end_time_seconds", 0)),
    }


def _music_item_to_dict(item: dict) -> dict:
    """Convert a MUSIC# DynamoDB item into the legacy nested musical_segment format."""
    return {
        "name":               item.get("name", ""),
        "name_english":       item.get("name_english", ""),
        "type":               item.get("type", ""),
        "saint":              item.get("saint", ""),
        "saint_english":      item.get("saint_english", ""),
        "exact_start_text":   item.get("exact_start_text", ""),
        "start_time_seconds": decimal_to_native(item.get("start_time_seconds", 0)),
        "end_time_seconds":   decimal_to_native(item.get("end_time_seconds", 0)),
    }


def sync_dynamo_to_meta(
    meta_dir:   str,
    table_name: str  = NEW_TABLE_NAME,
    region:     str  = "us-east-1",
    dry_run:    bool = False,
):
    """
    Scans sadhananandadeep-metadata (new single-table design) and syncs the
    local enriched_metadata JSON files.

    Parameters
    ----------
    meta_dir   : Path to the `enriched_metadata/` folder.
    table_name : DynamoDB table name (should be sadhananandadeep-metadata).
    region     : AWS region.
    dry_run    : If True, print what would change but do NOT write files.
    """
    dynamodb = boto3.resource("dynamodb", region_name=region)
    client   = boto3.client("dynamodb", region_name=region)

    # ── 1. Verify table exists ─────────────────────────────────────────────
    try:
        client.describe_table(TableName=table_name)
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ResourceNotFoundException":
            raise ValueError(
                f"\n❌ DynamoDB table '{table_name}' not found in region '{region}'.\n"
                "Make sure your AWS credentials are set and the table exists."
            )
        raise

    table = dynamodb.Table(table_name)

    # ── 2. Discover all video_ids via GSI1 (VIDEOS) ───────────────────────
    logging.info(f"Querying GSI1 (VIDEOS) from table '{table_name}'…")

    def _query_gsi1(**kwargs):
        return table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq("VIDEOS"),
            **kwargs,
        )

    video_items = _fetch_all_pages(_query_gsi1)
    logging.info(f"Found {len(video_items)} video records in DynamoDB.")

    # Build map: video_id → {title, topics, queries, ...} (video-level fields only)
    dynamo_videos: dict[str, dict] = {}
    for item in video_items:
        vid = item.get("video_id")
        if vid:
            dynamo_videos[vid] = decimal_to_native(item)

    # ── 3. For each video, fetch all STORY# and MUSIC# via GSI2 ──────────
    logging.info("Fetching stories & music segments per video via GSI2…")
    dynamo_stories: dict[str, list] = {}
    dynamo_music:   dict[str, list] = {}

    for vid in dynamo_videos:
        def _query_gsi2(vid=vid, **kwargs):
            return table.query(
                IndexName="GSI2",
                KeyConditionExpression=Key("video_id").eq(vid),
                **kwargs,
            )

        children = _fetch_all_pages(_query_gsi2)
        dynamo_stories[vid] = [
            _story_item_to_dict(i)
            for i in children
            if i.get("SK", "").startswith("STORY#")
        ]
        dynamo_music[vid] = [
            _music_item_to_dict(i)
            for i in children
            if i.get("SK", "").startswith("MUSIC#")
        ]

    # ── 4. Build set of local video IDs ──────────────────────────────────
    meta_files = glob.glob(os.path.join(meta_dir, "*_meta.json"))
    logging.info(f"Found {len(meta_files)} local meta files in '{meta_dir}'.")

    local_video_ids = {
        os.path.splitext(os.path.basename(fp))[0].replace("_meta", "")
        for fp in meta_files
    }

    updated      = 0
    skipped      = 0
    not_in_dynamo = 0
    created      = 0

    # ── 5a. Update existing local files ──────────────────────────────────
    for filepath in sorted(meta_files):
        video_id = os.path.splitext(os.path.basename(filepath))[0].replace("_meta", "")

        if video_id not in dynamo_videos:
            logging.warning(f"  ⚠  {video_id}: no DynamoDB record — skipping.")
            not_in_dynamo += 1
            continue

        db_stories = dynamo_stories.get(video_id, [])
        db_music   = dynamo_music.get(video_id, [])

        with open(filepath, "r", encoding="utf-8") as f:
            local_data = json.load(f)

        local_stories = local_data.get("stories", [])
        local_music   = local_data.get("musical_segments", [])

        changed = (
            json.dumps(db_stories, ensure_ascii=False, sort_keys=True) !=
            json.dumps(local_stories, ensure_ascii=False, sort_keys=True)
        ) or (
            json.dumps(db_music, ensure_ascii=False, sort_keys=True) !=
            json.dumps(local_music, ensure_ascii=False, sort_keys=True)
        )

        if not changed:
            logging.info(f"  ✓  {video_id}: already in sync.")
            skipped += 1
            continue

        logging.info(
            f"  ↻  {video_id}: updating "
            f"stories ({len(local_stories)}→{len(db_stories)})  "
            f"music ({len(local_music)}→{len(db_music)})"
        )

        if not dry_run:
            local_data["stories"]          = db_stories
            local_data["musical_segments"] = db_music
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(local_data, f, ensure_ascii=False, indent=2)

        updated += 1

    # ── 5b. Create local files for DynamoDB videos with no local file ─────
    for vid, record in sorted(dynamo_videos.items()):
        if vid in local_video_ids:
            continue  # already has a local file

        target  = os.path.join(meta_dir, f"{vid}_meta.json")
        new_data = {
            "video_id":             vid,
            "title":                record.get("title", ""),
            "stories":              dynamo_stories.get(vid, []),
            "musical_segments":     dynamo_music.get(vid, []),
            "topics":               record.get("topics", []),
            "queries":              record.get("queries", []),
            "actionable_practices": record.get("actionable_practices", []),
            "quoted_verses":        record.get("quoted_verses", []),
        }

        logging.info(
            f"  ✨  {vid}: no local file found — CREATING from DynamoDB "
            f"(stories={len(new_data['stories'])}, "
            f"music={len(new_data['musical_segments'])})."
        )

        if not dry_run:
            with open(target, "w", encoding="utf-8") as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)

        created += 1

    # ── 6. Summary ────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print(f"  Sync complete {'(DRY RUN — no files written) ' if dry_run else ''}  ")
    print("=" * 55)
    print(f"  Files updated      : {updated}")
    print(f"  Already in sync    : {skipped}")
    print(f"  Not in DynamoDB    : {not_in_dynamo}")
    print(f"  New files created  : {created}")
    print("=" * 55 + "\n")

    if not dry_run and (updated > 0 or created > 0):
        print("✅  Local meta files now match DynamoDB.")
        print("   You can safely commit these changes to Git.")


# ─────────────────────────────────────────────────────────────────────────────
# Local usage
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()  # picks up AWS credentials from your .env

    base_dir   = os.path.dirname(os.path.abspath(__file__))
    META_DIR   = os.path.join(base_dir, "enriched_metadata")
    TABLE_NAME = os.environ.get("DYNAMODB_TABLE", NEW_TABLE_NAME)
    REGION     = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))

    sync_dynamo_to_meta(
        meta_dir   = META_DIR,
        table_name = TABLE_NAME,
        region     = REGION,
        dry_run    = False,  # set True to preview changes without writing files
    )
