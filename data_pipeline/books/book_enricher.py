"""
Book Enricher Module.
Uses Gemini to extract structured metadata from a spiritual book's text.

Output saved to:
    data_pipeline/books/books_enriched_metadata/<book_name>_meta.json
"""
import os
import json
import logging
import time
from typing import Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """तू एक अत्यंत ज्ञानी आध्यात्मिक विश्लेषक आहेस. तुझे ध्येय अशा साधकांना मदत करणे आहे ज्यांच्या मनात आध्यात्मिक शंका आहेत.
तुला एका आध्यात्मिक पुस्तकाची माहिती दिली जाईल. तुझे संपूर्ण आउटपुट फक्त 'मराठी' भाषेत असावे.

तुझे कार्य: खालील ८ गोष्टी अत्यंत नेमकेपणाने काढा —

१. author: पुस्तकाचे लेखक/संकलक. स्पष्ट नसल्यास 'अज्ञात' लिहा.

२. summary: पुस्तकाचा गाभा — ३ ते ४ ओळींत सांगा हे पुस्तक काय आहे, कोणाबद्दल आहे, आणि त्यात काय सांगितले आहे.

३. questions: या पुस्तकात ज्या प्रश्नांची उत्तरे प्रत्यक्षपणे आहेत असे ५ ते ६ प्रश्न लिहा. नियम:
   - पहिला प्रश्न (index 0) हा पुस्तकाचा मध्यवर्ती/मूलभूत प्रश्न असावा — तो पुस्तकाची संपूर्ण दिशा ठरवतो.
   - उरलेले ४ ते ५ प्रश्न त्याच पुस्तकातील इतर महत्त्वाच्या शंका असाव्यात.
   - प्रत्येक प्रश्नाचे उत्तर पुस्तकात स्पष्टपणे असलेच पाहिजे — अनुमान नको.
   - प्रश्न साधकाच्या मनातून यावेत, जसे की "मला जगण्यात शांती कशी मिळेल?" किंवा "अहंकार सोडणे म्हणजे काय?"

४. key_learnings: या पुस्तकातील ५ ते ७ महत्त्वाच्या शिकवणी — प्रत्येक एका ओळीत, ठोस आणि साधकाला थेट उपयोगी. गोल-गोल विधाने नकोत.

५. for_whom: हे पुस्तक कोणासाठी सर्वात उपयुक्त आहे? (उदा. "जे साधक अहंकाराशी झुंजत आहेत" किंवा "नव्याने भक्तिमार्गावर आलेल्यांसाठी") — १ ते २ ओळी.

६. mood: पुस्तकाचा स्वर/रचना — खालीलपैकी एक किंवा दोन शब्द निवडा: भक्तिपर, तात्विक, व्यावहारिक, कथात्मक, प्रेरणादायी, चिंतनशील, उपदेशात्मक.

७. topics: पुस्तकात खरोखर चर्चिलेले विषय — फक्त खालील यादीतून निवडा, जे लागू होतात तेच:
["अध्यात्म आणि भक्ती", "सद्गुरू आणि संत चरित्र", "मनःशांती आणि आनंद", "प्रपंच आणि परमार्थ", "अहंकार आणि विकार", "आत्मज्ञान आणि मुक्ती", "कर्म आणि प्रारब्ध", "साधना आणि ध्यान", "संस्कार आणि मानवी मूल्ये", "तत्त्वज्ञान आणि विचार", "अंधश्रद्धा आणि गैरसमज", "इतर"]

८. structure_type: पुस्तकाची रचना ओळखा. फक्त खालीलपैकी एक प्रकार निवडा: 
["numbered_essays", "verses", "q_and_a", "chapters", "continuous_text"]
(उदा. जर लेख १., २७. असे सुरू होत असतील तर "numbered_essays", जर ओव्या असतील तर "verses").

उत्तर फक्त खालील JSON format मध्ये दे. JSON च्या बाहेर काहीही लिहू नकोस:
{
  "author": "string",
  "summary": "string",
  "questions": [
    "string (मध्यवर्ती प्रश्न — पहिला)",
    "string",
    "string",
    "string",
    "string",
    "string"
  ],
  "key_learnings": ["string"],
  "for_whom": "string",
  "mood": "string",
  "topics": ["string"],
  "structure_type": "string"
}"""


