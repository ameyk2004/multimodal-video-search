"""
Video Enricher Module.
Runs ONCE per video over the full concatenated transcript to extract structured
metadata (topics, queries, stories, actionable practices, quoted verses) using the Gemini LLM.

The enrichment artefact is saved to:
    data_pipeline/enriched_metadata/<video_id>_meta.json

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

तुझे नियम (STRICT RULES):
१. Topics (विषय): व्हिडिओमध्ये खरोखर चर्चा केलेले विशिष्ट आणि अचूक विषय (Topics) काढा. तू फक्त खालील यादीतूनच विषय निवडले पाहिजेत. यादीबाहेरचा कोणताही विषय लिहू नको:
   ["अध्यात्म आणि भक्ती", "सद्गुरू आणि संत चरित्र", "मनःशांती आणि आनंद", "प्रपंच आणि परमार्थ", "अहंकार आणि विकार", "आत्मज्ञान आणि मुक्ती", "कर्म आणि प्रारब्ध", "साधना आणि ध्यान", "संस्कार आणि मानवी मूल्ये", "तत्त्वज्ञान आणि विचार", "अंधश्रद्धा आणि गैरसमज", "इतर"]
२. Queries: शिष्यांच्या मनात येणाऱ्या खऱ्या शंका आणि प्रश्न. हे प्रश्न काही छोटे आणि काही थोडे मोठे (सविस्तर) असावेत. प्रत्येक प्रश्नाचे उत्तर या व्हिडिओत असलेच पाहिजे. try to extract as many unique queries as possible, and only those the answer should be present in the video. (around 10 is a good number for longer videos, with more unique questions)
३. Stories (कथा): व्हिडिओमधील सर्व मूल्यवान कथा, दृष्टांत, किंवा उदाहरणे शोधा. कोणतीही कथा वगळू नका, जरी ती छोटी असली तरीही ती महत्त्वपूर्ण असल्यास नक्की समाविष्ट करा.
   - 'normalized_saint_name': संतांचे नाव लिहिताना नेहमी पूर्ण आणि प्रमाणित नाव लिहा (उदा. गोंदवलेकर महाराज -> श्री ब्रह्मचैतन्य गोंदवलेकर महाराज). जर संताचे नाव माहीत नसेल तर 'अज्ञात' किंवा 'सामान्य' लिहू नका, थेट 'श्री पेठे काका' लिहा.
   - 'associated_topics': ही कथा कोणत्या विषयावर आहे, ते वरील Topics च्या यादीतूनच अचूक लिहा.
   - 'moral': कथेचे तात्पर्य अतिशय सविस्तर, किमान ३ ते ४ ओळींचे (lines) असावे.
   - 'exact_start_text' / 'exact_end_text': कथेचे पहिले आणि शेवटचे ५-१० शब्द जसेच्या तसे लिहा.
४. Actionable Practices (साधना/आचरण): गुरूजींनी शिष्यांना प्रत्यक्ष कृतीत आणण्यासाठी काय उपाय किंवा कृती सांगितली आहे (उदा. 'रोज १० मिनिटे नामस्मरण करा'), त्याची यादी करा.
५. Quoted Verses (श्लोक/अभंग): गुरूजींनी एखादा श्लोक, अभंग किंवा ओवी जशीच्या तशी म्हटली असेल, तर ती वेगळी काढा.
६. Musical Segments (भजन/आरती/नामस्मरण): व्हिडिओमध्ये असलेली भजने, आरती, नामस्मरण किंवा कीर्तन ओळखा.
   - 'type': "bhajan", "aarti", "namasmarana", किंवा "kirtan" यापैकी एक इंग्रजी शब्द वापरा. पार्श्वसंगीत (background music) किंवा नुसती धून असेल तर ती वगळा, ती musical_segments मध्ये टाकू नका. तसेच 'जागृत जीवन जगुनी जिज्ञासा' किंवा 'अंतर यात्रा करूया' यासारखे सुरुवातीचे प्रास्ताविक वगळा.
   - 'name': भजनाचे, आरतीचे किंवा कीर्तनाचे नाव (उदा. "नसोडे विठ्ठला"). हे फक्त आणि फक्त 'मराठी' अक्षरांमध्ये असावे.
   - 'saint': संबंधित संतांचे नाव (उदा. "संत तुकाराम महाराज"). हे सुद्धा 'मराठी' अक्षरांमध्येच असावे. जर संताचे नाव माहीत नसेल किंवा नसेल, तर कधीही 'सामान्य' लिहू नका, नेहमी 'श्री पेठे काका' असे लिहा.
   - 'confidence': "high", "medium", किंवा "low" यापैकी एक इंग्रजी शब्द वापरा.
   - 'exact_start_text' / 'exact_end_text': भजनाचे पहिले आणि शेवटचे ५-१० शब्द जसेच्या तसे लिहा. **महत्त्वाची अट: कोणताही एक शब्द ३ पेक्षा जास्त वेळा लिहू नका (उदा. 'विठ्ठल विठ्ठल' असे अनंत वेळा लिहू नका, फक्त २-३ वेळा लिहून थांबवा).**

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
        input_dir: str = "data_pipeline/output",
        output_dir: str = "data_pipeline/enriched_metadata",
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
            http_options={'timeout': 600000}  # 600,000 ms = 10 minutes (Required for massive transcripts)
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
        """Find the start index of exact_start_text and map it to time."""
        items_to_resolve = metadata.get("stories", []) + metadata.get("musical_segments", [])
        if not items_to_resolve:
            return
            
        # Extract just the char indices for bisect
        char_indices = [idx for idx, _ in char_to_time_map]

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

            # Find the largest character index that is less than or equal to start_index
            idx = bisect.bisect_right(char_indices, start_index) - 1
            if idx >= 0:
                item["start_time_seconds"] = char_to_time_map[idx][1]
            else:
                item["start_time_seconds"] = 0.0

    def _reconstruct_transcript(self, fragments: list) -> tuple[str, list]:
        """Concatenate all fragment texts and build a char index to timestamp map."""
        full_text_parts = []
        char_to_time_map = []
        current_char_length = 0

        for f in fragments:
            text = f.get("text", f.get("marathi_raw", "")).strip()
            if not text:
                continue
                
            # Assume start time mapping
            start_time = f.get("start", f.get("start_time", 0.0))
            char_to_time_map.append((current_char_length, start_time))
            
            full_text_parts.append(text)
            # length of text plus the space added during join
            current_char_length += len(text) + 1
            
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
                    # Longer exponential back-off (10s, 20s, 40s, 80s) to handle 503 High Demand
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
        input_dir="data_pipeline/output",
        output_dir="data_pipeline/enriched_metadata",
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
