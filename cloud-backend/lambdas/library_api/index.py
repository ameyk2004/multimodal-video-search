import json
import os
import logging
import boto3
import decimal
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            if obj % 1 > 0:
                return float(obj)
            else:
                return int(obj)
        elif isinstance(obj, BaseModel):
            return obj.model_dump()
        return super(DecimalEncoder, self).default(obj)

from models.response import (
    LibraryVideoSummary, VideosListResponse, VerseItem, 
    StorySummary, VideoDetailResponse, MusicalSegmentItem, MusicListResponse
)

class TopicListModel(BaseModel):
    video_id: str
    topics: List[str]

class QuestionListModel(BaseModel):
    video_id: str
    questions: List[str]

def _build_response(status_code, body):
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
        path = event.get('path', '')
        dynamodb = boto3.resource("dynamodb")
        table_name = os.environ.get("DYNAMODB_TABLE", "sadhananandadeep-content")
        table = dynamodb.Table(table_name)
        
        path_parameters = event.get('pathParameters') or {}
        video_id = path_parameters.get('videoId')

        if path == '/music':
            # Handle GET /music
            # Scan DB and extract all musical segments globally
            response = table.scan()
            items = response.get('Items', [])
            while 'LastEvaluatedKey' in response:
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response.get('Items', []))
            
            all_segments = []
            for item in items:
                v_id = item.get("video_id")
                raw_segments = item.get("musical_segments", [])
                for seg in raw_segments:
                    raw_start = seg.get("start_time_seconds", 0)
                    start_time = int(raw_start) if raw_start else 0
                    all_segments.append(MusicalSegmentItem(
                        video_id=v_id,
                        type=seg.get("type", "bhajan"),
                        name=seg.get("name", "Unknown"),
                        name_english=seg.get("name_english", ""),
                        saint=seg.get("saint", ""),
                        saint_english=seg.get("saint_english", ""),
                        exact_start_text=seg.get("exact_start_text", ""),
                        start_time_seconds=start_time
                    ))
            
            return _build_response(200, MusicListResponse(segments=all_segments))

        elif video_id:
            # Handle GET /videos/{video_id} and sub-routes
            response = table.get_item(Key={'video_id': video_id})
            item = response.get('Item')
            if not item:
                return _build_response(404, {"error": "Video not found"})
            
            if path.endswith('/topics'):
                topics = item.get("topics", [])
                return _build_response(200, TopicListModel(video_id=video_id, topics=topics))
                
            elif path.endswith('/questions'):
                queries = item.get("queries", [])
                return _build_response(200, QuestionListModel(video_id=video_id, questions=queries))
            
            else:
                raw_stories = item.get("stories", [])
                stories = []
                for story in raw_stories:
                    raw_start = story.get("start_time_seconds", 0)
                    start_time = int(raw_start) if raw_start else 0
                    stories.append(StorySummary(
                        title=story.get("title", "प्रवचन"),
                        title_english=story.get("title_english", ""),
                        moral=story.get("moral", ""),
                        start_time_seconds=start_time
                    ))
                
                detail_model = VideoDetailResponse(
                    video_id=video_id,
                    title=item.get("title", "प्रवचन"),
                    topics=item.get("topics", []),
                    queries=item.get("queries", []),
                    practices=item.get("actionable_practices", []),
                    verses=[
                        VerseItem(
                            verse_text=v.get("verse_text", ""),
                            source_or_author=v.get("source_or_author", "")
                        ) for v in item.get("quoted_verses", [])
                    ],
                    stories=stories
                )
                return _build_response(200, detail_model)
            
        else:
            # Handle GET /videos
            # In a real app we'd paginate, but for now we scan
            response = table.scan()
            items = response.get('Items', [])
            
            video_summaries = []
            for item in items:
                v_id = item.get("video_id")
                topics = item.get("topics", [])
                queries = item.get("queries", [])
                title = item.get("title", "प्रवचन")
                
                video_summaries.append(LibraryVideoSummary(
                    video_id=v_id,
                    title=title,
                    topics=topics,
                    topic_count=len(topics),
                    query_count=len(queries)
                ))
            
            list_response = VideosListResponse(videos=video_summaries)
            return _build_response(200, list_response)

    except Exception as exc:
        logger.error("Error in library API: %s", exc)
        return _build_response(500, {"error": "Failed to process request."})
