"""
sync_from_dynamo.py

Pulls the CORRECT `stories` and `musical_segments` data from DynamoDB and
writes it back into the local enriched_metadata JSON files.

Two cases handled:
  1. Local file EXISTS  → update stories & musical_segments from DynamoDB
  2. Local file MISSING → create a new <video_id>_meta.json from DynamoDB

Run locally:
    python data_pipeline/videos/sync_from_dynamo.py

Or paste the Colab version from:
    data_pipeline/colab/cell_3_5_sync_from_dynamo.py
"""

import json
import os
import decimal
import glob
import logging
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def decimal_to_native(obj):
    """Recursively convert Decimal objects to int/float for JSON serialisation."""
    if isinstance(obj, list):
        return [decimal_to_native(v) for v in obj]
    if isinstance(obj, dict):
        return {k: decimal_to_native(v) for k, v in obj.items()}
    if isinstance(obj, decimal.Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


def sync_dynamo_to_meta(
    meta_dir: str,
    table_name: str = "sadhananandadeep-content",
    region: str = "us-east-1",
    dry_run: bool = False,
):
    """
    Scans the DynamoDB table and syncs local meta JSON files.

    - If a local file exists  → updates stories & musical_segments from DynamoDB.
    - If no local file exists → creates a new <video_id>_meta.json from DynamoDB.
    - All other fields (topics, queries, actionable_practices, quoted_verses)
      are preserved exactly as-is in existing files.

    Parameters
    ----------
    meta_dir  : Path to the `enriched_metadata/` folder.
    table_name: DynamoDB table name.
    region    : AWS region.
    dry_run   : If True, print what would change but do NOT write files.
    """
    dynamodb = boto3.resource("dynamodb", region_name=region)

    # ── 1. Verify table exists ──────────────────────────────────────────
    client = boto3.client("dynamodb", region_name=region)
    try:
        client.describe_table(TableName=table_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            raise ValueError(
                f"\n❌  DynamoDB table '{table_name}' not found in region '{region}'.\n"
                "Make sure your AWS credentials are set and the table exists."
            )
        raise

    table = dynamodb.Table(table_name)

    # ── 2. Scan DynamoDB (paginated) ────────────────────────────────────
    logging.info(f"Scanning DynamoDB table '{table_name}'…")
    dynamo_items = {}

    response = table.scan(
        ProjectionExpression="video_id, #t, title, stories, musical_segments, "
                             "topics, queries, actionable_practices, quoted_verses",
        ExpressionAttributeNames={"#t": "type"}
    )
    for item in response.get("Items", []):
        vid = item.get("video_id")
        if vid:
            dynamo_items[vid] = item

    while "LastEvaluatedKey" in response:
        response = table.scan(
            ProjectionExpression="video_id, #t, title, stories, musical_segments, "
                                 "topics, queries, actionable_practices, quoted_verses",
            ExpressionAttributeNames={"#t": "type"},
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        for item in response.get("Items", []):
            vid = item.get("video_id")
            if vid:
                dynamo_items[vid] = item

    logging.info(f"Loaded {len(dynamo_items)} records from DynamoDB.")

    # ── 3. Build a set of local video IDs ───────────────────────────────
    meta_files = glob.glob(os.path.join(meta_dir, "*_meta.json"))
    logging.info(f"Found {len(meta_files)} local meta files in '{meta_dir}'.")

    local_video_ids = {
        os.path.splitext(os.path.basename(fp))[0].replace("_meta", "")
        for fp in meta_files
    }

    updated = 0
    skipped = 0
    not_in_dynamo = 0
    created = 0

    # ── 4a. Update existing local files ─────────────────────────────────
    for filepath in sorted(meta_files):
        video_id = os.path.splitext(os.path.basename(filepath))[0].replace("_meta", "")

        if video_id not in dynamo_items:
            logging.warning(f"  ⚠  {video_id}: no DynamoDB record — skipping.")
            not_in_dynamo += 1
            continue

        dynamo_record   = dynamo_items[video_id]
        dynamo_stories  = decimal_to_native(dynamo_record.get("stories", []))
        dynamo_music    = decimal_to_native(dynamo_record.get("musical_segments", []))

        with open(filepath, "r", encoding="utf-8") as f:
            local_data = json.load(f)

        local_stories = local_data.get("stories", [])
        local_music   = local_data.get("musical_segments", [])

        changed = (
            json.dumps(dynamo_stories, ensure_ascii=False, sort_keys=True) !=
            json.dumps(local_stories,  ensure_ascii=False, sort_keys=True)
        ) or (
            json.dumps(dynamo_music,  ensure_ascii=False, sort_keys=True) !=
            json.dumps(local_music,   ensure_ascii=False, sort_keys=True)
        )

        if not changed:
            logging.info(f"  ✓  {video_id}: already in sync.")
            skipped += 1
            continue

        logging.info(
            f"  ↻  {video_id}: updating "
            f"stories ({len(local_stories)}→{len(dynamo_stories)})  "
            f"music ({len(local_music)}→{len(dynamo_music)})"
        )

        if not dry_run:
            local_data["stories"]          = dynamo_stories
            local_data["musical_segments"] = dynamo_music
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(local_data, f, ensure_ascii=False, indent=2)

        updated += 1

    # ── 4b. Create files for DynamoDB records with NO local file ────────
    for vid, record in sorted(dynamo_items.items()):
        # Skip books
        if record.get("type") == "book":
            continue
        # Already has a local file
        if vid in local_video_ids:
            continue

        target = os.path.join(meta_dir, f"{vid}_meta.json")
        new_data = {
            "video_id":             vid,
            "title":                record.get("title", ""),
            "stories":              decimal_to_native(record.get("stories", [])),
            "musical_segments":     decimal_to_native(record.get("musical_segments", [])),
            "topics":               decimal_to_native(record.get("topics", [])),
            "queries":              decimal_to_native(record.get("queries", [])),
            "actionable_practices": decimal_to_native(record.get("actionable_practices", [])),
            "quoted_verses":        decimal_to_native(record.get("quoted_verses", [])),
        }

        logging.info(
            f"  ✨  {vid}: no local file found — CREATING from DynamoDB "
            f"(stories={len(new_data['stories'])}, music={len(new_data['musical_segments'])})."
        )

        if not dry_run:
            with open(target, "w", encoding="utf-8") as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)

        created += 1

    # ── 5. Summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print(f"  Sync complete {'(DRY RUN — no files written)' if dry_run else ''}  ")
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
    TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "sadhananandadeep-content")
    REGION     = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))

    sync_dynamo_to_meta(
        meta_dir   = META_DIR,
        table_name = TABLE_NAME,
        region     = REGION,
        dry_run    = False,   # set True to preview changes without writing files
    )
