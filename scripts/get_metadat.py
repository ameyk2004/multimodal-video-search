import boto3
import json

def get_unique_metadata():
    # Make sure to set your correct AWS region
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1') 
    table = dynamodb.Table('sadhananandadeep-content')

    unique_topics = set()
    unique_saints = set()
    all_musical_segments = []

    print("Scanning DynamoDB table...")
    response = table.scan()
    items = response.get('Items', [])

    # Handle pagination in case you have lots of data
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    for item in items:
        video_id = item.get('video_id', 'Unknown')
        
        # 1. Extract from stories
        for story in item.get('stories', []):
            # Topics
            if 'associated_topics' in story:
                topics = story['associated_topics']
                if isinstance(topics, list):
                    unique_topics.update(topics)
                elif isinstance(topics, str):
                    unique_topics.add(topics)
            
            # Saints from stories
            if 'normalized_saint_name' in story:
                unique_saints.add(story['normalized_saint_name'])
                
        # 2. Extract from musical segments
        for segment in item.get('musical_segments', []):
            if 'saint' in segment:
                unique_saints.add(segment['saint'])
            
            # Store full segment info for printing
            segment_data = segment.copy()
            segment_data['video_id'] = video_id
            all_musical_segments.append(segment_data)

    # Print the results
    print("\n=== Unique Story Topics ===")
    for topic in sorted(unique_topics):
        print(f"- {topic}")

    print("\n=== Unique Saints ===")
    for saint in sorted(unique_saints):
        print(f"- {saint}")
        
    print("\n=== All Musical Segments ===")
    print(f"Total Segments Found: {len(all_musical_segments)}\n")
    
    # Sort segments by name for easier reviewing
    all_musical_segments.sort(key=lambda x: x.get('name', ''))
    
    for idx, seg in enumerate(all_musical_segments, 1):
        name = seg.get('name', 'Unknown')
        seg_type = seg.get('type', 'Unknown')
        saint = seg.get('saint', 'None')
        video_id = seg.get('video_id')
        start = seg.get('start_time_seconds', 0)
        end = seg.get('end_time_seconds', 0)
        
        print(f"{idx:03d}. {name}")
        print(f"     Type: {seg_type} | Saint: {saint}")
        print(f"     Video ID: {video_id} | Time: {start}s - {end}s")
        print("-" * 50)

if __name__ == "__main__":
    get_unique_metadata()
