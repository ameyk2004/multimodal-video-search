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

class VideoSummaryModel(BaseModel):
    video_id: str
    topic_count: int = Field(default=0)
    query_count: int = Field(default=0)

class VideoListResponse(BaseModel):
    videos: List[VideoSummaryModel]

class StoryModel(BaseModel):
    video_id: str
    title: str
    character_or_saint: Optional[str] = ""
    moral: Optional[str] = ""
    exact_start_text: Optional[str] = ""
    exact_end_text: Optional[str] = ""
    start_time_seconds: int = 0

class VideoDetailModel(BaseModel):
    video_id: str
    stories: List[StoryModel] = Field(default_factory=list)

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
        table_name = os.environ.get("DYNAMODB_TABLE", "guru-video-metadata")
        table = dynamodb.Table(table_name)
        
        path_parameters = event.get('pathParameters') or {}
        video_id = path_parameters.get('videoId')

        if video_id:
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
                    stories.append(StoryModel(
                        video_id=video_id,
                        title=story.get("title", ""),
                        character_or_saint=story.get("character_or_saint", ""),
                        moral=story.get("moral", ""),
                        exact_start_text=story.get("exact_start_text", ""),
                        exact_end_text=story.get("exact_end_text", ""),
                        start_time_seconds=start_time
                    ))
                
                detail_model = VideoDetailModel(
                    video_id=video_id,
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
                
                video_summaries.append(VideoSummaryModel(
                    video_id=v_id,
                    topic_count=len(topics),
                    query_count=len(queries)
                ))
            
            list_response = VideoListResponse(videos=video_summaries)
            return _build_response(200, list_response)

    except Exception as exc:
        logger.error("Error in library API: %s", exc)
        return _build_response(500, {"error": "Failed to process request."})
