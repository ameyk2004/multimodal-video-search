import boto3
import logging
import os
import glob
import json
import sys
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "sadhananandadeep-content")

# =========================
# CONFIGURATION
# =========================

BHAJANS_TO_DELETE = {
    "अज्ञात",
    "जानकी स्मरण जय जय राम",
    "जानकी जीवन स्मरण जय जय राम",
    "जानकी जीवन स्मरण",
    "जानकी जीवनस्मरण जय जय राम",
    "जानकी अनुस्मरणे जय राम",
    "जानकीस्मरण जय जय राम",
    "जय जय राम",
    "सद्गुरु महाराज की जय",
    "सद्गुरू महाराज की जय",
    "सद्गुरुनाथ महाराज की जय",
}

# Pure title renames (old title -> new title)
BHAJANS_TO_RENAME = {
    # Pre-existing fixes
    "काय हो उतराई तया सद्गुरूच्या पायी": "काय हो उतराई",
    "तुझे रूप ध्यानी राहो माझे मन": "तुझे रूप ध्यानी राहो माझे मनी",
    "चित्ती त्याची घडावी संगती": "देव वसे चित्ती त्याची घडावी संगती",
    "मनुजा राम सदा वध रे": "मनुजा राम सदावदरे",
    "मनुजा राम सदाव": "मनुजा राम सदावदरे",
    "येऊनिया वास करीसे हृदय": "येऊनिया वास करीसी हृदयी",
    "नाम हरीचे गोड सखया": "नाम हरीचे गोड",
    "सखया नाम हरीचे गुण": "नाम हरीचे गोड",
    "न दिसे देव असुनी डोळा": "देव न दिसे असुनी डोळा",
    "राम कृष्ण हरी": "राम कृष्ण हरी नामस्मरण",
    "विठ्ठल विठ्ठल": "विठ्ठल नामस्मरण",
    "विठ्ठल विठ्ठल नामस्मरण": "विठ्ठल नामस्मरण",
    "श्री राम जय राम जय जय राम": "श्रीराम जय राम जय जय राम",

    # New renames from user

    # सखया नाम हरीचे गोड -> नाम हरीचे गोड
    "सखया नाम हरीचे गोड": "नाम हरीचे गोड",

    # कृपेने मुखी नाम येते -> ज्यांच्या कृपेने मुखी नाम येते
    "कृपेने मुखी नाम येते": "ज्यांच्या कृपेने मुखी नाम येते",

    # कट यमघाट रे बडा बिकट यम घाट रे -> बडा बिकट यम घाट रे
    "कट यमघाट रे बडा बिकट यम घाट रे": "बडा बिकट यम घाट रे",

    # चुकल्या कर्माची करा क्षमा -> तुमचा परोचा दिला तुम्हा हाती
    "चुकल्या कर्माची करा क्षमा": "तुमचा परोचा दिला तुम्हा हाती",

    # सुखासाठी कोठे जावे -> संतांचिये पायी ठेवा
    "सुखासाठी कोठे जावे": "संतांचिये पायी ठेवा",

    # अखंड रघुवीर स्मरण राहो -> माझे चित्त सदा करा पायी स्थिर
    "अखंड रघुवीर स्मरण राहो": "माझे चित्त सदा करा पायी स्थिर",

    # वणवण करीसी फुका -> नाम मार्ग हा सोपा
    "वणवण करीसी फुका": "नाम मार्ग हा सोपा",

    # गुरु वचने भवसारा -> निश्चय पूर्ण करा
    "गुरु वचने भवसारा": "निश्चय पूर्ण करा",

    # रूप अचेतन तसे सचेतन -> विश्वात्मकेची आरती
    "रूप अचेतन तसे सचेतन": "विश्वात्मकेची आरती",

    # सद्गुरू लीलामृत ग्रंथा जय आद्य चरित्रा हो -> सद्गुरूलीलामृत आरती
    "सद्गुरू लीलामृत ग्रंथा जय आद्य चरित्रा हो": "सद्गुरूलीलामृत आरती",
    # Variant without trailing हो
    "सद्गुरु लीलामृत ग्रंथा जय आद्य चरित्रा": "सद्गुरूलीलामृत आरती",

    # गाऊ संतांची आरती -> संतांची आरती
    "गाऊ संतांची आरती": "संतांची आरती",

    # एक निरंतर आम्हा ब्रह्म चैतन्यांचा आधार -> ब्रह्मचैतन्यांचा आधार
    "एक निरंतर आम्हा ब्रह्म चैतन्यांचा आधार": "ब्रह्मचैतन्यांचा आधार",

    # नामाविण हित समजू नका -> आजवरी तुम्हा सांगितला मात
    "नामाविण हित समजू नका": "आजवरी तुम्हा सांगितला मात",

    # जय जय हनुमंता -> हनुमानाची आरती
    "जय जय हनुमंता": "हनुमानाची आरती",

    # राम नाम वधो वाणी अन्नदान राहो सदनी -> राम नाम वधो वाणी
    "राम नाम वधो वाणी अन्नदान राहो सदनी": "राम नाम वधो वाणी",

    # सर्व भावे दास झालो त्यांचा -> संतांचिया पायी हा माझा विश्वास
    "सर्व भावे दास झालो त्यांचा": "संतांचिया पायी हा माझा विश्वास",

    # साई शिर्डीच्या नाथांची आरती -> साईबाबांची आरती
    "साई शिर्डीच्या नाथांची आरती": "साईबाबांची आरती",

    # आम्हा महा आरतांच्या नाथा चरणी ठेवनिया माथा ओवाळू आरती साई शिर्डीच्या नाथा -> साईबाबांची आरती
    "आम्हा महा आरतांच्या नाथा चरणी ठेवनिया माथा ओवाळू आरती साई शिर्डीच्या नाथा": "साईबाबांची आरती",

    # महाभय नामे निवारण दे -> नामची कारण दे
    "महाभय नामे निवारण दे": "नामची कारण दे",

    # जय करुणा करा आरती ओवाळू सद्गुरू माहेरा -> सुखसहिता दुःखरहिता आरती
    "जय करुणा करा आरती ओवाळू सद्गुरू माहेरा": "सुखसहिता दुःखरहिता आरती",

    # ऐसा असोनी अनुभव कासावीस होती जीव -> देव सखा जरी
    "ऐसा असोनी अनुभव कासावीस होती जीव": "देव सखा जरी",

    # कहे मोरे प्रभू घर आवे -> दीन कहे मोहे
    "कहे मोरे प्रभू घर आवे": "दीन कहे मोहे",
}

