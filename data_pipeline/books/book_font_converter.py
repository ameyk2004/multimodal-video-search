import os
import json
import logging
import time
import glob
from google import genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class BookFontConverter:
    """
    Reads the raw parsed JSON from books_output (which might contain legacy ASCII Marathi).
    Uses Gemini to transliterate the text into proper Unicode Devanagari.
    Overwrites the JSON with the corrected text so downstream processing (chunking, embedding) works properly.
    """
    def __init__(self, input_dir="data_pipeline/books/books_output"):
        self.input_dir = input_dir
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment.")
            
        self._genai_client = genai.Client(
            api_key=api_key,
            http_options={"timeout": 60000},
        )
        self._model_name = "gemini-2.5-flash"
        
        self.prompt_template = """The following JSON array contains pages of Marathi text encoded in a legacy ASCII font (like Shivaji or Kruti Dev).
Please translate the "text" field of each object back into standard Unicode Devanagari Marathi.
Return the exact same JSON array structure, but with the "text" fields translated. Do not alter the "page_number" or "book_name" fields.
Output ONLY valid JSON. Do not add any conversational text or markdown blocks.

JSON to convert:
{text}"""

    def process_all(self):
        json_files = glob.glob(os.path.join(self.input_dir, "*.json"))
        logger.info(f"Found {len(json_files)} book files to check for font conversion.")
        
        for filepath in json_files:
            self.process_book(filepath)
            
    def process_book(self, filepath: str):
        book_name = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            pages = json.load(f)
            
        if not pages:
            return
            
        # Check if it actually needs conversion (if we see typical legacy ASCII chars instead of devanagari)
        # Devanagari unicode range is \u0900-\u097F
        # We can just sample the first non-empty page
        sample_text = ""
        for p in pages:
            if p.get("text", "").strip():
                sample_text = p["text"]
                break
                
        has_devanagari = any('\u0900' <= char <= '\u097F' for char in sample_text)
        
        # We use a flag inside the json to know if we already converted it
        if pages[0].get("_font_converted", False) or has_devanagari:
            logger.info(f"✅ Skipping {book_name} - already in Unicode.")
            return
            
        print(f"🔄 Converting {book_name} from legacy ASCII to Unicode...")
        
        # Batch pages to reduce API calls (e.g. 5 pages per prompt)
        batch_size = 5
        converted_pages = []
        
        for i in range(0, len(pages), batch_size):
            batch = pages[i:i+batch_size]
            
            # Use JSON directly to preserve boundaries
            batch_json = json.dumps(batch, ensure_ascii=False)
            
            # Check if all pages are empty
            if all(not p.get("text", "").strip() for p in batch):
                for p in batch:
                    converted_pages.append(p)
                continue
                
            prompt = self.prompt_template.format(text=batch_json)
            
            success = False
            for attempt in range(1, 4):
                try:
                    response = self._genai_client.models.generate_content(
                        model=self._model_name,
                        contents=prompt,
                    )
                    translated = response.text.strip()
                    if translated.startswith("```json"):
                        translated = translated[7:]
                    if translated.startswith("```"):
                        translated = translated[3:]
                    if translated.endswith("```"):
                        translated = translated[:-3]
                        
                    translated_batch = json.loads(translated.strip())
                    
                    if len(translated_batch) != len(batch):
                        logger.warning(f"Length mismatch in {book_name} (Expected {len(batch)}, got {len(translated_batch)}).")
                        raise ValueError("JSON length mismatch")
                        
                    for p in translated_batch:
                        converted_pages.append(p)
                        
                    success = True
                    break
                except Exception as e:
                    logger.error(f"Error converting batch in {book_name}: {e}. Retrying {attempt}/3 in {10 * attempt}s...")
                    time.sleep(10 * attempt)
                    
            if not success:
                logger.error(f"Failed to convert pages {i} to {i+batch_size} in {book_name}")
                # Append original so we don't lose data
                converted_pages.extend(batch)
                
            print(f"  Converted pages {i+1} to {min(i+batch_size, len(pages))} / {len(pages)}", end="\r")
            
            # Rate limit protection: Sleep 4 seconds between requests to ensure we never hit the 15 RPM free tier limit
            time.sleep(4)
            
        print(f"\n✅ Finished converting {book_name}")
        
        # Mark as converted
        if converted_pages:
            converted_pages[0]["_font_converted"] = True
            
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(converted_pages, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    BookFontConverter().process_all()
