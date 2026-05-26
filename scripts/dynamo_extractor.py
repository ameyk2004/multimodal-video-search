"""
DynamoDB Extractor Script.
Reverse of dynamo_uploader.py — pulls all items from the DynamoDB content table
and writes them back to data_pipeline/enriched_metadata/ as <video_id>_meta.json files.

To run:
    source venv/bin/activate
    python scripts/dynamo_extractor.py
"""
import os
import json
import decimal
import boto3
import logging
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

TABLE_NAME  = os.environ.get("DYNAMODB_TABLE", "sadhananandadeep-content")
OUTPUT_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "data_pipeline", "enriched_metadata")


class DecimalConverter(json.JSONEncoder):
    """Converts DynamoDB Decimal types back to plain Python floats/ints for JSON serialisation."""
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj) if obj % 1 else int(obj)
        return super().default(obj)


def scan_table(table) -> list[dict]:
    """Full table scan with automatic pagination."""
    items = []
    response = table.scan()
    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    return items


def main():
    region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))
    print(f"Connecting to DynamoDB in region '{region}'...")

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

    print(f"Scanning DynamoDB table '{TABLE_NAME}'...")
    items = scan_table(table)
    print(f"\n📊 Scan Results: {len(items)} total items found in DynamoDB.\n")

    if not items:
        print("Nothing to extract. Exiting.")
        return

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

    for item in items:
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

        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(dict(item), f, ensure_ascii=False, indent=2, cls=DecimalConverter)

            action = "OVERWRITTEN" if os.path.exists(out_path) and overwrite else "SAVED"
            print(f"  ✅ {action}: {video_id}_meta.json")
            saved += 1

        except Exception as e:
            logging.error("Failed to write %s: %s", out_path, e)
            errors += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("📥 EXTRACTION SUMMARY")
    print("=" * 50)
    print(f"Total items in DynamoDB:   {len(items)}")
    print(f"Files saved / overwritten: {saved}")
    print(f"Files skipped (existing):  {skipped}")
    print(f"Errors:                    {errors}")
    print("=" * 50)
    print(f"\n✅ Done! Files written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
