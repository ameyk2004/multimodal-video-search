"""
Video Enricher Module.
Runs ONCE per video over the full concatenated transcript to extract structured
metadata (topics, queries, stories) using the Gemini LLM.

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
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Strict Marathi system prompt ──────────────────────────────────────────────
_SYSTEM_PROMPT = """तू एक अत्यंत ज्ञानी आध्यात्मिक विश्लेषक आहेस. तुझे ध्येय अशा साधकांना किंवा शिष्यांना मदत करणे आहे ज्यांच्या मनात आध्यात्मिक शंका आहेत.
तुला संपूर्ण व्हिडिओची ट्रान्स्क्रिप्ट दिली जाईल. तुझे विचार आणि संपूर्ण आउटपुट फक्त आणि फक्त 'मराठी' भाषेत असावे.

१. 'primary_topics': व्हिडिओमध्ये जेवढे महत्त्वाचे आध्यात्मिक विषय सविस्तर हाताळले आहेत, ते सर्व विषय यादीत लिहा. कोणतीही संख्यात्मक मर्यादा नाही.
२. 'suggested_queries': शिष्यांच्या मनात ज्या खऱ्या आणि प्रामाणिक शंका येऊ शकतात, तसे प्रश्न तयार करा. (उदा. 'माझे मन अभ्यासात/साधनेत एकाग्र कसे करू?'). अट एकच: तू तयार केलेल्या प्रत्येक प्रश्नाचे अचूक आणि स्पष्ट उत्तर या व्हिडिओमध्ये गुरूजींनी दिलेले असलेच पाहिजे.
३. 'stories_found': व्हिडिओमध्ये गुरूजींनी सांगितलेली कोणतीही कथा, दृष्टांत किंवा उदाहरण शोधून काढा. प्रत्येक कथेचे शीर्षक, संतांचे/पात्राचे नाव (नसल्यास 'सामान्य'), आणि कथेचे तात्पर्य (moral) स्पष्ट लिहा.
४. कथेच्या अचूक वेळेसाठी (timestamps) कथेचे पहिले ५-१० शब्द ('exact_start_text') आणि शेवटचे ५-१० शब्द ('exact_end_text') जसेच्या तसे ट्रान्स्क्रिप्टमधून उचलून लिहा.

तुझे उत्तर खालील JSON schema मध्ये दे. JSON च्या बाहेर काहीही लिहू नकोस:
{
  "primary_topics": ["string", ...],
  "suggested_queries": ["string", ...],
  "stories_found": [
    {
      "title": "string",
      "character_or_saint": "string",
      "moral": "string",
      "exact_start_text": "string",
      "exact_end_text": "string"
    }
  ]
}"""


class VideoEnricher:
    """
    Runs once per video over the full concatenated Marathi transcript.
    Uses Gemini to extract structured metadata and optionally saves it to DynamoDB.
    """

    def __init__(
        self,
        input_dir: str = "data_pipeline/output",
        output_dir: str = "data_pipeline/enriched_metadata",
        dynamodb_table: Optional[str] = None,
    ):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.dynamodb_table = dynamodb_table
        os.makedirs(self.output_dir, exist_ok=True)

        # Gemini setup — google.genai SDK
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment / .env file.")
        self._genai_client = genai.Client(api_key=api_key)
        self._model_name = "gemini-2.5-pro"
        self._gen_config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",   # ask for raw JSON directly
        )
        logger.info("VideoEnricher initialised with Gemini (%s).", self._model_name)

        # Optional DynamoDB
        self._ddb = None
        if self.dynamodb_table:
            region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))
            self._ddb = boto3.resource("dynamodb", region_name=region).Table(self.dynamodb_table)
            logger.info("DynamoDB table '%s' connected.", self.dynamodb_table)

    # ── Public API ────────────────────────────────────────────────────────────

    def process_video(self, video_id: str) -> Optional[dict]:
        """
        Enrich a single video. Returns the metadata dict or None if skipped.
        Idempotent: skips if artefact file already exists.
        """
        out_path = os.path.join(self.output_dir, f"{video_id}_meta.json")
        if os.path.exists(out_path):
            logger.info("Skipping %s – metadata already exists.", video_id)
            return json.loads(open(out_path, encoding="utf-8").read())

        raw_path = os.path.join(self.input_dir, f"{video_id}.json")
        if not os.path.exists(raw_path):
            logger.error("Raw transcript not found: %s", raw_path)
            return None

        with open(raw_path, encoding="utf-8") as f:
            fragments = json.load(f)

        full_text = self._reconstruct_transcript(fragments)
        if not full_text.strip():
            logger.warning("Empty transcript for %s. Skipping.", video_id)
            return None

        metadata = self._call_llm(video_id, full_text)
        if not metadata:
            return None

        # Attach video_id and save
        metadata["video_id"] = video_id
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.info("Saved metadata for %s → %s", video_id, out_path)

        # Push to DynamoDB if configured
        if self._ddb:
            self._push_to_dynamodb(metadata)

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

    def _reconstruct_transcript(self, fragments: list) -> str:
        """Concatenate all fragment texts into a single clean string."""
        return " ".join(
            f.get("text", f.get("marathi_raw", "")).strip()
            for f in fragments
            if f.get("text") or f.get("marathi_raw")
        )

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

    def _push_to_dynamodb(self, metadata: dict):
        """Upsert the metadata record into DynamoDB."""
        try:
            self._ddb.put_item(Item=metadata)
            logger.info("Pushed video_id=%s to DynamoDB.", metadata.get("video_id"))
        except ClientError as e:
            logger.error("DynamoDB write failed: %s", e.response["Error"]["Message"])


# ── Standalone entry-point ────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    enricher = VideoEnricher(
        input_dir="data_pipeline/output",
        output_dir="data_pipeline/enriched_metadata",
        dynamodb_table=os.getenv("DYNAMODB_TABLE"),  # optional
    )
    enricher.process_all()
