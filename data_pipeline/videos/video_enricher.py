"""
Video Enricher Module.
Runs ONCE per video over the full concatenated transcript to extract structured
metadata (topics, queries, stories, actionable practices, quoted verses) using the Gemini LLM.

The enrichment artefact is saved to:
    data_pipeline/videos/enriched_metadata/<video_id>_meta.json

This step is idempotent: if the artefact already exists the video is skipped.

To run standalone:
    source venv/bin/activate
    python -m data_pipeline.video_enricher
"""
import os
import json
import logging
import time
import bisect
import re
import string
from typing import Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """तू एक अत्यंत ज्ञानी आध्यात्मिक विश्लेषक आहेस. तुझे ध्येय अशा साधकांना मदत करणे आहे ज्यांच्या मनात आध्यात्मिक शंका आहेत.
तुला संपूर्ण व्हिडिओची ट्रान्स्क्रिप्ट दिली जाईल. तुझे विचार आणि संपूर्ण आउटपुट फक्त आणि फक्त 'मराठी' भाषेत असावे.

═══════════════════════════════════════════════════
नियम १ — TOPICS (विषय)
═══════════════════════════════════════════════════
व्हिडिओमध्ये खरोखर चर्चा केलेले विशिष्ट विषय काढा. फक्त खालील यादीतूनच निवडा:
["अध्यात्म आणि भक्ती", "सद्गुरू आणि संत चरित्र", "मनःशांती आणि आनंद", "प्रपंच आणि परमार्थ", "अहंकार आणि विकार", "आत्मज्ञान आणि मुक्ती", "कर्म आणि प्रारब्ध", "साधना आणि ध्यान", "संस्कार आणि मानवी मूल्ये", "तत्त्वज्ञान आणि विचार", "अंधश्रद्धा आणि गैरसमज", "इतर"]
यादीबाहेरचा कोणताही विषय लिहू नको.

═══════════════════════════════════════════════════
नियम २ — QUERIES (प्रश्न)
═══════════════════════════════════════════════════
शिष्यांच्या मनात येणाऱ्या खऱ्या शंका आणि प्रश्न. प्रत्येक प्रश्नाचे उत्तर या व्हिडिओत असलेच पाहिजे.
- काही प्रश्न छोटे, काही सविस्तर असावेत.
- शक्य तितके अनन्य (unique) प्रश्न काढा (लांब व्हिडिओसाठी सुमारे १० प्रश्न योग्य आहेत).

═══════════════════════════════════════════════════
नियम ३ — STORIES (कथा) ← सर्वात महत्त्वाचा नियम
═══════════════════════════════════════════════════
व्हिडिओमधील मूल्यवान कथा, दृष्टांत, किंवा उदाहरणे शोधा.

**CRITICAL — कथा ओळखण्याचे निकष:**
✅ कथा समाविष्ट करा जेव्हा:
   - गुरूजी एखाद्या संत, भक्त, किंवा व्यक्तीची घटना सांगतात
   - कथेला स्पष्ट सुरुवात, मध्य, आणि शेवट असतो
   - कथेचे तात्पर्य (moral) स्पष्टपणे निघते
   - कथा किमान ६०-९० सेकंद लांब आहे असे अनुमानित होते

❌ कथा समाविष्ट करू नका जेव्हा:
   - फक्त एक-दोन वाक्यांचे उदाहरण आहे (anecdote/reference)
   - कथा अपूर्ण वाटते — तात्पर्यापर्यंत पोहोचत नाही
   - फक्त एखाद्या संताचा उल्लेख आहे, घटना नाही

**exact_start_text — कठोर नियम:**
- कथा सुरू होते तेव्हाचे पहिले ७-१० शब्द जसेच्या तसे लिहा.
- ट्रान्स्क्रिप्टमधून थेट copy करा — शब्द बदलू नका, अनुवाद करू नका.

**exact_end_text — सर्वात महत्त्वाचा नियम:**
- exact_end_text हे कथेचे LOGICAL END असणे आवश्यक आहे — म्हणजेच जिथे कथेचे तात्पर्य पूर्ण होते किंवा गुरूजी कथेचा निष्कर्ष सांगतात, तिथून शेवटचे ७-१० शब्द घ्या.
- कधीही कथा अर्धवट सोडू नका. जर गुरूजी म्हणतात "...म्हणून नामस्मरण हेच खरे साधन आहे" — हे शेवटचे वाक्य exact_end_text असावे.
- ट्रान्स्क्रिप्टमधून थेट copy करा — शब्द बदलू नका.
- एकाच शब्दाची ३ पेक्षा जास्त वेळा पुनरावृत्ती करू नका.

**normalized_saint_name:** संतांचे पूर्ण आणि प्रमाणित नाव लिहा:
- गोंदवलेकर महाराज → श्री ब्रह्मचैतन्य गोंदवलेकर महाराज
- तुकाराम → संत तुकाराम महाराज
- रामदास → समर्थ रामदास स्वामी
- ज्ञानेश्वर → संत ज्ञानेश्वर महाराज
जर संताचे नाव माहीत नसेल तर 'श्री पेठे काका' लिहा (कधीही 'अज्ञात' किंवा 'सामान्य' लिहू नका).

**associated_topics:** Topics च्या वरील यादीतूनच अचूक लिहा.

**moral:** कथेचे तात्पर्य किमान ३-४ ओळींचे सविस्तर असावे.

═══════════════════════════════════════════════════
नियम ४ — ACTIONABLE PRACTICES (साधना/आचरण)
═══════════════════════════════════════════════════
गुरूजींनी शिष्यांना प्रत्यक्ष कृतीत आणण्यासाठी काय उपाय सांगितले (उदा. 'रोज १० मिनिटे नामस्मरण करा'), त्याची यादी करा.

═══════════════════════════════════════════════════
नियम ५ — QUOTED VERSES (श्लोक/अभंग)
═══════════════════════════════════════════════════
गुरूजींनी एखादा श्लोक, अभंग किंवा ओवी जशीच्या तशी म्हटली असेल, तर ती वेगळी काढा.

═══════════════════════════════════════════════════
नियम ६ — MUSICAL SEGMENTS (भजन/आरती/नामस्मरण) ← खूप महत्त्वाचे नियम
═══════════════════════════════════════════════════

**STEP 1 — काय वगळायचे (NEVER include these):**
❌ खालील गोष्टी कधीही musical_segment म्हणून नोंद करू नका:
   - पार्श्वसंगीत (background music) किंवा नुसती धून
   - व्हिडिओचे प्रास्ताविक (intro jingle): 'जागृत जीवन जगुनी जिज्ञासा', 'अंतर यात्रा करूया' — हे कधीही नोंद करू नका
   - जयघोष / audience response: 'सद्गुरु महाराज की जय', 'जय जय राम', 'सद्गुरुनाथ महाराज की जय' — हे भजन नाहीत
   - कोणताही segment जो ३०-४५ सेकंदांपेक्षा कमी असेल
   - 'अज्ञात' नावाचा कोणताही segment

**STEP 2 — `name` (भजनाचे नाव) — कठोर नियम:**
- नाव म्हणजे भजनाचे **प्रचलित/प्रसिद्ध नाव** — पहिल्या ओळीचा तुकडा नव्हे.
- उदा. "विठ्ठल विठ्ठल विठ्ठल" हे नाव नाही → योग्य नाव: "विठ्ठल नामस्मरण"
- उदा. "राम कृष्ण हरी राम कृष्ण हरी" हे नाव नाही → योग्य नाव: "राम कृष्ण हरी नामस्मरण"
- जर प्रचलित नाव माहीत नसेल, तर पहिल्या ओळीचा संपूर्ण अर्थपूर्ण भाग नाव म्हणून वापरा (फक्त एक-दोन शब्द नाही).
- नाव फक्त मराठी अक्षरांमध्ये असावे.

**STEP 3 — `type` — प्रत्येक प्रकाराची व्याख्या:**
- `aarti`: "आरती" शब्द नावात येतो, किंवा दीप/निरांजन ओवाळण्याची संकल्पना आहे → type = "aarti"
- `namasmarana`: एकाच देवाच्या/नामाची सतत पुनरावृत्ती, फक्त नाम-जप → type = "namasmarana"
- `kirtan`: कथा-निरूपणासह गायन, प्रश्नोत्तरे आणि संगीत एकत्र → type = "kirtan"
- `bhajan`: वरील तीन प्रकारांत बसत नाही असे भक्तिगीत → type = "bhajan"

**STEP 4 — `saint` (रचयिता) — कठोर नियम:**
- saint म्हणजे **भजनाचे मूळ रचयिता** — गाणारे किंवा सादर करणारे नव्हे.
- प्रमाणित नावे वापरा:
  - तुकाराम → संत तुकाराम महाराज
  - ज्ञानेश्वर → संत ज्ञानेश्वर महाराज
  - रामदास → समर्थ रामदास स्वामी
  - नामदेव → संत नामदेव महाराज
  - एकनाथ → संत एकनाथ महाराज
  - ब्रह्मचैतन्य → श्री ब्रह्मचैतन्य गोंदवलेकर महाराज
  - कबीर → संत कबीर
- **जर रचयिता माहीत नसेल किंवा आधुनिक रचना असेल, तरच 'श्री पेठे काका' लिहा.**
- कधीही 'अज्ञात' किंवा 'सामान्य' लिहू नका.

**STEP 5 — `exact_start_text` / `exact_end_text`:**
- ट्रान्स्क्रिप्टमधून थेट copy करा — ७-१० शब्द, जसेच्या तसे.
- एकाच शब्दाची ३ पेक्षा जास्त वेळा पुनरावृत्ती करू नका.
- उदा. "विठ्ठल विठ्ठल जय हरी विठ्ठल" — योग्य. "विठ्ठल विठ्ठल विठ्ठल विठ्ठल विठ्ठल" — चुकीचे.

**STEP 6 — `confidence`:**
- `high`: नाव आणि रचयिता दोन्ही निश्चित
- `medium`: नाव माहीत पण रचयिता अनिश्चित
- `low`: नाव अनुमानित

═══════════════════════════════════════════════════

तुझे उत्तर खालील JSON schema मध्ये दे. JSON च्या बाहेर काहीही लिहू नकोस:
{
  "topics": ["string"],
  "queries": ["string"],
  "stories": [
    {
      "title": "string",
      "normalized_saint_name": "string",
      "associated_topics": ["string"],
      "moral": "string",
      "exact_start_text": "string",
      "exact_end_text": "string"
    }
  ],
  "actionable_practices": ["string"],
  "quoted_verses": [
    {
      "verse_text": "string",
      "source_or_author": "string"
    }
  ],
  "musical_segments": [
    {
      "type": "string",
      "name": "string",
      "saint": "string",
      "confidence": "string",
      "exact_start_text": "string",
      "exact_end_text": "string"
    }
  ]
}"""


