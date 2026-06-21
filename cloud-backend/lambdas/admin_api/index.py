"""
Admin API Lambda — uses the new sadhananandadeep-metadata single-table design.

Endpoints:
  GET  /admin/videos               — list all videos with their stories & music
  GET  /admin/videos/{videoId}     — full metadata for one video
  PUT  /admin/videos/{videoId}     — replace stories and/or musical_segments

Schema:
  VIDEO#{id} / METADATA            — video-level fields (topics, queries, …)
  SAINT#{nm} / STORY#{uuid}        — individual story (GSI2 key: video_id)
  SAINT#{nm} / MUSIC#{uuid}        — individual music segment (GSI2 key: video_id)

Idempotency on PUT:
  1. Query GSI2 for all existing STORY# and MUSIC# items for the video.
  2. Batch-delete them.
  3. Batch-insert the new items from the request body using deterministic UUIDs.
"""

import json
import os
import uuid
import decimal
import logging
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from pydantic import BaseModel

logger = logging.getLogger()
logger.setLevel(logging.INFO)

NEW_TABLE_NAME = "sadhananandadeep-metadata"


# ─── Decimal encoder ─────────────────────────────────────────────────────────

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj) if obj % 1 > 0 else int(obj)
        elif isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)


# ─── Response builder ─────────────────────────────────────────────────────────

def _build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, PUT, OPTIONS",
        },
        "body": json.dumps(body, cls=DecimalEncoder),
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _to_decimal(obj):
    """Recursively convert float → Decimal for DynamoDB storage."""
    if isinstance(obj, float):
        return decimal.Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_decimal(v) for v in obj]
    return obj


def _from_decimal(obj):
    """Recursively convert Decimal → int/float for JSON responses."""
    if isinstance(obj, decimal.Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: _from_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_from_decimal(v) for v in obj]
    return obj


def _deterministic_id(video_id: str, discriminator: str) -> str:
    """Stable UUID from (video_id, discriminator) — idempotent across PUT calls."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{video_id}:{discriminator}"))


def _fetch_all_pages(query_fn, **kwargs) -> list:
    resp  = query_fn(**kwargs)
    items = list(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = query_fn(ExclusiveStartKey=resp["LastEvaluatedKey"], **kwargs)
        items.extend(resp.get("Items", []))
    return items


def _get_stories_and_music(table, video_id: str):
    """Return (stories_list, music_list) from DynamoDB for a given video_id via GSI2."""
    def _query(**kwargs):
        return table.query(
            IndexName="GSI2",
            KeyConditionExpression=Key("video_id").eq(video_id),
            **kwargs,
        )

    children = _fetch_all_pages(_query)

    stories = []
    music   = []
    for item in children:
        sk = item.get("SK", "")
        native = _from_decimal(item)
        if sk.startswith("STORY#"):
            stories.append({
                "title":                         native.get("title", ""),
                "title_english":                 native.get("title_english", ""),
                "moral":                         native.get("moral", ""),
                "character_or_saint":            native.get("character_or_saint", ""),
                "normalized_saint_name":         native.get("normalized_saint_name", ""),
                "normalized_saint_name_english": native.get("normalized_saint_name_english", ""),
                "associated_topics":             native.get("associated_topics", []),
                "exact_start_text":              native.get("exact_start_text", ""),
                "start_time_seconds":            native.get("start_time_seconds", 0),
                "end_time_seconds":              native.get("end_time_seconds", 0),
            })
        elif sk.startswith("MUSIC#"):
            music.append({
                "name":               native.get("name", ""),
                "name_english":       native.get("name_english", ""),
                "type":               native.get("type", ""),
                "saint":              native.get("saint", ""),
                "saint_english":      native.get("saint_english", ""),
                "exact_start_text":   native.get("exact_start_text", ""),
                "start_time_seconds": native.get("start_time_seconds", 0),
                "end_time_seconds":   native.get("end_time_seconds", 0),
            })

    return stories, music


def _delete_children(table, video_id: str):
    """
    Delete ALL STORY# and MUSIC# items linked to video_id (via GSI2).
    We must fetch their PK+SK first because those are the real primary keys.
    """
    def _query(**kwargs):
        return table.query(
            IndexName="GSI2",
            KeyConditionExpression=Key("video_id").eq(video_id),
            ProjectionExpression="PK, SK",
            **kwargs,
        )

    children = _fetch_all_pages(_query)
    if not children:
        return

    with table.batch_writer() as batch:
        for item in children:
            sk = item.get("SK", "")
            if sk.startswith("STORY#") or sk.startswith("MUSIC#"):
                batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})


def _ensure_saint(table, saint_name: str, seen: set):
    """Write a placeholder saint profile if one doesn't already exist."""
    if saint_name in seen:
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
            ConditionExpression="attribute_not_exists(PK)",
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
    finally:
        seen.add(saint_name)


