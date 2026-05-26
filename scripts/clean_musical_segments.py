import boto3
from decimal import Decimal

def clean_segments():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('sadhananandadeep-content')
    
    print("Scanning DynamoDB table for items with musical_segments...")
    response = table.scan()
    items = response.get('Items', [])
    
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
        
    invalid_names = {"", "अज्ञात", "शांत संगीत", "प्रार्थना संगीत", "मंगलाचरण आणि प्रार्थना"}
    
    total_removed = 0
    updated_items_count = 0
    
    for item in items:
        video_id = item.get('video_id')
        segments = item.get('musical_segments', [])
        
        if not segments:
            continue
            
        original_count = len(segments)
        valid_segments = []
        
        for seg in segments:
            name = seg.get('name', '').strip()
            seg_type = seg.get('type', '')
            
            start = float(seg.get('start_time_seconds', 0))
            end = float(seg.get('end_time_seconds', 0))
            
            # Identify hallucinated segments
            
            # 1. Check for completely invalid names
            if name in invalid_names:
                continue
                
            # 2. Check for background_music type
            if seg_type == 'background_music':
                continue
                
            # 3. Check for short duration (less than 5 seconds) 
            # ONLY if end time is actually > 0 and greater than start
            # This fixes the bug where end=0 caused negative durations and deleted everything!
            if end > 0 and end > start:
                duration = end - start
                if duration < 5.0:
                    continue
                    
            # 4. Hard-delete specific hallucinated intros (even if end_time is 0)
            if "जागृत जीवन" in name or "अंतर यात्रा" in name:
                continue
                
            # If it passes the checks, it's valid! Keep it.
            valid_segments.append(seg)
            
        # Check if we removed any segments 
        if valid_segments != segments:
            removed = original_count - len(valid_segments)
            total_removed += removed
            updated_items_count += 1
            
            print(f"Updating {video_id}: Removed {removed} hallucinated segments / Standardized names. ({len(valid_segments)} valid remaining)")
            
            # Update DynamoDB
            table.update_item(
                Key={'video_id': video_id},
                UpdateExpression="SET musical_segments = :val",
                ExpressionAttributeValues={':val': valid_segments}
            )
            
    print(f"\nCleanup Complete!")
    print(f"Total Segments Removed: {total_removed}")
    print(f"Total Videos Updated: {updated_items_count}")

if __name__ == "__main__":
    clean_segments()
