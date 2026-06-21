# ════════════════════════════════════════════════════════════════════════
# EMERGENCY FIX — Deduplicate DynamoDB + Local Files
#
# RUN THIS NOW in Colab before doing anything else.
#
# What happened:
#   Cell 3.5 (sync) saw 3x duplicate STORY#/MUSIC# items in DynamoDB
#   (caused by old migration + multiple uploader runs with different saint names)
#   and faithfully wrote all 3 copies to each local _meta.json.
#
# This script:
#   1. Deduplicates local _meta.json files (keeps best story per start_time)
#   2. Deletes ALL duplicate STORY#/MUSIC# items from DynamoDB
#   3. Re-uploads from the clean local files
#
# ════════════════════════════════════════════════════════════════════════

import json, os, glob, decimal, uuid, logging
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

META_DIR   = '/content/repo/data_pipeline/videos/enriched_metadata'
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'sadhananandadeep-metadata')
REGION     = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table    = dynamodb.Table(TABLE_NAME)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def to_native(obj):
    if isinstance(obj, list):            return [to_native(v) for v in obj]
    if isinstance(obj, dict):            return {k: to_native(v) for k, v in obj.items()}
    if isinstance(obj, decimal.Decimal): return int(obj) if obj % 1 == 0 else float(obj)
    return obj

def to_decimal(obj):
    if isinstance(obj, float):  return decimal.Decimal(str(obj))
    if isinstance(obj, dict):   return {k: to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):   return [to_decimal(v) for v in obj]
    return obj

def det_id(video_id, discriminator):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{video_id}:{discriminator}"))

def fetch_all(query_fn, **kwargs):
    resp  = query_fn(**kwargs)
    items = list(resp.get('Items', []))
    while 'LastEvaluatedKey' in resp:
        resp = query_fn(ExclusiveStartKey=resp['LastEvaluatedKey'], **kwargs)
        items.extend(resp.get('Items', []))
    return items


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 1 — Fix local _meta.json files (deduplicate by start_time_seconds)
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("PHASE 1: Deduplicating local _meta.json files")
print("="*60)

files = sorted(glob.glob(os.path.join(META_DIR, '*_meta.json')))
print(f"Found {len(files)} local files.")

total_story_dupes  = 0
total_music_dupes  = 0
files_fixed        = 0

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    video_id = data.get('video_id', os.path.basename(filepath).replace('_meta.json',''))

    # Deduplicate stories by start_time_seconds — keep the one with the most data
    stories     = data.get('stories', [])
    seen_starts = {}
    for s in stories:
        start = s.get('start_time_seconds', 0)
        if start not in seen_starts:
            seen_starts[start] = s
        else:
            # Keep whichever has more fields filled in
            existing = seen_starts[start]
            if len([v for v in s.values() if v]) > len([v for v in existing.values() if v]):
                seen_starts[start] = s
    deduped_stories = list(seen_starts.values())
    story_dupes     = len(stories) - len(deduped_stories)

    # Deduplicate musical_segments by start_time_seconds
    music       = data.get('musical_segments', [])
    seen_music  = {}
    for m in music:
        start = m.get('start_time_seconds', 0)
        if start not in seen_music:
            seen_music[start] = m
        else:
            existing = seen_music[start]
            if len([v for v in m.values() if v]) > len([v for v in existing.values() if v]):
                seen_music[start] = m
    deduped_music = list(seen_music.values())
    music_dupes   = len(music) - len(deduped_music)

    if story_dupes > 0 or music_dupes > 0:
        data['stories']          = deduped_stories
        data['musical_segments'] = deduped_music
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  ✅ {video_id}: stories {len(stories)}→{len(deduped_stories)}, music {len(music)}→{len(deduped_music)}")
        total_story_dupes += story_dupes
        total_music_dupes += music_dupes
        files_fixed += 1

print(f"\nPhase 1 complete: fixed {files_fixed} files, removed {total_story_dupes} story dupes, {total_music_dupes} music dupes.")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Delete ALL STORY# and MUSIC# items from DynamoDB
#           (nuclear clean: we re-upload clean data in Phase 3)
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("PHASE 2: Deleting all STORY# and MUSIC# items from DynamoDB")
print("="*60)

# Collect all STORY# items
print("  Querying GSI1 STORIES...")
story_items = fetch_all(lambda **kw: table.query(
    IndexName='GSI1',
    KeyConditionExpression=Key('GSI1PK').eq('STORIES'),
    ProjectionExpression='PK, SK',
    **kw
))

# Collect all MUSIC# items
print("  Querying GSI1 MUSIC...")
music_items = fetch_all(lambda **kw: table.query(
    IndexName='GSI1',
    KeyConditionExpression=Key('GSI1PK').eq('MUSIC'),
    ProjectionExpression='PK, SK',
    **kw
))

all_children = story_items + music_items
print(f"  Found {len(story_items)} STORY# items and {len(music_items)} MUSIC# items.")
print(f"  Total items to delete: {len(all_children)}")

if all_children:
    with table.batch_writer() as batch:
        for item in all_children:
            batch.delete_item(Key={'PK': item['PK'], 'SK': item['SK']})
    print(f"  ✅ Deleted {len(all_children)} items from DynamoDB.")
