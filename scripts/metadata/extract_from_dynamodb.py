"""
DynamoDB Extractor Script.
Reverse of dynamo_uploader.py — pulls all items from the NEW DynamoDB
single-table (sadhananandadeep-metadata) and writes them back to
data_pipeline/videos/enriched_metadata/ as <video_id>_meta.json files.

Access patterns:
  • GSI1 (GSI1PK = "VIDEOS") → discover all video records & their top-level metadata
  • GSI2 (video_id = <id>)   → fetch STORY# and MUSIC# items per video

To run:
    source venv/bin/activate
    python scripts/metadata/extract_from_dynamodb.py
"""
import os
import json
import decimal
import boto3
import logging
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

TABLE_NAME   = os.environ.get("DYNAMODB_TABLE", "sadhananandadeep-metadata")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR   = os.path.join(PROJECT_ROOT, "data_pipeline", "videos", "enriched_metadata")


class DecimalConverter(json.JSONEncoder):
    """Converts DynamoDB Decimal types back to plain Python floats/ints for JSON serialisation."""
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj) if obj % 1 else int(obj)
        return super().default(obj)


def decimal_to_native(obj):
    if isinstance(obj, decimal.Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: decimal_to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [decimal_to_native(v) for v in obj]
    return obj


def fetch_all_pages(query_fn, **kwargs) -> list:
    resp  = query_fn(**kwargs)
    items = list(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = query_fn(ExclusiveStartKey=resp["LastEvaluatedKey"], **kwargs)
        items.extend(resp.get("Items", []))
    return items


def main():
    region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))
    print(f"Connecting to DynamoDB table '{TABLE_NAME}' in region '{region}'...")

    dynamodb = boto3.resource("dynamodb", region_name=region)
    client   = boto3.client("dynamodb", region_name=region)

    # Verify the table exists
    try:
        client.describe_table(TableName=TABLE_NAME)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"❌ DynamoDB table '{TABLE_NAME}' not found. "
                  "Deploy the cloud-backend stack first.")
        else:
            print(f"❌ AWS error: {e}")
        return

    table = dynamodb.Table(TABLE_NAME)

    # ── 1. Fetch all videos via GSI1 ──────────────────────────────────────────
    print(f"Querying GSI1 (VIDEOS) from '{TABLE_NAME}'...")

    def _query_videos(**kw):
        return table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq("VIDEOS"),
            **kw,
        )

    video_items = fetch_all_pages(_query_videos)
    print(f"\n📊 Found {len(video_items)} video records in DynamoDB.\n")

    if not video_items:
        print("Nothing to extract. Exiting.")
        return

    # ── 2. Fetch stories & music per video via GSI2 ───────────────────────────
    print("Fetching stories & music segments per video via GSI2...")
    dynamo_stories: dict = {}
    dynamo_music:   dict = {}

    for vi in video_items:
        vid = vi.get("video_id")
        if not vid:
            continue

        def _query_gsi2(vid=vid, **kw):
            return table.query(
                IndexName="GSI2",
                KeyConditionExpression=Key("video_id").eq(vid),
                **kw,
            )

        children = fetch_all_pages(_query_gsi2)
        dynamo_stories[vid] = [
            {k: decimal_to_native(v) for k, v in i.items()}
            for i in children if i.get("SK", "").startswith("STORY#")
        ]
        dynamo_music[vid] = [
            {k: decimal_to_native(v) for k, v in i.items()}
            for i in children if i.get("SK", "").startswith("MUSIC#")
        ]

    # ── Overwrite flag ────────────────────────────────────────────────────────
    try:
        overwrite_input = input(
            "Do you want to OVERWRITE existing local meta files? (y/n) [n]: "
        ).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return

    overwrite = overwrite_input in ("y", "yes")
    if overwrite:
        print("⚠️  Overwrite mode ON — existing files will be replaced.\n")
    else:
        print("ℹ️  Skip mode ON — existing files will be left untouched.\n")

    # ── Extract ───────────────────────────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    saved   = 0
    skipped = 0
    errors  = 0

    for item in video_items:
        video_id = item.get("video_id")
        if not video_id:
            logging.warning("Item has no video_id — skipping: %s", item)
            errors += 1
            continue

        out_path = os.path.join(OUTPUT_DIR, f"{video_id}_meta.json")

        if os.path.exists(out_path) and not overwrite:
            print(f"  ⏩ SKIPPED  (exists): {video_id}_meta.json")
            skipped += 1
            continue

        # Reconstruct the flat format expected by the local pipeline
        native_item = decimal_to_native(dict(item))
        native_item["stories"]          = dynamo_stories.get(video_id, [])
        native_item["musical_segments"] = dynamo_music.get(video_id, [])

        # Strip internal DynamoDB keys from the output
        for internal_key in ("PK", "SK", "GSI1PK", "GSI1SK"):
            native_item.pop(internal_key, None)

        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(native_item, f, ensure_ascii=False, indent=2)

            action = "OVERWRITTEN" if os.path.exists(out_path) and overwrite else "SAVED"
            print(f"  ✅ {action}: {video_id}_meta.json  "
                  f"(stories={len(native_item['stories'])}, "
                  f"music={len(native_item['musical_segments'])})")
            saved += 1

        except Exception as e:
            logging.error("Failed to write %s: %s", out_path, e)
            errors += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("📥 EXTRACTION SUMMARY")
    print("=" * 50)
    print(f"Total items in DynamoDB:   {len(video_items)}")
    print(f"Files saved / overwritten: {saved}")
    print(f"Files skipped (existing):  {skipped}")
    print(f"Errors:                    {errors}")
    print("=" * 50)
    print(f"\n✅ Done! Files written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
