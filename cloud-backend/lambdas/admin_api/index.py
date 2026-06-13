import json
import os
import logging
import boto3
import decimal
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
        elif isinstance(obj, BaseModel):
            return obj.model_dump()
        return super(DecimalEncoder, self).default(obj)

def _build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, PUT, OPTIONS",
        },
        "body": json.dumps(body, cls=DecimalEncoder)
    }

def lambda_handler(event, context):
    try:
        path = event.get('path', '')
        http_method = event.get('httpMethod', '')
        
        # Handle OPTIONS request for CORS
        if http_method == 'OPTIONS':
            return _build_response(200, {})

        dynamodb = boto3.resource("dynamodb")
        table_name = os.environ.get("DYNAMODB_TABLE", "sadhananandadeep-content")
        table = dynamodb.Table(table_name)
        
        path_parameters = event.get('pathParameters') or {}
        video_id = path_parameters.get('videoId')

        if path == '/admin/videos' and http_method == 'GET':
            # List all videos for admin panel dropdown
            response = table.scan(
                ProjectionExpression="video_id, title, #t, stories, musical_segments",
                ExpressionAttributeNames={"#t": "type"}
            )
            items = response.get('Items', [])
            while 'LastEvaluatedKey' in response:
                response = table.scan(
                    ProjectionExpression="video_id, title, #t, stories, musical_segments",
                    ExpressionAttributeNames={"#t": "type"},
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
                
            videos = []
            for item in items:
                if item.get("type") != "book":
                    videos.append({
                        "video_id": item.get("video_id"),
                        "title": item.get("title", "अज्ञात"),
                        "stories": item.get("stories", []),
                        "musical_segments": item.get("musical_segments", [])
                    })
            return _build_response(200, {"videos": videos})

        elif video_id and http_method == 'GET':
            # Get full video metadata
            response = table.get_item(Key={'video_id': video_id})
            item = response.get('Item')
            if not item:
                return _build_response(404, {"error": "Video not found"})
            return _build_response(200, item)

        elif video_id and http_method == 'PUT':
            # Update specific arrays (stories and musical_segments)
            body = json.loads(event.get('body', '{}'))
            update_expr = "SET "
            expr_attr_values = {}
            
            if 'stories' in body:
                update_expr += "stories = :stories, "
                expr_attr_values[':stories'] = body['stories']
            if 'musical_segments' in body:
                update_expr += "musical_segments = :musical_segments, "
                expr_attr_values[':musical_segments'] = body['musical_segments']
                
            if not expr_attr_values:
                return _build_response(400, {"error": "No valid fields to update"})
                
            update_expr = update_expr.rstrip(", ")
            
            # Ensure start_time_seconds and end_time_seconds are integers
            # DynamoDB requires decimals for numbers, but boto3 converts integers automatically
            # However, ensure there are no float to decimal conversion issues.
            def convert_floats_to_decimals(obj):
                if isinstance(obj, float):
                    return decimal.Decimal(str(obj))
                elif isinstance(obj, dict):
                    return {k: convert_floats_to_decimals(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_floats_to_decimals(v) for v in obj]
                return obj
                
            expr_attr_values = convert_floats_to_decimals(expr_attr_values)

            table.update_item(
                Key={'video_id': video_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_attr_values
            )
            return _build_response(200, {"message": "Update successful"})

        return _build_response(404, {"error": "Route not found"})

    except Exception as exc:
        logger.error("Error in admin API: %s", exc)
        return _build_response(500, {"error": "Failed to process request."})