# Metadata corrections applied AFTER renaming.
# Key = final (post-rename) title. Only listed fields are updated.
SEGMENT_CORRECTIONS = {
    # सज्जनगडनिवासा राममय हृदया -> type=aarti, new title, saint = श्री पेठे काका
    "सज्जनगडनिवासा राममय हृदया": {
        "type": "aarti",
        "name": "रामदास स्वामींची आरती",
        "saint": "श्री पेठे काका",
    },

    # भजनाचा शेवट आला -> saint = ब्रह्मचैतन्य
    "भजनाचा शेवट आला": {
        "saint": "श्री ब्रह्मचैतन्य गोंदवलेकर महाराज",
    },

    # जन्मोजन्मीचे सुकृत -> saint = समर्थ रामदास स्वामी
    "जन्मोजन्मीचे सुकृत": {
        "saint": "समर्थ रामदास स्वामी",
    },

    # मनुजा राम सदावदरे -> saint = संत निरंजन महाराज
    "मनुजा राम सदावदरे": {
        "saint": "संत निरंजन महाराज",
    },

    # निश्चय पूर्ण करा (was गुरु वचने भवसारा) -> saint = संत निरंजन महाराज
    "निश्चय पूर्ण करा": {
        "saint": "संत निरंजन महाराज",
    },

    # श्री तुकोबांची आरती -> saint = श्री पेठे काका
    "श्री तुकोबांची आरती (ओवाळूया श्री तुकोबारा)": {
        "saint": "श्री पेठे काका",
    },

    # नमो नमस्ते श्री रमणाय चिद्घन स्वरूपाय -> saint = श्री पेठे काका
    "नमो नमस्ते श्री रमणाय चिद्घन स्वरूपाय": {
        "saint": "श्री पेठे काका",
    },

    # हनुमानाची आरती (was जय जय हनुमंता) -> saint = श्री पेठे काका, type = aarti
    "हनुमानाची आरती": {
        "saint": "श्री पेठे काका",
        "type": "aarti",
    },

    # राम नाम वधो वाणी -> saint = यमुनाबाई केतकर
    "राम नाम वधो वाणी": {
        "saint": "यमुनाबाई केतकर",
    },

    # माणिक प्रभू आरती -> saint = श्री पेठे काका
    "माणिक प्रभू आरती": {
        "saint": "श्री पेठे काका",
    },

    # साईबाबांची आरती -> saint = श्री पेठे काका, type = aarti
    "साईबाबांची आरती": {
        "saint": "श्री पेठे काका",
        "type": "aarti",
    },

    # मी माझे विसरून जाई -> saint = श्री ब्रह्मचैतन्य गोंदवलेकर महाराज
    "मी माझे विसरून जाई": {
        "saint": "श्री ब्रह्मचैतन्य गोंदवलेकर महाराज",
    },

    # मी नाही पाहिला मी नाही देखिला -> saint = कै. जगन्नाथपंत आठवले
    "मी नाही पाहिला मी नाही देखिला": {
        "saint": "कै. जगन्नाथपंत आठवले",
    },

    # गोंदवलेकर महाराजांची आरती -> saint = श्री पेठे काका
    "गोंदवलेकर महाराजांची आरती": {
        "saint": "श्री पेठे काका",
    },

    # आजवरी तुम्हा सांगितला मात (was नामाविण हित समजू नका)
    # -> saint = श्री ब्रह्मचैतन्य गोंदवलेकर महाराज
    "आजवरी तुम्हा सांगितला मात": {
        "saint": "श्री ब्रह्मचैतन्य गोंदवलेकर महाराज",
    },

    # माझे चित्त सदा करा पायी स्थिर (was अखंड रघुवीर स्मरण राहो)
    # -> saint = श्री ब्रह्मचैतन्य गोंदवलेकर महाराज
    "माझे चित्त सदा करा पायी स्थिर": {
        "saint": "श्री ब्रह्मचैतन्य गोंदवलेकर महाराज",
    },

    # बंध विमोचन राम -> saint = वेण्णा स्वामी
    "बंध विमोचन राम": {
        "saint": "वेण्णा स्वामी",
    },

    # तुझ्या पायाची आठवण -> saint = संत विश्वनाथ महाराज
    "तुझ्या पायाची आठवण": {
        "saint": "संत विश्वनाथ महाराज",
    },

    # विश्वात्मकेची आरती (was रूप अचेतन तसे सचेतन) -> type = aarti
    "विश्वात्मकेची आरती": {
        "type": "aarti",
    },

    # सद्गुरूलीलामृत आरती -> type = aarti
    "सद्गुरूलीलामृत आरती": {
        "type": "aarti",
    },

    # संतांची आरती (was गाऊ संतांची आरती) -> type = aarti
    "संतांची आरती": {
        "type": "aarti",
    },

    # सुखसहिता दुःखरहिता आरती (was जय करुणा) -> type = aarti
    "सुखसहिता दुःखरहिता आरती": {
        "type": "aarti",
    },
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

def clean_item(item):
    """
    Cleans up the musical_segments in-place based on the DELETE, RENAME, and CORRECTIONS config.
    Returns True if the item was changed.
    """
    changed = False
    video_id = item.get("video_id", "?")

    original_segments = item.get("musical_segments", [])
    if not original_segments:
        return False

    new_segments = []

    for seg in original_segments:
        name = seg.get("name")

        if not name:
            logging.info(f"[DELETE] video={video_id} - Removing hallucinated segment with EMPTY title")
            changed = True
            continue

        # Exception for Raghupati Raghav Rajaram
        if "रघुपति" in name or "रघुपती" in name:
            if video_id != "fLPku9IH4UA":
                logging.info(f"[DELETE] video={video_id} - Removing Raghupati Raghav variation: {name!r}")
                changed = True
                continue

        if "अंतर यात्रा" in name or "अंतरयात्रा" in name:
            logging.info(f"[DELETE] video={video_id} - Removing Antar Yatra variation: {name!r}")
            changed = True
            continue

        if "जागृत जीवन जगुनी जिज्ञासा" in name:
            logging.info(f"[DELETE] video={video_id} - Removing Jagrut Jivan variation: {name!r}")
            changed = True
            continue

        if seg.get("type") == "background_music" or name == "background_music":
            logging.info(f"[DELETE] video={video_id} - Removing background_music: {name!r}")
            changed = True
            continue

        # 1. Handle Deletions
        if name in BHAJANS_TO_DELETE:
            logging.info(f"[DELETE] video={video_id} - Removing hallucinated bhajan: {name!r}")
            changed = True
            continue  # skip adding it to new_segments

        # 2. Handle Renames (may produce the corrected title used by SEGMENT_CORRECTIONS below)
        if name in BHAJANS_TO_RENAME:
            new_name = BHAJANS_TO_RENAME[name]
            if new_name != name:
                logging.info(f"[RENAME] video={video_id} - {name!r} -> {new_name!r}")
                seg["name"] = new_name
                name = new_name  # use new name for corrections lookup
                changed = True

        # 3. Apply metadata corrections (type / saint / title overrides)
        if name in SEGMENT_CORRECTIONS:
            corrections = SEGMENT_CORRECTIONS[name]
            for field, value in corrections.items():
                if field == "name":
                    # name correction: update and re-point local name var
                    if seg.get("name") != value:
                        logging.info(f"[CORRECT] video={video_id} - '{name}' name overridden to: {value!r}")
                        seg["name"] = value
                        name = value
                        changed = True
                else:
                    if seg.get(field) != value:
                        logging.info(f"[CORRECT] video={video_id} - '{name}' {field}: {seg.get(field)!r} -> {value!r}")
                        seg[field] = value
                        changed = True

        new_segments.append(seg)

    if changed:
        item["musical_segments"] = new_segments

    return changed

def clean_local_files(directory="data_pipeline/enriched_metadata", dry_run=False):
    """
    Reads all local JSON files, applies deletions/renames/corrections, and rewrites them if changed.
    """
    json_files = glob.glob(os.path.join(directory, "*.json"))
    updated_files = 0

    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                item = json.load(f)

            if clean_item(item):
                if not dry_run:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(item, f, ensure_ascii=False, indent=2)
                updated_files += 1
        except Exception as e:
            logging.error(f"Failed to clean local file {filepath}: {e}")

    action = "Would update" if dry_run else "Updated"
    logging.info(f"Done local cleaning. {action} {updated_files} JSON files.")

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        logging.info("=========================================")
        logging.info("DRY RUN MODE - No files will be saved")
        logging.info("=========================================")

    if not BHAJANS_TO_DELETE and not BHAJANS_TO_RENAME and not SEGMENT_CORRECTIONS:
        logging.warning("No bhajans configured for deletion or renaming! Exiting.")
        sys.exit(0)

    # 1. Clean local JSON files
    logging.info("Starting cleanup of local JSON files...")
    clean_local_files(dry_run=dry_run)

    # 2. Clean DynamoDB
    logging.info("Starting cleanup of DynamoDB...")
    try:
        items = scan_all_items()
        logging.info(f"Total Items Scanned from DynamoDB: {len(items)}")

        updated_count = 0
        for item in items:
            if clean_item(item):
                video_id = item["video_id"]
                updated_count += 1
                if not dry_run:
                    try:
                        table.update_item(
                            Key={"video_id": video_id},
                            UpdateExpression="SET musical_segments = :ms",
                            ExpressionAttributeValues={
                                ":ms": item.get("musical_segments", []),
                            },
                        )
                    except Exception as e:
                        logging.error(f"Failed to update {video_id} in DynamoDB: {e}")

        action = "Would update" if dry_run else "Total Updated"
        logging.info(f"Done. {action} Items in DynamoDB: {updated_count}")

    except Exception as e:
        logging.error(f"Failed to scan or update DynamoDB: {e}")
        logging.info("Local files were still updated.")