else:
    print("  Nothing to delete.")


# ═════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Re-upload from clean local files
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("PHASE 3: Re-uploading clean data to DynamoDB")
print("="*60)

files = sorted(glob.glob(os.path.join(META_DIR, '*_meta.json')))
processed_saints = set()
stats = {'videos': 0, 'stories': 0, 'music': 0, 'saints': 0}

with table.batch_writer() as batch:
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f, parse_float=decimal.Decimal)

        video_id  = data.get('video_id', os.path.basename(filepath).replace('_meta.json',''))
        is_book   = data.get('type') == 'book'
        pk_prefix = 'BOOK' if is_book else 'VIDEO'

        # Upsert VIDEO/BOOK METADATA
        video_record = {
            'PK': f'{pk_prefix}#{video_id}', 'SK': 'METADATA',
            'GSI1PK': 'BOOKS' if is_book else 'VIDEOS',
            'GSI1SK': str(data.get('created_at', '0')),
            'video_id': video_id,
        }
        skip_keys = {'stories', 'musical_segments', 'stories_found'}
        for k, v in data.items():
            if k not in skip_keys:
                video_record[k] = to_decimal(v)
        batch.put_item(Item=video_record)
        stats['videos'] += 1

        if is_book:
            continue

        # Insert Stories
        for story in data.get('stories', []):
            saint_name = (story.get('normalized_saint_name') or
                          story.get('character_or_saint') or 'Unknown Saint')
            start    = story.get('start_time_seconds', 0)
            story_id = det_id(video_id, str(start))

            if saint_name not in processed_saints:
                try:
                    table.put_item(
                        Item={
                            'PK': f'SAINT#{saint_name}', 'SK': 'METADATA',
                            'GSI1PK': 'SAINTS', 'GSI1SK': saint_name,
                            'name': saint_name, 'quote': 'Tap to explore teachings.',
                            'tradition': 'Various', 'era': 'Unknown Era',
                            'learnings': [], 'fullBio': '', 'imageUrl': ''
                        },
                        ConditionExpression='attribute_not_exists(PK)'
                    )
                    stats['saints'] += 1
                except ClientError as e:
                    if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
                        raise
                processed_saints.add(saint_name)

            batch.put_item(Item={
                'PK': f'SAINT#{saint_name}', 'SK': f'STORY#{story_id}',
                'GSI1PK': 'STORIES', 'GSI1SK': str(start),
                'video_id': video_id, 'story_id': story_id,
                'title':                       story.get('title', data.get('title', 'प्रवचन')),
                'title_english':               story.get('title_english', ''),
                'moral':                       story.get('moral', ''),
                'character_or_saint':          story.get('character_or_saint', saint_name),
                'normalized_saint_name':       saint_name,
                'normalized_saint_name_english': story.get('normalized_saint_name_english', ''),
                'associated_topics':           story.get('associated_topics', []),
                'exact_start_text':            story.get('exact_start_text', ''),
                'start_time_seconds':          to_decimal(start),
                'end_time_seconds':            to_decimal(story.get('end_time_seconds', 0)),
            })
            stats['stories'] += 1

        # Insert Musical Segments
        for music in data.get('musical_segments', []):
            saint_name = music.get('saint') or 'Unknown Saint'
            start      = music.get('start_time_seconds', 0)
            music_id   = det_id(video_id, f'music_{start}')

            if saint_name not in processed_saints:
                try:
                    table.put_item(
                        Item={
                            'PK': f'SAINT#{saint_name}', 'SK': 'METADATA',
                            'GSI1PK': 'SAINTS', 'GSI1SK': saint_name,
                            'name': saint_name, 'quote': 'Tap to explore teachings.',
                            'tradition': 'Various', 'era': 'Unknown Era',
                            'learnings': [], 'fullBio': '', 'imageUrl': ''
                        },
                        ConditionExpression='attribute_not_exists(PK)'
                    )
                    stats['saints'] += 1
                except ClientError as e:
                    if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
                        raise
                processed_saints.add(saint_name)

            batch.put_item(Item={
                'PK': f'SAINT#{saint_name}', 'SK': f'MUSIC#{music_id}',
                'GSI1PK': 'MUSIC', 'GSI1SK': str(start),
                'video_id': video_id, 'music_id': music_id,
                'name':               music.get('name', 'Unknown Bhajan'),
                'name_english':       music.get('name_english', ''),
                'type':               music.get('type', 'Abhang'),
                'saint':              saint_name,
                'saint_english':      music.get('saint_english', ''),
                'exact_start_text':   music.get('exact_start_text', ''),
                'start_time_seconds': to_decimal(start),
                'end_time_seconds':   to_decimal(music.get('end_time_seconds', 0)),
            })
            stats['music'] += 1

print("\n" + "="*60)
print("  EMERGENCY FIX COMPLETE")
print("="*60)
print(f"  Videos/Books uploaded : {stats['videos']}")
print(f"  Stories uploaded      : {stats['stories']}")
print(f"  Music segments        : {stats['music']}")
print(f"  Saint profiles        : {stats['saints']} (new placeholders only)")
print("="*60)
print("\n✅ DynamoDB is clean. Run Cell 3.5 again to verify — counts should now be 1:1 with local files.")