# ─── Lambda handler ───────────────────────────────────────────────────────────

def lambda_handler(event, context):
    try:
        path        = event.get("path", "")
        http_method = event.get("httpMethod", "")

        if http_method == "OPTIONS":
            return _build_response(200, {})

        dynamodb   = boto3.resource("dynamodb")
        table_name = os.environ.get("DYNAMODB_TABLE", NEW_TABLE_NAME)
        table      = dynamodb.Table(table_name)

        path_parameters = event.get("pathParameters") or {}
        video_id        = path_parameters.get("videoId")

        # ── GET /admin/videos ─────────────────────────────────────────────────
        if path == "/admin/videos" and http_method == "GET":
            def _query_videos(**kwargs):
                return table.query(
                    IndexName="GSI1",
                    KeyConditionExpression=Key("GSI1PK").eq("VIDEOS"),
                    **kwargs,
                )

            video_items = _fetch_all_pages(_query_videos)

            videos = []
            for item in video_items:
                vid     = item.get("video_id", item.get("PK", "").split("#", 1)[-1])
                stories, music = _get_stories_and_music(table, vid)
                videos.append({
                    "video_id":         vid,
                    "title":            _from_decimal(item.get("title", "अज्ञात")),
                    "stories":          stories,
                    "musical_segments": music,
                })

            return _build_response(200, {"videos": videos})

        # ── GET /admin/videos/{videoId} ────────────────────────────────────────
        elif video_id and http_method == "GET":
            resp = table.get_item(Key={"PK": f"VIDEO#{video_id}", "SK": "METADATA"})
            item = resp.get("Item")
            if not item:
                return _build_response(404, {"error": "Video not found"})

            stories, music = _get_stories_and_music(table, video_id)
            payload        = _from_decimal(item)
            payload["stories"]          = stories
            payload["musical_segments"] = music
            return _build_response(200, payload)

        # ── PUT /admin/videos/{videoId} ────────────────────────────────────────
        elif video_id and http_method == "PUT":
            body = json.loads(event.get("body", "{}"))

            if "stories" not in body and "musical_segments" not in body:
                return _build_response(400, {"error": "No valid fields to update (stories or musical_segments required)"})

            # 1. Delete all existing STORY# / MUSIC# children for this video
            _delete_children(table, video_id)

            seen_saints: set = set()

            # 2. Insert new stories
            if "stories" in body:
                with table.batch_writer() as batch:
                    for story in body.get("stories", []):
                        saint_name = (
                            story.get("normalized_saint_name")
                            or story.get("character_or_saint")
                            or "Unknown Saint"
                        )
                        start    = story.get("start_time_seconds", 0)
                        story_id = _deterministic_id(video_id, str(start))

                        _ensure_saint(table, saint_name, seen_saints)

                        batch.put_item(Item={
                            "PK":     f"SAINT#{saint_name}",
                            "SK":     f"STORY#{story_id}",
                            "GSI1PK": "STORIES",
                            "GSI1SK": str(start),
                            "video_id":                    video_id,
                            "story_id":                    story_id,
                            "title":                       story.get("title", "प्रवचन"),
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

            # 3. Insert new musical segments
            if "musical_segments" in body:
                with table.batch_writer() as batch:
                    for music in body.get("musical_segments", []):
                        saint_name = music.get("saint") or "Unknown Saint"
                        start      = music.get("start_time_seconds", 0)
                        music_id   = _deterministic_id(video_id, f"music_{start}")

                        _ensure_saint(table, saint_name, seen_saints)

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

            return _build_response(200, {"message": "Update successful"})

        return _build_response(404, {"error": "Route not found"})

    except Exception as exc:
        logger.error("Error in admin API: %s", exc, exc_info=True)
        return _build_response(500, {"error": "Failed to process request."})
