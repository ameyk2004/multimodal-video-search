import json
import os
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def _build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
        },
        "body": json.dumps(body)
    }

def lambda_handler(event, context):
    try:
        dynamodb = boto3.resource("dynamodb")
        table_name = os.environ.get("DYNAMODB_TABLE", "guru-video-metadata")
        table = dynamodb.Table(table_name)
        
        # Scan the table (assuming it's small enough, otherwise we should paginate)
        response = table.scan()
        items = response.get('Items', [])
        
        all_stories = []
        for item in items:
            video_id = item.get("video_id")
            stories = item.get("stories", [])
            for story in stories:
                all_stories.append({
                    "video_id": video_id,
                    "title": story.get("title", ""),
                    "content": story.get("moral", story.get("content", ""))
                })
        
        return _build_response(200, {
            "stories": all_stories
        })

    except Exception as exc:
        logger.error("Error fetching stories: %s", exc)
        return _build_response(500, {"error": "Failed to fetch stories from database."})
