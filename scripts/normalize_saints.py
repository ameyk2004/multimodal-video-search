import boto3
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

TABLE_NAME = "guru-video-metadata"

# ─── SAINT MAPPING ────────────────────────────────────────────────────────────
SAINT_MAPPING = {
    "श्री ब्रह्मचैतन्य महाराज": "श्री ब्रह्मचैतन्य गोंदवलेकर महाराज",
    "संत गोंदवलेकर महाराज": "श्री ब्रह्मचैतन्य गोंदवलेकर महाराज",
    "रमण महर्षी": "श्री रमण महर्षी",
    "संत रमण महर्षी": "श्री रमण महर्षी",
    "भगवान रमण महर्षी": "श्री रमण महर्षी",
    "संत रामदास": "समर्थ रामदास स्वामी",
    "संत समर्थ रामदास स्वामी": "समर्थ रामदास स्वामी",
    "स्वामी समर्थ": "स्वामी समर्थ महाराज",
    "संत स्वामी समर्थ": "स्वामी समर्थ महाराज",
    "श्री स्वामी समर्थ महाराज": "स्वामी समर्थ महाराज",
    "संत रामकृष्ण परमहंस": "श्री रामकृष्ण परमहंस",
    "संत साईबाबा": "श्री साईबाबा",
    "साईबाबा": "श्री साईबाबा",
    "संत बिडकर महाराज": "श्री रामानंद बिडकर महाराज",
    "श्री रामानंद बेडकर महाराज": "श्री रामानंद बिडकर महाराज",
    "संत बाबा महाराज सहस्रबुद्धे": "संत बाबा महाराज सहस्रबुद्धे",
    "संत बाबा महाराज": "संत बाबा महाराज सहस्रबुद्धे",
    "कृष्णदास महाराज": "श्री कृष्णदास महाराज",
    "विश्वनाथ": "संत विश्वनाथ महाराज",
    "अज्ञात": "श्री पेठे काका",
    "सामान्य": "श्री पेठे काका",
    "सामान्य गुरु": "श्री पेठे काका",
    "दिन म्हणे": "श्री पेठे काका",
}

# ─── TOPIC MAPPING (Keyword Based) ────────────────────────────────────────────
TOPIC_CATEGORIES = {
    "अध्यात्म आणि भक्ती": ["भक्ती", "देव", "ईश्वर", "नामस्मरण", "प्रार्थना", "उपासना", "अध्यात्म", "भगवंत", "भजन", "पूजा", "आध्यात्मिक", "श्रद्धा", "मूर्तीपूजा", "मंत्र", "तीर्थयात्रा"],
    "सद्गुरू आणि संत चरित्र": ["गुरु", "गुरू", "संत", "सद्गुरू", "सत्पुरुष", "कृपा", "लीला", "शिष्य", "सत्संग", "अनुग्रह", "पुण्य पुरुष", "सोबती"],
    "मनःशांती आणि आनंद": ["शांती", "शांतता", "आनंद", "सुख", "दुःख", "समाधान", "भय", "चिंता", "मन", "निर्भयता", "मोकळेपणा", "असमाधान", "मनःशांती", "निर्वैरता"],
    "प्रपंच आणि परमार्थ": ["प्रपंच", "संसार", "कर्तव्य", "कौटुंबिक", "जीवन", "व्यवहार", "जबाबदारी", "विवाह", "योगक्षेम"],
    "अहंकार आणि विकार": ["अहंकार", "विकार", "वासना", "स्वार्थ", "आसक्ती", "मोह", "अभिमान", "निरहंकार", "मत्सर"],
    "आत्मज्ञान आणि मुक्ती": ["आत्म", "मुक्ती", "मृत्यू", "चैतन्य", "देह", "निर्वाण", "चराचरात", "अस्तित्व"],
    "कर्म आणि प्रारब्ध": ["कर्म", "प्रारब्ध", "पुनर्जन्म", "पूर्वजन्म", "नशीब", "ऋण", "फळ"],
    "साधना आणि ध्यान": ["साधना", "ध्यान", "तप", "योग", "एकाग्रता", "संकल्प", "सिद्धी", "आचरण", "नित्यपाठ", "अग्निहोत्र", "साधकाची"],
    "संस्कार आणि मानवी मूल्ये": ["संस्कार", "मूल्ये", "शिक्षण", "प्रामाणिकपणा", "नम्रता", "सत्य", "कृतज्ञता", "प्रेम", "सेवा", "परोपकार", "समानता", "साधेपणा", "स्वावलंबन", "शिस्त", "निसर्ग"],
    "तत्त्वज्ञान आणि विचार": ["तत्त्वज्ञान", "विचार", "विज्ञान", "दृष्टिकोन", "ज्ञान", "बुद्धी", "लौकिक", "अज्ञान", "स्मृती"],
    "अंधश्रद्धा आणि गैरसमज": ["अंधश्रद्धा", "गैरसमज", "रूढी", "परंपरा", "चुकीच्या", "भेदभाव"]
}

def normalize_topic(topic_str):
    if not isinstance(topic_str, str): return "इतर"
    for category, keywords in TOPIC_CATEGORIES.items():
        if any(keyword in topic_str for keyword in keywords):
            return category
    return "इतर"

def normalize_saint(saint_name):
    if not saint_name: return saint_name
    return SAINT_MAPPING.get(saint_name, saint_name)

def normalize_dynamodb():
    logging.info(f"Connecting to DynamoDB table: {TABLE_NAME}")
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table(TABLE_NAME)
    
    try:
        response = table.scan()
        items = response.get('Items', [])
    except Exception as e:
        logging.error(f"Failed to scan table: {e}")
        return

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    logging.info(f"Scanned {len(items)} items from DynamoDB. Checking for normalization...")
    updated_count = 0
    
    for item in items:
        video_id = item.get('video_id')
        stories = item.get('stories', [])
        musical_segments = item.get('musical_segments', [])
        
        if not video_id:
            continue
            
        needs_update = False
        
        # 1. Normalize stories
        for story in stories:
            # Topics
            old_topic = story.get('associated_topics')
            if isinstance(old_topic, list):
                norm_topics = list({normalize_topic(t) for t in old_topic})
                if old_topic != norm_topics:
                    story['associated_topics'] = norm_topics
                    needs_update = True
            elif isinstance(old_topic, str):
                new_topic = normalize_topic(old_topic)
                if old_topic != new_topic:
                    story['associated_topics'] = new_topic
                    needs_update = True
                    
            # Saints
            current_saint = story.get('normalized_saint_name')
            if current_saint:
                new_saint = normalize_saint(current_saint)
                if current_saint != new_saint:
                    story['normalized_saint_name'] = new_saint
                    needs_update = True
                    
        # 2. Normalize musical segments
        for segment in musical_segments:
            current_saint = segment.get('saint')
            if current_saint:
                new_saint = normalize_saint(current_saint)
                if current_saint != new_saint:
                    segment['saint'] = new_saint
                    needs_update = True
                
        if needs_update:
            try:
                table.update_item(
                    Key={'video_id': video_id},
                    UpdateExpression="SET stories = :s, musical_segments = :m",
                    ExpressionAttributeValues={':s': stories, ':m': musical_segments}
                )
                updated_count += 1
            except Exception as e:
                logging.error(f"Failed to update {video_id}: {e}")
                
    logging.info(f"Database Normalization complete. Updated {updated_count} records in DynamoDB.")

if __name__ == "__main__":
    normalize_dynamodb()
