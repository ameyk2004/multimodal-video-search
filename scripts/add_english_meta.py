import json
import glob
import os

DICT_PATH = 'data_pipeline/marathi_to_english_dict.json'
METADATA_DIR = 'data_pipeline/enriched_metadata'

def main():
    if not os.path.exists(DICT_PATH):
        print(f"Error: Dictionary file {DICT_PATH} not found.")
        return
        
    with open(DICT_PATH, 'r', encoding='utf-8') as f:
        transliteration_map = json.load(f)
        
    json_files = glob.glob(os.path.join(METADATA_DIR, '*.json'))
    updated_count = 0
    
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            changed = False
            
            # Process stories
            if 'stories' in data:
                for story in data['stories']:
                    # Transliterate title
                    if 'title' in story and story['title'] in transliteration_map:
                        story['title_english'] = transliteration_map[story['title']]
                        changed = True
                        
                    # Transliterate normalized_saint_name
                    if 'normalized_saint_name' in story and story['normalized_saint_name'] in transliteration_map:
                        story['normalized_saint_name_english'] = transliteration_map[story['normalized_saint_name']]
                        changed = True
                        
            # Process musical segments
            if 'musical_segments' in data:
                for seg in data['musical_segments']:
                    # Transliterate name
                    if 'name' in seg and seg['name'] in transliteration_map:
                        seg['name_english'] = transliteration_map[seg['name']]
                        changed = True
                        
                    # Transliterate saint
                    if 'saint' in seg and seg['saint'] in transliteration_map:
                        seg['saint_english'] = transliteration_map[seg['saint']]
                        changed = True
                        
            if changed:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                updated_count += 1
                
        except Exception as e:
            print(f"Failed to process {filepath}: {e}")
            
    print(f"Update complete! Added English transliteration keys to {updated_count} files.")

if __name__ == '__main__':
    main()
