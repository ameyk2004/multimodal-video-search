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
from typing import Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_MASTER_TOPICS = '["भक्ती", "कर्मयोग", "ध्यान/साधना", "चित्तशुद्धी", "अहंकार नाश", "सत्संग", "वैराग्य", "नामस्मरण", "ईश्वरप्राप्ती", "संसार आणि परमार्थ"]'

_SYSTEM_PROMPT = f"""तू एक अत्यंत ज्ञानी आध्यात्मिक विश्लेषक आहेस. तुझे ध्येय अशा साधकांना मदत करणे आहे ज्यांच्या मनात आध्यात्मिक शंका आहेत.
तुला संपूर्ण व्हिडिओची ट्रान्स्क्रिप्ट दिली जाईल. तुझे विचार आणि संपूर्ण आउटपुट फक्त आणि फक्त 'मराठी' भाषेत असावे.

तुझे नियम (STRICT RULES):
१. Topics (विषय): खालील दिलेल्या अधिकृत यादीमधूनच विषय निवडा. स्वतःचे नवीन विषय बनवू नका. 
अधिकृत यादी: {_MASTER_TOPICS}
२. Queries: शिष्यांच्या मनात येणाऱ्या खऱ्या शंका (उदा. 'माझे मन एकाग्र कसे करू?'). प्रत्येक प्रश्नाचे उत्तर या व्हिडिओत असलेच पाहिजे.
३. Stories (कथा): व्हिडिओमधील कथा शोधा. 
   - 'normalized_saint_name': संतांचे नाव नेहमी प्रमाणित असावे (उदा. 'तुकोबा' ऐवजी 'संत तुकाराम महाराज', 'माऊली' ऐवजी 'संत ज्ञानेश्वर महाराज'). नसल्यास 'सामान्य' लिहा.
   - 'associated_topics': ही कथा कोणत्या विषयावर आहे, ते वरील अधिकृत यादीतून निवडून लिहा.
   - 'moral': कथेचे तात्पर्य अतिशय सविस्तर, किमान ३ ते ४ ओळींचे (lines) असावे.
   - 'exact_start_text' / 'exact_end_text': कथेचे पहिले आणि शेवटचे ५-१० शब्द जसेच्या तसे लिहा.
४. Actionable Practices (साधना/आचरण): गुरूजींनी शिष्यांना प्रत्यक्ष कृतीत आणण्यासाठी काय उपाय किंवा कृती सांगितली आहे (उदा. 'रोज १० मिनिटे नामस्मरण करा'), त्याची यादी करा.
५. Quoted Verses (श्लोक/अभंग): गुरूजींनी एखादा श्लोक, अभंग किंवा ओवी जशीच्या तशी म्हटली असेल, तर ती वेगळी काढा.

तुझे उत्तर खालील JSON schema मध्ये दे. JSON च्या बाहेर काहीही लिहू नकोस:
{{
  "topics": ["MUST be from the Master List"],
  "queries": ["string"],
  "stories": [
    {{
      "title": "string",
      "normalized_saint_name": "string",
      "associated_topics": ["MUST be from the Master List"],
      "moral": "string (Detailed, 3 to 4 lines long)",
      "exact_start_text": "string",
      "exact_end_text": "string"
    }}
  ],
  "actionable_practices": ["string"],
  "quoted_verses": [
    {{
      "verse_text": "string",
      "source_or_author": "string (e.g., 'श्रीमद्भगवद्गीता', 'संत तुकाराम महाराज' or 'अज्ञात')"
    }}
  ]
}}"""


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
        self._genai_client = genai.Client(api_key=api_key)
        self._model_name = "gemini-2.5-flash"
        self._gen_config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",   # ask for raw JSON directly
            temperature=0.0,
        )
        logger.info("VideoEnricher initialised with Gemini (%s) deterministic mode.", self._model_name)

    # ── Public API ────────────────────────────────────────────────────────────

    def process_video(self, video_id: str) -> Optional[dict]:
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

        metadata = self._call_llm(video_id, full_text)
        if not metadata:
            return None

        self._resolve_story_timestamps(metadata, full_text, char_to_time_map)

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
        raw_files = glob.glob(os.path.join(self.input_dir, "*.json"))
        results = []
        for filepath in raw_files:
            video_id = os.path.splitext(os.path.basename(filepath))[0]
            result = self.process_video(video_id)
            if result:
                results.append(result)
        return results

    # ── Private helpers ───────────────────────────────────────────────────────
    
    def _resolve_story_timestamps(self, metadata: dict, full_text: str, char_to_time_map: list):
        """Find the start index of exact_start_text and map it to time."""
        stories = metadata.get("stories", [])
        if not stories:
            return
            
        # Extract just the char indices for bisect
        char_indices = [idx for idx, _ in char_to_time_map]

        for story in stories:
            start_text = story.get("exact_start_text", "")
            if not start_text:
                continue
                
            start_index = full_text.find(start_text)
            if start_index == -1:
                logger.warning(f"Hallucination detected: Could not find exact_start_text '{start_text}' in transcript.")
                continue

            # Find the largest character index that is less than or equal to start_index
            idx = bisect.bisect_right(char_indices, start_index) - 1
            if idx >= 0:
                story["start_time_seconds"] = char_to_time_map[idx][1]
            else:
                story["start_time_seconds"] = 0.0

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
        for attempt in range(1, 4):
            try:
                response = self._genai_client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=self._gen_config,
                )
                raw_json = response.text.strip()
                # Strip markdown code fences if the model adds them despite mime type
                if raw_json.startswith("```"):
                    raw_json = raw_json.split("```")[1]
                    if raw_json.startswith("json"):
                        raw_json = raw_json[4:]
                return json.loads(raw_json.strip())
            except json.JSONDecodeError as e:
                logger.error("JSON parse error on attempt %d for %s: %s", attempt, video_id, e)
            except Exception as e:
                logger.error("LLM call failed on attempt %d for %s: %s", attempt, video_id, e)
                if attempt < 3:
                    time.sleep(2 ** attempt)  # Exponential back-off
        return None


# ── Standalone entry-point ────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    enricher = VideoEnricher(
        input_dir="data_pipeline/output",
        output_dir="data_pipeline/enriched_metadata",
    )
    enricher.process_all()
