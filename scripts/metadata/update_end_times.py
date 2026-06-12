import os
import json
import bisect
import string
import re
import boto3

def _reconstruct_transcript(fragments: list) -> tuple[str, list]:
    full_text_parts = []
    char_to_time_map = []
    current_char_length = 0

    for f in fragments:
        text = f.get("text", f.get("marathi_raw", "")).strip()
        if not text:
            continue
            
        start_time = float(f.get("start", f.get("start_time", 0.0)))
        duration = float(f.get("duration", 0.0))
        text_len = len(text)
        
        char_to_time_map.append((current_char_length, start_time, duration, text_len))
        full_text_parts.append(text)
        current_char_length += text_len + 1
        
    full_text = " ".join(full_text_parts)
    return full_text, char_to_time_map

def _resolve_end_times(items: list, full_text: str, char_to_time_map: list):
    char_indices = [entry[0] for entry in char_to_time_map]
    updated = False

    for item in items:
        # Avoid overriding if already set and valid
        if item.get("end_time_seconds") and item["end_time_seconds"] > 0:
            continue
            
        end_text = item.get("exact_end_text", "")
        if end_text:
            end_index = full_text.find(end_text)
            if end_index == -1:
                # Regex fallback
                words = end_text.split()
                clean_words = [w.strip(string.punctuation) for w in words if w.strip(string.punctuation)]
                if clean_words:
                    for length in [15, 10, 7, 5, 3]:
                        for offset in [0, 1, 2]:
                            if offset + length <= len(clean_words):
                                pattern_words = clean_words[offset : offset + length]
                                pattern = r'[\s,.\?!;:\"\'\-]+'.join(re.escape(w) for w in pattern_words)
                                match = re.search(pattern, full_text)
                                if match:
                                    end_index = match.end() - len(end_text)
                                    break
                        if end_index != -1:
                            break
                            
            if end_index != -1:
                target_index = end_index + len(end_text)
                idx = bisect.bisect_right(char_indices, target_index) - 1
                if idx >= 0:
                    frag_char_start, frag_start_time, frag_duration, frag_text_len = char_to_time_map[idx]
                    chars_into = target_index - frag_char_start
                    ratio = min(max(chars_into / frag_text_len, 0.0), 1.0) if frag_text_len > 0 else 0.0
                    interpolated = frag_start_time + (frag_duration * ratio)
                    item["end_time_seconds"] = round(interpolated, 3)
                    updated = True
                else:
                    item["end_time_seconds"] = item.get("start_time_seconds", 0.0)
            else:
                item["end_time_seconds"] = item.get("start_time_seconds", 0.0)
        else:
            item["end_time_seconds"] = item.get("start_time_seconds", 0.0)
            
    return updated

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    raw_dir = os.path.join(base_dir, "data_pipeline", "videos", "output")
    
    region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))
    dynamodb = boto3.resource('dynamodb', region_name=region)
    table_name = os.environ.get("DYNAMODB_TABLE", "sadhananandadeep-content")
    table = dynamodb.Table(table_name)
    
    print(f"Scanning DynamoDB table: {table_name}")
    response = table.scan()
    items = response.get('Items', [])
    
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
        
    print(f"Found {len(items)} items in DynamoDB.")
    
    updated_videos = 0
    total_stories_updated = 0
    total_music_updated = 0

    for item in items:
        video_id = item.get("video_id")
        if not video_id:
            continue
            
        stories = item.get("stories", [])
        music = item.get("musical_segments", [])
        
        if not stories and not music:
            continue
            
        raw_path = os.path.join(raw_dir, f"{video_id}.json")
        if not os.path.exists(raw_path):
            print(f"Warning: Raw transcript not found locally for {video_id}. Skipping.")
            continue
            
        with open(raw_path, "r", encoding="utf-8") as f:
            fragments = json.load(f)
            
        full_text, char_to_time_map = _reconstruct_transcript(fragments)
        
        updated_s = _resolve_end_times(stories, full_text, char_to_time_map)
        updated_m = _resolve_end_times(music, full_text, char_to_time_map)
        
        if updated_s or updated_m:
            table.update_item(
                Key={'video_id': video_id},
                UpdateExpression="SET stories = :s, musical_segments = :m",
                ExpressionAttributeValues={
                    ':s': stories,
                    ':m': music
                }
            )
            updated_videos += 1
            if updated_s: total_stories_updated += len(stories)
            if updated_m: total_music_updated += len(music)
            print(f"Updated {video_id} in DynamoDB.")

    print(f"✅ Successfully updated {updated_videos} videos in DynamoDB.")
    print(f"✅ Added end_time_seconds to {total_stories_updated} stories and {total_music_updated} musical segments.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