class VideoEnricher:
    """
    Runs once per video over the full concatenated Marathi transcript.
    Uses Gemini to extract structured metadata.
    """

    def __init__(
        self,
        input_dir: str = "data_pipeline/videos/output",
        output_dir: str = "data_pipeline/videos/enriched_metadata",
    ):
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Gemini setup — google.genai SDK
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment / .env file.")
        self._genai_client = genai.Client(
            api_key=api_key,
            http_options={'timeout': 60000}  # 60,000 ms = 60 seconds (Fail fast if stuck)
        )
        self._model_name = "gemini-3.5-flash"
        self._gen_config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",   # ask for raw JSON directly
            temperature=0.0,
        )
        logger.info("VideoEnricher initialised with Gemini (%s) deterministic mode.", self._model_name)

    # ── Public API ────────────────────────────────────────────────────────────

    def process_video(self, video_id: str, manual_json_path: Optional[str] = None) -> Optional[dict]:
        """
        Enrich a single video. Returns the metadata dict or None if skipped.
        Idempotent: skips if artefact file already exists.
        """
        out_path = os.path.join(self.output_dir, f"{video_id}_meta.json")
        if os.path.exists(out_path):
            logger.info("Skipping %s – metadata already exists.", video_id)
            with open(out_path, encoding="utf-8") as f:
                return json.loads(f.read())

        raw_path = os.path.join(self.input_dir, f"{video_id}.json")
        if not os.path.exists(raw_path):
            logger.error("Raw transcript not found: %s", raw_path)
            return None

        with open(raw_path, encoding="utf-8") as f:
            fragments = json.load(f)

        full_text, char_to_time_map = self._reconstruct_transcript(fragments)
        if not full_text.strip():
            logger.warning("Empty transcript for %s. Skipping.", video_id)
            return None

        if manual_json_path and os.path.exists(manual_json_path):
            logger.info("Using manual LLM response from %s", manual_json_path)
            with open(manual_json_path, 'r', encoding='utf-8') as mf:
                metadata = json.load(mf)
        else:
            metadata = self._call_llm(video_id, full_text)
            
        if not metadata:
            return None

        self._resolve_timestamps(metadata, full_text, char_to_time_map)

        # Attach video_id and save
        metadata["video_id"] = video_id
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.info("Saved metadata for %s → %s", video_id, out_path)

        return metadata

    def process_all(self) -> list[dict]:
        """
        Process every raw JSON in input_dir. Idempotent.
        """
        import glob
        import random
        
        raw_files = sorted(glob.glob(os.path.join(self.input_dir, "*.json")))
        total_files = len(raw_files)
        logger.info(f"Starting enrichment process for {total_files} videos.")
        print(f"🚀 Starting enrichment process for {total_files} videos in {self.input_dir}")
        stats = {
            "total_given": total_files,
            "success": 0,
            "skipped_already_exists": 0,
            "skipped_no_result": 0,
            "error": 0
        }
        
        results = []
        for idx, filepath in enumerate(raw_files, start=1):
            video_id = os.path.splitext(os.path.basename(filepath))[0]
            print(f"[{idx}/{total_files}] Processing {video_id}...")
            
            # Check if output already exists to avoid hitting API/sleeping unnecessarily
            out_path = os.path.join(self.output_dir, f"{video_id}_meta.json")
            already_exists = os.path.exists(out_path)
            
            try:
                result = self.process_video(video_id)
                if result:
                    results.append(result)
                    if already_exists:
                        print(f"  ⏩ Skipped: Already enriched {video_id}.")
                        stats["skipped_already_exists"] += 1
                    else:
                        print(f"  ✅ Success: {video_id} enriched.")
                        stats["success"] += 1
                        # Add artificial delay to avoid hammering Gemini API and getting rate limited
                        sleep_duration = random.uniform(2.0, 5.0)
                        time.sleep(sleep_duration)
                else:
                    print(f"  ⚠️ Skipped / No result: {video_id}")
                    stats["skipped_no_result"] += 1
            except Exception as e:
                logger.error(f"Failed to process video {video_id}", exc_info=True)
                print(f"  ❌ Error processing {video_id}: {e}")
                stats["error"] += 1
                
        total_existing = 0
        if os.path.exists(self.output_dir):
            total_existing = len([f for f in os.listdir(self.output_dir) if f.endswith('_meta.json')])
            
        print("\n" + "="*50)
        print("🎬 ENRICHMENT PIPELINE SUMMARY")
        print("="*50)
        print(f"Total Raw Files Found:            {stats['total_given']}")
        print(f"Total Successfully Enriched:      {stats['success']}")
        print(f"Total in enriched_metadata/ dir:  {total_existing}")
        print("\n[ SKIPPED VIDEOS ]")
        print(f"Skipped (Already Enriched):       {stats['skipped_already_exists']}")
        print(f"Skipped (Empty/No Result):        {stats['skipped_no_result']}")
        print("\n[ ERRORS ]")
        print(f"Failed to Process:                {stats['error']}")
        print("="*50)
        print("\nEnrichment pipeline finished. Check enriched_metadata/ directory and ingestion.log")
        
        return results

    # ── Private helpers ───────────────────────────────────────────────────────
    
    def _resolve_timestamps(self, metadata: dict, full_text: str, char_to_time_map: list):
        """Find the start index of exact_start_text and map it to time using interpolation."""
        items_to_resolve = metadata.get("stories", []) + metadata.get("musical_segments", [])
        if not items_to_resolve:
            return
            
        # Extract just the char indices for bisect
        char_indices = [entry[0] for entry in char_to_time_map]

        for item in items_to_resolve:
            start_text = item.get("exact_start_text", "")
            if not start_text:
                continue
                
            start_index = full_text.find(start_text)
            if start_index == -1:
                # Fallback: Progressive regex word matching to handle punctuation differences & minor hallucinations
                words = start_text.split()
                clean_words = [w.strip(string.punctuation) for w in words if w.strip(string.punctuation)]
                
                if clean_words:
                    for length in [15, 10, 7, 5, 3]:
                        for offset in [0, 1, 2]:
                            if offset + length <= len(clean_words):
                                pattern_words = clean_words[offset : offset + length]
                                # Match sequence allowing for whitespace and punctuation gaps
                                pattern = r'[\s,.\?!;:\"\'\-]+'.join(re.escape(w) for w in pattern_words)
                                match = re.search(pattern, full_text)
                                if match:
                                    start_index = match.start()
                                    break
                        if start_index != -1:
                            break
                
                if start_index == -1:
                    item_name = item.get("title", item.get("name", "Unknown Item"))
                    logger.warning(
                        f"🚨 TIMESTAMP FAILURE | Item: '{item_name}'\n"
                        f"   Could not match LLM exact_start_text against transcript.\n"
                        f"   Snippet attempted: '{start_text[:100]}...'\n"
                        f"   Action: Defaulting start_time_seconds to 0.0s"
                    )
                    item["start_time_seconds"] = 0.0
                    continue

            # Interpolate: find the fragment and estimate exact position within it
            idx = bisect.bisect_right(char_indices, start_index) - 1
            if idx >= 0:
                frag_char_start, frag_start_time, frag_duration, frag_text_len = char_to_time_map[idx]
                chars_into = start_index - frag_char_start
                if frag_text_len > 0:
                    ratio = min(max(chars_into / frag_text_len, 0.0), 1.0)
                else:
                    ratio = 0.0
                interpolated = frag_start_time + (frag_duration * ratio)
                item["start_time_seconds"] = round(interpolated, 3)
            else:
                item["start_time_seconds"] = 0.0

    def _reconstruct_transcript(self, fragments: list) -> tuple[str, list]:
        """Concatenate all fragment texts and build a char index to timestamp map with duration info."""
        full_text_parts = []
        char_to_time_map = []  # (char_index, start_time, duration, text_len)
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
            # length of text plus the space added during join
            current_char_length += text_len + 1
            
        full_text = " ".join(full_text_parts)
        return full_text, char_to_time_map

    def _call_llm(self, video_id: str, full_text: str) -> Optional[dict]:
        """Send the full transcript to Gemini and parse the JSON response."""
        prompt = (
            f"व्हिडिओ ID: {video_id}\n\n"
            f"खालील संपूर्ण ट्रान्स्क्रिप्टचे विश्लेषण करा:\n\n{full_text}"
        )
        for attempt in range(1, 2):
            try:
                response = self._genai_client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=self._gen_config,
                )
                raw_json = response.text.strip()
                
                # Robustly extract the first complete JSON object using brace counting
                start_idx = raw_json.find('{')
                if start_idx != -1:
                    brace_count = 0
                    for i in range(start_idx, len(raw_json)):
                        if raw_json[i] == '{':
                            brace_count += 1
                        elif raw_json[i] == '}':
                            brace_count -= 1
                        
                        if brace_count == 0:
                            # Found the exact end of the first JSON object
                            raw_json = raw_json[start_idx:i + 1]
                            break
                            
                return json.loads(raw_json)
            except json.JSONDecodeError as e:
                logger.error("JSON parse error on attempt %d for %s: %s", attempt, video_id, e)
                logger.error("=== RAW LLM OUTPUT ===")
                logger.error(raw_json)
                logger.error("======================")
            except Exception as e:
                logger.error("LLM call failed on attempt %d for %s: %s", attempt, video_id, e)
                if attempt < 5:
                    error_msg = str(e).lower()
                    if "429" in error_msg or "quota" in error_msg:
                        logger.info("⏳ Gemini Rate Limit Hit! Waiting 65 seconds...")
                        time.sleep(65)
                    else:
                        sleep_time = 5 * (2 ** attempt)
                        logger.info("Sleeping for %d seconds before next attempt...", sleep_time)
                        time.sleep(sleep_time)
        return None


# ── Standalone entry-point ────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Enrich video transcripts.")
    parser.add_argument("--manual", type=str, help="Path to a manually generated JSON response from Gemini web app")
    parser.add_argument("--video_id", type=str, help="The video ID for the manual JSON response")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    enricher = VideoEnricher(
        input_dir="data_pipeline/videos/output",
        output_dir="data_pipeline/videos/enriched_metadata",
    )
    
    if args.manual and args.video_id:
        print(f"🚀 Running in MANUAL mode for video {args.video_id}")
        result = enricher.process_video(args.video_id, manual_json_path=args.manual)
        if result:
            print(f"✅ Successfully processed and saved manual metadata for {args.video_id}")
        else:
            print(f"❌ Failed to process manual metadata for {args.video_id}")
    else:
        enricher.process_all()
