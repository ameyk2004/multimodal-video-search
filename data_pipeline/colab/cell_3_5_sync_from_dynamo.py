# ════════════════════════════════════════════════════════════════════════
# CELL 3.5 — Sync enriched_metadata JSON files FROM DynamoDB
#
# ▶  WHEN TO RUN:
#    After editing stories / musical-segment timestamps in the Admin Panel.
#    Run this BEFORE Cell 7 (DynamoDB upload) so you never overwrite correct
#    data with stale local data.
#
# ▶  DIRECTION:  DynamoDB  →  local enriched_metadata/*.json
# ▶  CASE 1 — local file EXISTS  : updates stories & musical_segments only
# ▶  CASE 2 — local file MISSING : creates a new <video_id>_meta.json
# ════════════════════════════════════════════════════════════════════════

import json, os, glob, decimal, logging
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ── Config ────────────────────────────────────────────────────────────
META_DIR   = '/content/repo/data_pipeline/videos/enriched_metadata'
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'sadhananandadeep-content')
REGION     = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
DRY_RUN    = False   # ← set True to preview changes without writing files

# ── Helper: Decimal → native Python ───────────────────────────────────
def to_native(obj):
    if isinstance(obj, list):            return [to_native(v) for v in obj]
    if isinstance(obj, dict):            return {k: to_native(v) for k, v in obj.items()}
    if isinstance(obj, decimal.Decimal): return int(obj) if obj % 1 == 0 else float(obj)
    return obj

# ── 1. Verify table ───────────────────────────────────────────────────
client   = boto3.client('dynamodb', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
try:
    client.describe_table(TableName=TABLE_NAME)
    print(f'✅  Connected to DynamoDB table: {TABLE_NAME}')
except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceNotFoundException':
        raise ValueError(
            f'❌  Table "{TABLE_NAME}" not found in region "{REGION}".\n'
            'Check your AWS credentials and the DYNAMODB_TABLE env var.'
        )
    raise

# ── 2. Scan DynamoDB (paginated, all relevant fields) ─────────────────
print('⬇️  Scanning DynamoDB table...')
table        = dynamodb.Table(TABLE_NAME)
dynamo_items = {}

resp = table.scan(
    ProjectionExpression=(
        'video_id, #t, title, stories, musical_segments, '
        'topics, queries, actionable_practices, quoted_verses'
    ),
    ExpressionAttributeNames={'#t': 'type'}
)
for item in resp.get('Items', []):
    if item.get('video_id'):
        dynamo_items[item['video_id']] = item

while 'LastEvaluatedKey' in resp:
    resp = table.scan(
        ProjectionExpression=(
            'video_id, #t, title, stories, musical_segments, '
            'topics, queries, actionable_practices, quoted_verses'
        ),
        ExpressionAttributeNames={'#t': 'type'},
        ExclusiveStartKey=resp['LastEvaluatedKey']
    )
    for item in resp.get('Items', []):
        if item.get('video_id'):
            dynamo_items[item['video_id']] = item

print(f'   Loaded {len(dynamo_items)} records from DynamoDB.')

# ── 3. Build set of existing local video IDs ──────────────────────────
meta_files = sorted(glob.glob(os.path.join(META_DIR, '*_meta.json')))
print(f'📂  Found {len(meta_files)} local meta files in {META_DIR}')

local_ids = {
    os.path.splitext(os.path.basename(fp))[0].replace('_meta', '')
    for fp in meta_files
}

updated, skipped, not_in_dynamo, created = 0, 0, 0, 0

# ── 4a. Update existing local files ───────────────────────────────────
for filepath in meta_files:
    video_id = os.path.splitext(os.path.basename(filepath))[0].replace('_meta', '')

    if video_id not in dynamo_items:
        print(f'  ⚠️  {video_id}: no DynamoDB record — skipping.')
        not_in_dynamo += 1
        continue

    rec        = dynamo_items[video_id]
    db_stories = to_native(rec.get('stories', []))
    db_music   = to_native(rec.get('musical_segments', []))

    with open(filepath, 'r', encoding='utf-8') as f:
        local = json.load(f)

    # Deep-compare to avoid false positives from float precision
    changed = (
        json.dumps(db_stories, ensure_ascii=False, sort_keys=True) !=
        json.dumps(local.get('stories', []), ensure_ascii=False, sort_keys=True)
    ) or (
        json.dumps(db_music, ensure_ascii=False, sort_keys=True) !=
        json.dumps(local.get('musical_segments', []), ensure_ascii=False, sort_keys=True)
    )

    if not changed:
        skipped += 1
        continue

    print(
        f'  ↻  {video_id}: stories '
        f'{len(local.get("stories",[]))}→{len(db_stories)},  '
        f'music {len(local.get("musical_segments",[]))}→{len(db_music)}'
    )

    if not DRY_RUN:
        local['stories']          = db_stories
        local['musical_segments'] = db_music
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(local, f, ensure_ascii=False, indent=2)

    updated += 1

# ── 4b. Create files for DynamoDB records with NO local file ──────────
for vid, record in sorted(dynamo_items.items()):
    if record.get('type') == 'book':   # skip books
        continue
    if vid in local_ids:               # already has a local file
        continue

    target = os.path.join(META_DIR, f'{vid}_meta.json')
    new_data = {
        'video_id':             vid,
        'title':                record.get('title', ''),
        'stories':              to_native(record.get('stories', [])),
        'musical_segments':     to_native(record.get('musical_segments', [])),
        'topics':               to_native(record.get('topics', [])),
        'queries':              to_native(record.get('queries', [])),
        'actionable_practices': to_native(record.get('actionable_practices', [])),
        'quoted_verses':        to_native(record.get('quoted_verses', [])),
    }

    print(
        f'  ✨  {vid}: no local file found — CREATING from DynamoDB '
        f'(stories={len(new_data["stories"])}, music={len(new_data["musical_segments"])})'
    )

    if not DRY_RUN:
        with open(target, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)

    created += 1

# ── 5. Summary ────────────────────────────────────────────────────────
label = '(DRY RUN — no files written)' if DRY_RUN else ''
print()
print('=' * 55)
print(f'  SYNC COMPLETE  {label}')
print('=' * 55)
print(f'  Files updated      : {updated}')
print(f'  Already in sync    : {skipped}')
print(f'  Not in DynamoDB    : {not_in_dynamo}')
print(f'  New files created  : {created}')
print('=' * 55)
if not DRY_RUN and (updated > 0 or created > 0):
    print('\n✅  Local meta files now match DynamoDB.')
    print('   Commit these changes to Git so future pipelines start clean.')
