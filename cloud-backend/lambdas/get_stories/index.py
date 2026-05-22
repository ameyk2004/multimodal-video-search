import json
import os
import logging
import boto3
import decimal
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            if obj % 1 > 0:
                return float(obj)
            else:
                return int(obj)
            return super(DecimalEncoder, self).default(obj)
        elif isinstance(obj, BaseModel):
            return obj.model_dump()
        return super(DecimalEncoder, self).default(obj)

class StoryModel(BaseModel):
    video_id: str
    title: str
    character_or_saint: Optional[str] = ""
    moral: Optional[str] = ""
    exact_start_text: Optional[str] = ""
    exact_end_text: Optional[str] = ""
    start_time_seconds: int = 0
    thumbnail_url: str
    youtube_url: str
    searchable_text: str

class StoriesResponse(BaseModel):
    stories: List[StoryModel]

def _build_response(status_code, body):
    # Ensure body is a dict before json.dumps
    if isinstance(body, BaseModel):
        body = body.model_dump()
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
        },
        "body": json.dumps(body, cls=DecimalEncoder)
    }

def lambda_handler(event, context):
    try:
        dynamodb = boto3.resource("dynamodb")
        table_name = os.environ.get("DYNAMODB_TABLE", "guru-video-metadata")
        table = dynamodb.Table(table_name)
        
        # Scan the table
        response = table.scan()
        items = response.get('Items', [])
        
        all_stories = []
        for item in items:
            video_id = item.get("video_id")
            stories = item.get("stories", [])
            for story in stories:
                title = story.get("title", "")
                moral = story.get("moral", "")
                saint = story.get("character_or_saint", "")
                start_text = story.get("exact_start_text", "")
                
                searchable_text = f"{title} {moral} {saint} {start_text}".lower()
                
                # Handle possible float/decimal values safely
                raw_start = story.get("start_time_seconds", 0)
                if isinstance(raw_start, decimal.Decimal):
                    start_time = int(raw_start)
                else:
                    start_time = int(raw_start) if raw_start else 0

                all_stories.append(StoryModel(
                    video_id=video_id,
                    title=title,
                    character_or_saint=saint,
                    moral=moral,
                    exact_start_text=start_text,
                    exact_end_text=story.get("exact_end_text", ""),
                    start_time_seconds=start_time,
                    thumbnail_url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                    youtube_url=f"https://www.youtube.com/watch?v={video_id}&t={start_time}s",
                    searchable_text=searchable_text
                ))
        
        response_model = StoriesResponse(stories=all_stories)
        return _build_response(200, response_model)

    except Exception as exc:
        logger.error("Error fetching stories: %s", exc)
        return _build_response(500, {"error": "Failed to fetch stories from database."})
