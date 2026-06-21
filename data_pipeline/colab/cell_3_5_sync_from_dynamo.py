# ════════════════════════════════════════════════════════════════════════
# CELL 3.5 — Sync enriched_metadata JSON files FROM DynamoDB (NEW SCHEMA)
#
# ▶  WHEN TO RUN:
#    After editing stories / musical-segment timestamps in the Admin Panel.
#    Run this BEFORE Cell 7 (DynamoDB upload) so you never overwrite correct
#    data with stale local data.
#
# ▶  TABLE:      sadhananandadeep-metadata   (new single-table design)
# ▶  DIRECTION:  DynamoDB  →  local enriched_metadata/*.json
#
# ▶  CASE 1 — local file EXISTS  : updates stories & musical_segments only
# ▶  CASE 2 — local file MISSING : creates a new <video_id>_meta.json
#
# ▶  ACCESS PATTERNS:
#    • GSI1 (GSI1PK = "VIDEOS") → discover all video_ids & top-level metadata
#    • GSI2 (video_id = <id>)   → fetch STORY# and MUSIC# items per video
# ════════════════════════════════════════════════════════════════════════

import json, os, glob, decimal, logging
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ── Config ────────────────────────────────────────────────────────────
META_DIR   = '/content/repo/data_pipeline/videos/enriched_metadata'
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'sadhananandadeep-metadata')
REGION     = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
DRY_RUN    = False   # ← set True to preview changes without writing files

# ── Helper: Decimal → native Python ───────────────────────────────────
def to_native(obj):
    if isinstance(obj, list):            return [to_native(v) for v in obj]
    if isinstance(obj, dict):            return {k: to_native(v) for k, v in obj.items()}
    if isinstance(obj, decimal.Decimal): return int(obj) if obj % 1 == 0 else float(obj)
    return obj

def _fetch_all_pages(query_fn, **kwargs) -> list:
    """Run a paginated DynamoDB query and collect all items."""
    resp  = query_fn(**kwargs)
    items = list(resp.get('Items', []))
    while 'LastEvaluatedKey' in resp:
        resp = query_fn(ExclusiveStartKey=resp['LastEvaluatedKey'], **kwargs)
        items.extend(resp.get('Items', []))
    return items

def _story_to_dict(item: dict) -> dict:
    return {
        'title':                         item.get('title', ''),
        'title_english':                 item.get('title_english', ''),
        'moral':                         item.get('moral', ''),
        'character_or_saint':            item.get('character_or_saint', ''),
        'normalized_saint_name':         item.get('normalized_saint_name', ''),
        'normalized_saint_name_english': item.get('normalized_saint_name_english', ''),
        'associated_topics':             to_native(item.get('associated_topics', [])),
        'exact_start_text':              item.get('exact_start_text', ''),
        'start_time_seconds':            to_native(item.get('start_time_seconds', 0)),
        'end_time_seconds':              to_native(item.get('end_time_seconds', 0)),
    }

def _music_to_dict(item: dict) -> dict:
    return {
        'name':               item.get('name', ''),
        'name_english':       item.get('name_english', ''),
        'type':               item.get('type', ''),
        'saint':              item.get('saint', ''),
        'saint_english':      item.get('saint_english', ''),
        'exact_start_text':   item.get('exact_start_text', ''),
        'start_time_seconds': to_native(item.get('start_time_seconds', 0)),
        'end_time_seconds':   to_native(item.get('end_time_seconds', 0)),
    }

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

table = dynamodb.Table(TABLE_NAME)

# ── 2. Discover all videos via GSI1 ──────────────────────────────────
print('⬇️  Querying GSI1 (VIDEOS) from DynamoDB…')

def _gsi1_query(**kwargs):
    return table.query(
        IndexName='GSI1',
        KeyConditionExpression=Key('GSI1PK').eq('VIDEOS'),
        **kwargs
    )

video_items = _fetch_all_pages(_gsi1_query)
print(f'   Found {len(video_items)} video records.')

dynamo_videos = {}
for item in video_items:
    vid = item.get('video_id')
    if vid:
        dynamo_videos[vid] = to_native(item)

# ── 3. Fetch STORY# and MUSIC# for each video via GSI2 ───────────────
print('⬇️  Fetching stories & music per video via GSI2…')
dynamo_stories = {}
dynamo_music   = {}

for vid in dynamo_videos:
    def _gsi2_query(vid=vid, **kwargs):
        return table.query(
            IndexName='GSI2',
            KeyConditionExpression=Key('video_id').eq(vid),
            **kwargs
        )
    children = _fetch_all_pages(_gsi2_query)
    dynamo_stories[vid] = [_story_to_dict(i) for i in children if i.get('SK','').startswith('STORY#')]
    dynamo_music[vid]   = [_music_to_dict(i) for i in children if i.get('SK','').startswith('MUSIC#')]

print(f'   Loaded stories/music for {len(dynamo_videos)} videos.')

# ── 4. Build set of existing local video IDs ──────────────────────────
meta_files = sorted(glob.glob(os.path.join(META_DIR, '*_meta.json')))
print(f'📂  Found {len(meta_files)} local meta files in {META_DIR}')

local_ids = {
    os.path.splitext(os.path.basename(fp))[0].replace('_meta', '')
    for fp in meta_files
}

updated, skipped, not_in_dynamo, created = 0, 0, 0, 0

# ── 5a. Update existing local files ───────────────────────────────────
for filepath in meta_files:
    video_id = os.path.splitext(os.path.basename(filepath))[0].replace('_meta', '')

    if video_id not in dynamo_videos:
        print(f'  ⚠️  {video_id}: no DynamoDB record — skipping.')
        not_in_dynamo += 1
        continue

    db_stories = dynamo_stories.get(video_id, [])
    db_music   = dynamo_music.get(video_id, [])

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

# ── 5b. Create files for DynamoDB records with NO local file ──────────
for vid, record in sorted(dynamo_videos.items()):
    if vid in local_ids:
        continue

    target   = os.path.join(META_DIR, f'{vid}_meta.json')
    new_data = {
        'video_id':             vid,
        'title':                record.get('title', ''),
        'stories':              dynamo_stories.get(vid, []),
        'musical_segments':     dynamo_music.get(vid, []),
        'topics':               record.get('topics', []),
        'queries':              record.get('queries', []),
        'actionable_practices': record.get('actionable_practices', []),
        'quoted_verses':        record.get('quoted_verses', []),
    }

    print(
        f'  ✨  {vid}: no local file found — CREATING from DynamoDB '
        f'(stories={len(new_data["stories"])}, music={len(new_data["musical_segments"])})'
    )

    if not DRY_RUN:
        with open(target, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)

    created += 1

# ── 6. Summary ────────────────────────────────────────────────────────
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
