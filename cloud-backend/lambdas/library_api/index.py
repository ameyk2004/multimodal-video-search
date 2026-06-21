import json
import os
import logging
import boto3
import decimal
import urllib.parse
from typing import List, Optional
from pydantic import BaseModel, Field
from boto3.dynamodb.conditions import Key

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
    StorySummary, VideoDetailResponse, MusicalSegmentItem, MusicListResponse,
    LibraryBookSummary, BooksListResponse, BookDetailResponse,
    SaintSummary, SaintDetailResponse, SaintsListResponse
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
        table_name = os.environ.get("DYNAMODB_TABLE", "sadhananandadeep-metadata")
        table = dynamodb.Table(table_name)
        
        path_parameters = event.get('pathParameters') or {}
        video_id = urllib.parse.unquote(path_parameters.get('videoId', '')) if path_parameters.get('videoId') else None
        book_id = urllib.parse.unquote(path_parameters.get('bookId', '')) if path_parameters.get('bookId') else None
        saint_id = urllib.parse.unquote(path_parameters.get('saintId', '')) if path_parameters.get('saintId') else None

        if path == '/saints' or path.startswith('/saints/'):
            if saint_id:
                # Get Saint Bio
                bio_response = table.get_item(Key={'PK': f'SAINT#{saint_id}', 'SK': 'METADATA'})
                bio = bio_response.get('Item', {})
                if not bio:
                    return _build_response(404, {"error": "Saint not found"})
                
                # Query all Stories & Music for this Saint
                items_response = table.query(
                    KeyConditionExpression=Key('PK').eq(f'SAINT#{saint_id}')
                )
                items = items_response.get('Items', [])
                
                stories = []
                music = []
                for item in items:
                    sk = item.get('SK', '')
                    if sk.startswith('STORY#'):
                        raw_start = item.get("start_time_seconds", 0)
                        start_time = int(raw_start) if raw_start else 0
                        raw_end = item.get("end_time_seconds", 0)
                        end_time = int(raw_end) if raw_end else 0
                        stories.append(StorySummary(
                            video_id=item.get("video_id", ""),
                            title=item.get("title", "प्रवचन"),
                            title_english=item.get("title_english", ""),
                            moral=item.get("moral", ""),
                            start_time_seconds=start_time,
                            end_time_seconds=end_time
                        ))
                    elif sk.startswith('MUSIC#'):
                        raw_start = item.get("start_time_seconds", 0)
                        start_time = int(raw_start) if raw_start else 0
                        raw_end = item.get("end_time_seconds", 0)
                        end_time = int(raw_end) if raw_end else 0
                        music.append(MusicalSegmentItem(
                            video_id=item.get("video_id", ""),
                            type=item.get("type", "bhajan"),
                            name=item.get("name", "Unknown"),
                            name_english=item.get("name_english", ""),
                            saint=saint_id,
                            saint_english="",
                            exact_start_text=item.get("exact_start_text", ""),
                            start_time_seconds=start_time,
                            end_time_seconds=end_time
                        ))
                
                return _build_response(200, SaintDetailResponse(
                    name=bio.get('name', saint_id),
                    quote=bio.get('quote', ''),
                    tradition=bio.get('tradition', ''),
                    era=bio.get('era', ''),
                    fullBio=bio.get('fullBio', ''),
                    imageUrl=bio.get('imageUrl', ''),
                    learnings=bio.get('learnings', []),
                    stories=stories,
                    music=music
                ))
            else:
                # Query GSI1 for all saints
                response = table.query(
                    IndexName='GSI1',
                    KeyConditionExpression=Key('GSI1PK').eq('SAINTS')
                )
                items = response.get('Items', [])
                while 'LastEvaluatedKey' in response:
                    response = table.query(
                        IndexName='GSI1',
                        KeyConditionExpression=Key('GSI1PK').eq('SAINTS'),
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                    items.extend(response.get('Items', []))
                
                saints = []
                for item in items:
                    saints.append(SaintSummary(
                        name=item.get('name', ''),
                        quote=item.get('quote', ''),
                        imageUrl=item.get('imageUrl', '')
                    ))
                return _build_response(200, SaintsListResponse(saints=saints))

        elif path == '/books' or path.startswith('/books/'):
            if book_id:
                response = table.get_item(Key={'PK': f'BOOK#{book_id}', 'SK': 'METADATA'})
                item = response.get('Item')
                if not item:
                    return _build_response(404, {"error": "Book not found"})
                
                detail_model = BookDetailResponse(
                    video_id=book_id,
                    title=item.get("title", "अज्ञात पुस्तक"),
                    author=item.get("author", "अज्ञात"),
                    date_written=item.get("date_written", "अज्ञात"),
                    summary=item.get("summary", ""),
                    for_whom=item.get("for_whom", ""),
                    mood=item.get("mood", ""),
                    structure_type=item.get("structure_type", ""),
                    topics=item.get("topics", []),
                    questions=item.get("questions", []),
                    key_learnings=item.get("key_learnings", []),
                    table_of_contents=item.get("table_of_contents", [])
                )
                return _build_response(200, detail_model)
            else:
                response = table.query(
                    IndexName='GSI1',
                    KeyConditionExpression=Key('GSI1PK').eq('BOOKS')
                )
                items = response.get('Items', [])
                while 'LastEvaluatedKey' in response:
                    response = table.query(
                        IndexName='GSI1',
                        KeyConditionExpression=Key('GSI1PK').eq('BOOKS'),
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                    items.extend(response.get('Items', []))
                
                book_summaries = []
                for item in items:
                    book_summaries.append(LibraryBookSummary(
                        video_id=item.get("video_id", item.get("PK", "").split("#")[-1]),
                        title=item.get("title", "अज्ञात पुस्तक"),
                        author=item.get("author", "अज्ञात"),
                        topics=item.get("topics", []),
                        question_count=len(item.get("questions", [])),
                        mood=item.get("mood", "")
                    ))
                return _build_response(200, BooksListResponse(books=book_summaries))

        elif path == '/music':
            response = table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('GSI1PK').eq('MUSIC')
            )
            items = response.get('Items', [])
            while 'LastEvaluatedKey' in response:
                response = table.query(
                    IndexName='GSI1',
                    KeyConditionExpression=Key('GSI1PK').eq('MUSIC'),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
            
            all_segments = []
            for item in items:
                raw_start = item.get("start_time_seconds", 0)
                start_time = int(raw_start) if raw_start else 0
                raw_end = item.get("end_time_seconds", 0)
                end_time = int(raw_end) if raw_end else 0
                saint = item.get("character_or_saint", item.get("normalized_saint_name", ""))
                if not saint and item.get("PK", "").startswith("SAINT#"):
                    saint = item.get("PK").split("#", 1)[1]
                    
                all_segments.append(MusicalSegmentItem(
                    video_id=item.get("video_id", ""),
                    type=item.get("type", "bhajan"),
                    name=item.get("name", "Unknown"),
                    name_english=item.get("name_english", ""),
                    saint=saint,
                    saint_english=item.get("saint_english", ""),
                    exact_start_text=item.get("exact_start_text", ""),
                    start_time_seconds=start_time,
                    end_time_seconds=end_time
                ))
            
            return _build_response(200, MusicListResponse(segments=all_segments))

        elif video_id:
            # Handle GET /videos/{video_id}
            response = table.get_item(Key={'PK': f'VIDEO#{video_id}', 'SK': 'METADATA'})
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
                # Query all stories for this video using GSI2
                gsi2_response = table.query(
                    IndexName='GSI2',
                    KeyConditionExpression=Key('video_id').eq(video_id)
                )
                gsi2_items = gsi2_response.get('Items', [])
                
                stories = []
                for story in gsi2_items:
                    if story.get('SK', '').startswith('STORY#'):
                        raw_start = story.get("start_time_seconds", 0)
                        start_time = int(raw_start) if raw_start else 0
                        raw_end = story.get("end_time_seconds", 0)
                        end_time = int(raw_end) if raw_end else 0
                        stories.append(StorySummary(
                            video_id=story.get("video_id", ""),
                            title=story.get("title", "प्रवचन"),
                            title_english=story.get("title_english", ""),
                            moral=story.get("moral", ""),
                            start_time_seconds=start_time,
                            end_time_seconds=end_time
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
            response = table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('GSI1PK').eq('VIDEOS')
            )
            items = response.get('Items', [])
            while 'LastEvaluatedKey' in response:
                response = table.query(
                    IndexName='GSI1',
                    KeyConditionExpression=Key('GSI1PK').eq('VIDEOS'),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
            
            video_summaries = []
            for item in items:
                v_id = item.get("video_id", item.get("PK", "").split("#")[-1])
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
