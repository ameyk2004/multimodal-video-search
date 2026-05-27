import boto3
import logging
import os
import glob
import json
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

TABLE_NAME = "sadhananandadeep-content"
REGION = "us-east-1"

# =========================
# NORMALIZATION MAPS
# =========================

# Bhajan name corrections — matched against musical_segments[].name
BHAJAN_MAP = {
    "काय होऊ तराई तया सद्गुरूच्या पायी": "काय हो उतराई",
    "काय होत नाही तया सद्गुरूच्या पायी": "काय हो उतराई",

    "हरीचे गुणगाई मनुजा": "हरीचे गुण गाई मनुजा",

    "शिव हर शिव हर सदाशिव": "शिव हर रे सांब सदाशिव शिव हर रे",
    "शिव हर रे साम सदाशिव": "शिव हर रे सांब सदाशिव शिव हर रे",
}

# Saint name corrections — matched against:
#   musical_segments[].saint
#   stories[].normalized_saint_name
SAINT_MAP = {
    "श्री ब्रह्मचैतन्य महाराज": "श्री ब्रह्मचैतन्य गोंदवलेकर महाराज",
    "संत गोंदवलेकर महाराज": "श्री ब्रह्मचैतन्य गोंदवलेकर महाराज",
    "रमण महर्षी": "श्री रमण महर्षी",
    "संत रमण महर्षी": "श्री रमण महर्षी",
    "भगवान रमण महर्षी": "श्री रमण महर्षी",
    "संत रामदास": "समर्थ रामदास स्वामी",
    "संत समर्थ रामदास स्वामी": "समर्थ रामदास स्वामी",
    "समर्थ रामदास महाराज": "समर्थ रामदास स्वामी",
    "स्वामी समर्थ": "स्वामी समर्थ महाराज",
    "संत स्वामी समर्थ": "स्वामी समर्थ महाराज",
    "श्री स्वामी समर्थ": "स्वामी समर्थ महाराज",
    "श्री स्वामी समर्थ महाराज": "स्वामी समर्थ महाराज",
    "संत रामकृष्ण परमहंस": "श्री रामकृष्ण परमहंस",
    "संत साईबाबा": "श्री साईबाबा",
    "साईबाबा": "श्री साईबाबा",
    "संत बिडकर महाराज": "श्री रामानंद बिडकर महाराज",
    "श्री रामानंद बेडकर महाराज": "श्री रामानंद बिडकर महाराज",
    "संत बाबा महाराज": "संत बाबा महाराज सहस्रबुद्धे",
    "कृष्णदास महाराज": "श्री कृष्णदास महाराज",
    "विश्वनाथ": "संत विश्वनाथ महाराज",
    "अज्ञात": "श्री पेठे काका",
    "सामान्य": "श्री पेठे काका",
    "सामान्य गुरु": "श्री पेठे काका",
    "दिन म्हणे": "श्री पेठे काका",
    "संत निरंजन": "श्री निरंजन स्वामी",
    "संत निरंजन माधव": "श्री निरंजन स्वामी",
    
    # Literal & Spelling Duplicates
    "श्री अंबराव महाराज": "श्री अंबुराव महाराज",
    "श्री रमणा महर्षी": "श्री रमण महर्षी",
    "श्री स्वामी स्वरूपानंद": "श्री स्वामी स्वरूपानंद महाराज",
    "स्वामी स्वरूपानंद": "श्री स्वामी स्वरूपानंद महाराज",
    
    # Cross-Prefix Duplicates
    "श्री तैलंग स्वामी": "संत तैलंग स्वामी",
    "श्री दासगणू महाराज": "संत दासगणू महाराज",
    "श्री पंत महाराज बाळेकुंद्रीकर": "संत पंत महाराज बाळेकुंद्री",
    "श्री बाबा महाराज सहस्रबुद्धे": "संत बाबा महाराज सहस्रबुद्धे",
    "श्री ब्रह्मानंद महाराज": "स्वामी ब्रह्मानंद महाराज",
    "संत ब्रह्मानंद महाराज": "स्वामी ब्रह्मानंद महाराज",
    "श्री भाऊसाहेब महाराज उमदीकर": "संत भाऊसाहेब महाराज",
    "श्री वासुदेवानंद सरस्वती स्वामी महाराज": "संत वासुदेवानंद सरस्वती महाराज",
}

# =========================
# DYNAMODB SETUP
# =========================

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

# =========================
# HELPERS
# =========================

def scan_all_items():
    items = []
    response = table.scan()
    items.extend(response.get("Items", []))
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))
    return items


def normalize_item(item):
    """
    Walk the nested structure of a single DynamoDB item and apply
    BHAJAN_MAP and SAINT_MAP corrections in-place.
    Returns True if anything was changed.
    """
    changed = False
    video_id = item.get("video_id", "?")

    # ── musical_segments ─────────────────────────────────────────────────────
    for seg in item.get("musical_segments", []):

        # Bhajan name
        name = seg.get("name")
        if name and name in BHAJAN_MAP:
            logging.info(f"[BHAJAN] video={video_id}  OLD: {name!r}  →  NEW: {BHAJAN_MAP[name]!r}")
            seg["name"] = BHAJAN_MAP[name]
            changed = True

        # Saint inside musical_segment
        saint = seg.get("saint")
        if saint and saint in SAINT_MAP:
            logging.info(f"[SAINT/segment] video={video_id}  OLD: {saint!r}  →  NEW: {SAINT_MAP[saint]!r}")
            seg["saint"] = SAINT_MAP[saint]
            changed = True

    # ── stories ───────────────────────────────────────────────────────────────
    for story in item.get("stories", []):
        saint = story.get("normalized_saint_name")
        if saint and saint in SAINT_MAP:
            logging.info(f"[SAINT/story] video={video_id}  OLD: {saint!r}  →  NEW: {SAINT_MAP[saint]!r}")
            story["normalized_saint_name"] = SAINT_MAP[saint]
            changed = True

    return changed


# =========================
# LOCAL JSON NORMALIZATION
# =========================

def normalize_local_files(directory="data_pipeline/enriched_metadata"):
    """
    Reads all local JSON files, applies normalizations, and rewrites them if changed.
    """
    json_files = glob.glob(os.path.join(directory, "*.json"))
    updated_files = 0
    
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                item = json.load(f)
                
            if normalize_item(item):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(item, f, ensure_ascii=False, indent=2)
                updated_files += 1
        except Exception as e:
            logging.error(f"Failed to normalize local file {filepath}: {e}")
            
    logging.info(f"Done local normalization. Updated {updated_files} JSON files.")

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    # 1. Normalize local JSON files
    logging.info("Starting normalization of local JSON files...")
    normalize_local_files()
    
    # 2. Normalize DynamoDB
    logging.info("Starting normalization of DynamoDB...")
    items = scan_all_items()
    logging.info(f"Total Items Scanned from DynamoDB: {len(items)}")

    updated_count = 0

    for item in items:
        if normalize_item(item):
            video_id = item["video_id"]
            try:
                table.update_item(
                    Key={"video_id": video_id},
                    UpdateExpression="SET musical_segments = :ms, stories = :st",
                    ExpressionAttributeValues={
                        ":ms": item.get("musical_segments", []),
                        ":st": item.get("stories", []),
                    },
                )
                updated_count += 1
            except Exception as e:
                logging.error(f"Failed to update {video_id}: {e}")

    logging.info(f"Done. Total Updated Items: {updated_count}")
