import boto3
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

TABLE_NAME = "guru-video-metadata"

# Here is the exact mapping we are using to fix the LLM hallucinations.
# Format: "Old/Incorrect Name": "New/Normalized Name"
SAINT_MAPPING = {
    # Krishnamurti
    "जिद्दू कृष्णमूर्ती": "जे. कृष्णमूर्ती",
    
    # Raman Maharshi
    "भगवान रमण महर्षी": "रमण महर्षी",
    "श्री रमण महर्षी": "रमण महर्षी",
    "संत रमण महर्षी": "रमण महर्षी",
    
    # Gondavalekar Maharaj
    "श्री गोंदवलेकर महाराज": "श्री ब्रह्मचैतन्य गोंदवलेकर महाराज",
    "संत ब्रह्मचैतन्य गोंदवलेकर महाराज": "श्री ब्रह्मचैतन्य गोंदवलेकर महाराज",
    
    # Sai Baba
    "श्री साईबाबा": "साईबाबा",
    "संत साईबाबा": "साईबाबा",
    
    # Swami Samarth
    "श्री स्वामी समर्थ महाराज": "स्वामी समर्थ महाराज",
    "संत स्वामी समर्थ महाराज": "स्वामी समर्थ महाराज",
    
    # General / Unknown
    "सामान्य": "सामान्य गुरु",
    
    # Optional additions based on your image:
    "श्री तात्यासाहेब महाराज": "तात्यासाहेब केतकर महाराज",
}

def normalize_saints():
    """
    Scans the DynamoDB table and updates 'normalized_saint_name' and 'character_or_saint'
    if they match any of the hallucinated values in our mapping.
    """
    logging.info(f"Connecting to DynamoDB table: {TABLE_NAME}")
    
    # Initialize the dynamodb resource
    # Assumes AWS credentials are setup in the environment
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1') # Ensure region is correct, using us-east-1 as default
    table = dynamodb.Table(TABLE_NAME)
    
    # 1. Scan the table to get all items
    try:
        response = table.scan()
        items = response.get('Items', [])
    except Exception as e:
        logging.error(f"Failed to scan table: {e}")
        return

    # Handle pagination if the table has more than 1MB of data
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    logging.info(f"Scanned {len(items)} items from DynamoDB. Checking for normalization...")
    
    updated_count = 0
    
    # 2. Iterate and update matching items
    for item in items:
        video_id = item.get('video_id')
        stories = item.get('stories', [])
        if not video_id or not stories:
            continue
            
        needs_update = False
        
        for i, story in enumerate(stories):
            # Check normalized_saint_name
            current_saint = story.get('normalized_saint_name')
            if current_saint and current_saint in SAINT_MAPPING:
                new_saint = SAINT_MAPPING[current_saint]
                logging.info(f"[{video_id}] Replacing normalized_saint_name: '{current_saint}' -> '{new_saint}'")
                story['normalized_saint_name'] = new_saint
                needs_update = True
                
            # Check character_or_saint (sometimes populated instead)
            current_char = story.get('character_or_saint')
            if current_char and current_char in SAINT_MAPPING:
                new_char = SAINT_MAPPING[current_char]
                logging.info(f"[{video_id}] Replacing character_or_saint: '{current_char}' -> '{new_char}'")
                story['character_or_saint'] = new_char
                needs_update = True
                
        # 3. Apply updates to the database
        if needs_update:
            try:
                table.update_item(
                    Key={'video_id': video_id},
                    UpdateExpression="SET stories = :s",
                    ExpressionAttributeValues={':s': stories}
                )
                updated_count += 1
            except Exception as e:
                logging.error(f"Failed to update {video_id}: {e}")
                
    logging.info(f"Normalization complete. Updated {updated_count} records.")

if __name__ == "__main__":
    normalize_saints()