class BookEnricher:
    def __init__(
        self,
        input_dir: str = "data_pipeline/books/books_output",
        output_dir: str = "data_pipeline/books/books_enriched_metadata",
    ):
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment / .env file.")

        self._genai_client = genai.Client(
            api_key=api_key,
            http_options={"timeout": 60000},
        )
        self._model_name = "gemini-3.5-flash"
        self._gen_config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.0,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_book(self, book_name: str) -> Optional[dict]:
        out_path = os.path.join(self.output_dir, f"{book_name}_meta.json")
        if os.path.exists(out_path):
            logger.info("Skipping %s – metadata already exists.", book_name)
            with open(out_path, encoding="utf-8") as f:
                return json.load(f)

        raw_path = os.path.join(self.input_dir, f"{book_name}.json")
        if not os.path.exists(raw_path):
            logger.error("Raw text not found: %s", raw_path)
            return None

        with open(raw_path, encoding="utf-8") as f:
            pages: list[dict] = json.load(f)

        full_text = self._stitch_pages(pages)
        if not full_text.strip():
            logger.warning("Empty book for %s. Skipping.", book_name)
            return None

        # Feed only the first ~60k chars to stay well within token limits
        # while still capturing author info, structure, and core content.
        sampled_text = self._smart_sample(full_text)

        metadata = self._call_llm(book_name, sampled_text)
        if not metadata:
            return None

        metadata["book_name"] = book_name
        metadata["type"] = "book"

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.info("Saved metadata for %s → %s", book_name, out_path)
        return metadata

    def process_all(self) -> list[dict]:
        import glob

        raw_files = sorted(glob.glob(os.path.join(self.input_dir, "*.json")))
        total = len(raw_files)
        print(f"🚀 Starting enrichment for {total} books in {self.input_dir}")

        stats = dict(total=total, success=0, skipped=0, error=0)
        results = []

        for idx, filepath in enumerate(raw_files, 1):
            book_name = os.path.splitext(os.path.basename(filepath))[0]
            print(f"[{idx}/{total}] {book_name} …", end=" ", flush=True)
            try:
                result = self.process_book(book_name)
                if result:
                    results.append(result)
                    stats["success"] += 1
                    print("✅")
                else:
                    stats["skipped"] += 1
                    print("⏩ skipped")
            except Exception as e:
                logger.error("Failed to process %s", book_name, exc_info=True)
                stats["error"] += 1
                print(f"❌ {e}")

        print("\n" + "=" * 50)
        print("🎬 ENRICHMENT SUMMARY")
        print("=" * 50)
        print(f"Total:    {stats['total']}")
        print(f"Success:  {stats['success']}")
        print(f"Skipped:  {stats['skipped']}")
        print(f"Errors:   {stats['error']}")
        print("=" * 50)
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _stitch_pages(pages: list[dict]) -> str:
        """Concatenate page texts in order."""
        return "\n".join(p.get("text", "") for p in pages if p.get("text"))

    @staticmethod
    def _smart_sample(text: str, max_chars: int = 60_000) -> str:
        """
        Return a representative sample of the book.
        Strategy: first 40 k chars (cover, intro, opening chapters) +
                  a middle slice (8 k) + last 8 k (conclusion / colophon).
        This covers author info, core teachings, and the ending tone.
        """
        if len(text) <= max_chars:
            return text

        head = text[:40_000]
        mid_start = len(text) // 2 - 4_000
        mid = text[mid_start: mid_start + 8_000]
        tail = text[-8_000:]
        return head + "\n\n[...]\n\n" + mid + "\n\n[...]\n\n" + tail

    def _call_llm(self, book_name: str, text: str) -> Optional[dict]:
        prompt = (
            f"पुस्तक: {book_name}\n\n"
            f"खालील पुस्तकाचे विश्लेषण करा:\n\n{text}"
        )
        for attempt in range(1, 4):
            try:
                response = self._genai_client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=self._gen_config,
                )
                raw = response.text.strip()
                # Defensively extract the outermost JSON object
                start = raw.find("{")
                if start != -1:
                    depth = 0
                    for i in range(start, len(raw)):
                        depth += (raw[i] == "{") - (raw[i] == "}")
                        if depth == 0:
                            raw = raw[start: i + 1]
                            break
                return json.loads(raw)
            except Exception as e:
                logger.warning("Attempt %d failed for %s: %s", attempt, book_name, e)
                time.sleep(5 * attempt)
        logger.error("All attempts failed for %s", book_name)
        return None


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    BookEnricher().process_all()
