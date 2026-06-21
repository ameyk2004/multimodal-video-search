import json
import os
import logging
import boto3
import decimal
import random
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

from models.response import StoryItem, StoriesResponse

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
        table_name = os.environ.get("DYNAMODB_TABLE", "sadhananandadeep-metadata")
        table = dynamodb.Table(table_name)
        
        from boto3.dynamodb.conditions import Key
        
        # Query GSI1 for all stories
        response = table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq('STORIES')
        )
        items = response.get('Items', [])
        
        while 'LastEvaluatedKey' in response:
            response = table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('GSI1PK').eq('STORIES'),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
        
        all_stories = []
        for item in items:
            video_id = item.get("video_id")
            story_title = item.get("title", "प्रवचन")
            story_title_english = item.get("title_english", "")
            moral = item.get("moral", "")
            
            # Extract saint name from PK or item
            saint = item.get("character_or_saint", item.get("normalized_saint_name", ""))
            if not saint and item.get("PK", "").startswith("SAINT#"):
                saint = item.get("PK").split("#", 1)[1]
            
            norm_saint = item.get("normalized_saint_name", saint)
            norm_saint_english = item.get("normalized_saint_name_english", "")
            assoc_topics = item.get("associated_topics", [])
            start_text = item.get("exact_start_text", "")
            
            # Handle possible float/decimal values safely
            raw_start = item.get("start_time_seconds", 0)
            start_time = int(raw_start) if raw_start else 0
                
            raw_end = item.get("end_time_seconds", 0)
            end_time = int(raw_end) if raw_end else 0

            all_stories.append(StoryItem(
                video_id=video_id,
                title=story_title,
                title_english=story_title_english,
                character_or_saint=saint,
                normalized_saint_name=norm_saint,
                normalized_saint_name_english=norm_saint_english,
                associated_topics=assoc_topics,
                moral=moral,
                exact_start_text=start_text,
                start_time_seconds=start_time,
                end_time_seconds=end_time,
                thumbnail_url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                youtube_url=f"https://www.youtube.com/watch?v={video_id}&t={start_time}s"
            ))
        # Shuffle the stories to provide a Discovery-style feed
        random.shuffle(all_stories)
        
        response_model = StoriesResponse(stories=all_stories)
        return _build_response(200, response_model)

    except Exception as exc:
        logger.error("Error fetching stories: %s", exc)
        return _build_response(500, {"error": "Failed to fetch stories from database."})
