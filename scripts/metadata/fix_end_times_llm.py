"""
fix_end_times_llm.py
====================
Lightweight script that uses Gemini to correctly identify the exact_end_text
for every story and musical segment, then recalculates end_time_seconds
using the same interpolation logic as the enricher pipeline.

Run in Google Colab:
    !pip install google-genai boto3 python-dotenv
    %cd /content/repo
    !python scripts/metadata/fix_end_times_llm.py --dry-run   # preview
    !python scripts/metadata/fix_end_times_llm.py              # commit to DynamoDB
"""

import os
import json
import bisect
import string
import re
import time
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from typing import Optional

import boto3
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Gemini prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """तू एक अत्यंत अचूक ट्रान्स्क्रिप्ट विश्लेषक आहेस. तुला एका प्रवचनाची ट्रान्स्क्रिप्ट दिली जाईल, आणि त्यात कोणत्या कथा (stories) आणि संगीत विभाग (musical segments) आहेत ते सांगितले जाईल.

तुझे एकमेव काम: प्रत्येक कथा आणि संगीत विभागाचा **अचूक शेवटचा वाक्यांश** ट्रान्स्क्रिप्टमधून शोधणे.

कथेचा शेवट कसा ओळखायचा:
- कथेचा शेवट म्हणजे जिथे कथेचा मुद्दा/तात्पर्य संपतो आणि गुरूजी पुढच्या विषयावर किंवा नवीन कथेवर जातात.
- कथेचा शेवट ही कथेची "punchline" किंवा शेवटचा निष्कर्ष/शिकवण असते.
- कथा अचानक (abruptly) संपत नाही – ती नैसर्गिकरित्या पूर्ण होते.

संगीत विभागाचा शेवट कसा ओळखायचा:
- भजन/आरती/नामस्मरण संपते आणि गुरूजी पुन्हा बोलायला लागतात – त्याच्या आधीचा शेवटचा ओळ.
- संगीत सेक्शनचा शेवट म्हणजे जिथे गाणे/भजन/नामस्मरण खरोखर संपते.

STRICT RULES:
१. exact_end_text हा ट्रान्स्क्रिप्टमधून VERBATIM (जसाच्या तसा) कॉपी केलेला असणे आवश्यक आहे.
२. exact_end_text मध्ये शेवटचे ८-१५ शब्द लिहा – पुरेसे की ते transcript मध्ये unique असतील.
३. कोणतेही शब्द बदलू नका, जोडू नका, काढू नका.
४. एकही शब्द hallucinate करू नका. transcript मध्ये जे लिहिले आहे तेच लिहा.
५. JSON format मध्येच उत्तर दे, बाहेर काहीही लिहू नका.

तुझे उत्तर खालील JSON schema मध्ये दे:
{
  "stories": [
    {
      "title": "string (same title as given to you)",
      "exact_end_text": "string (VERBATIM from transcript)"
    }
  ],
  "musical_segments": [
    {
      "name": "string (same name as given to you)",
      "exact_end_text": "string (VERBATIM from transcript)"
    }
  ]
}"""


# ── Transcript helpers (same as enricher pipeline) ────────────────────────────

def _reconstruct_transcript(fragments: list) -> tuple:
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


def _find_text_position(text_to_find: str, full_text: str) -> int:
    """Find the end char position of text_to_find in full_text using exact match then fuzzy fallback."""
    if not text_to_find:
        return -1

    idx = full_text.find(text_to_find)
    if idx != -1:
        return idx + len(text_to_find)

    # Fuzzy fallback: progressive regex word matching
    words = text_to_find.split()
    clean_words = [w.strip(string.punctuation) for w in words if w.strip(string.punctuation)]
    if not clean_words:
        return -1

    for length in [15, 12, 10, 8, 7, 6, 5, 4, 3]:
        for offset in [0, 1, 2]:
            if offset + length <= len(clean_words):
                pattern_words = clean_words[offset: offset + length]
                pattern = r'[\s,.\?!;:\"\'\-]+'.join(re.escape(w) for w in pattern_words)
                match = re.search(pattern, full_text)
                if match:
                    return match.end()
    return -1


def _interpolate_time(char_position: int, char_to_time_map: list) -> int:
    """Convert a character position in the full text to an integer timestamp."""
    char_indices = [entry[0] for entry in char_to_time_map]
    idx = bisect.bisect_right(char_indices, char_position) - 1
    if idx >= 0:
        frag_char_start, frag_start_time, frag_duration, frag_text_len = char_to_time_map[idx]
        chars_into = char_position - frag_char_start
        ratio = min(max(chars_into / frag_text_len, 0.0), 1.0) if frag_text_len > 0 else 0.0
        interpolated = frag_start_time + (frag_duration * ratio)
        return int(interpolated)
    return 0


def _extract_snippet(full_text: str, char_to_time_map: list, start_time_seconds: float, padding_before: int = 200) -> str:
    """Extract transcript text starting from a given timestamp (with some padding before)."""
    char_indices = [entry[0] for entry in char_to_time_map]
    times = [entry[1] for entry in char_to_time_map]

    # Find the fragment closest to start_time_seconds
    best_idx = 0
    for i, t in enumerate(times):
        if t <= start_time_seconds:
            best_idx = i
        else:
            break

    start_char = max(0, char_to_time_map[best_idx][0] - padding_before)
    return full_text[start_char:]


# ── Gemini client ─────────────────────────────────────────────────────────────

class EndTextFixer:
    def __init__(self, dry_run: bool = False):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment.")

        self._client = genai.Client(
            api_key=api_key,
            http_options={'timeout': 120000}
        )
        self._model = "gemini-2.5-flash"
        self._config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.0,
        )
        self.dry_run = dry_run

        region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))
        self._dynamodb = boto3.resource('dynamodb', region_name=region)
        self._table_name = os.environ.get("DYNAMODB_TABLE", "sadhananandadeep-content")
        self._table = self._dynamodb.Table(self._table_name)

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._raw_dir = os.path.join(base_dir, "data_pipeline", "videos", "output")

    def _build_prompt(self, video_id: str, stories: list, music: list, transcript_text: str) -> str:
        """Build a focused prompt with just the info Gemini needs."""
        segments_info = []

        for i, s in enumerate(stories):
            start_sec = s.get("start_time_seconds", 0)
            minutes = int(start_sec) // 60
            seconds = int(start_sec) % 60
            segments_info.append(
                f"कथा {i+1}:\n"
                f"  शीर्षक: {s.get('title', 'Unknown')}\n"
                f"  तात्पर्य: {s.get('moral', '')}\n"
                f"  सुरुवात वेळ: {minutes}:{seconds:02d}\n"
                f"  सुरुवातीचा मजकूर: \"{s.get('exact_start_text', '')}\""
            )

        for i, m in enumerate(music):
            start_sec = m.get("start_time_seconds", 0)
            minutes = int(start_sec) // 60
            seconds = int(start_sec) % 60
            segments_info.append(
                f"संगीत {i+1}:\n"
                f"  नाव: {m.get('name', 'Unknown')}\n"
                f"  प्रकार: {m.get('type', 'bhajan')}\n"
                f"  सुरुवात वेळ: {minutes}:{seconds:02d}\n"
                f"  सुरुवातीचा मजकूर: \"{m.get('exact_start_text', '')}\""
            )

        return (
            f"व्हिडिओ ID: {video_id}\n\n"
            f"या व्हिडिओमध्ये खालील कथा आणि संगीत विभाग आहेत:\n\n"
            + "\n\n".join(segments_info)
            + f"\n\n--- ट्रान्स्क्रिप्ट ---\n\n{transcript_text}"
        )

    def _call_llm(self, video_id: str, prompt: str) -> Optional[dict]:
        """Call Gemini with retries and rate-limit handling."""
        for attempt in range(3):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=self._config,
                )
                raw = response.text.strip()
                start_idx = raw.find('{')
                if start_idx != -1:
                    brace_count = 0
                    for i in range(start_idx, len(raw)):
                        if raw[i] == '{':
                            brace_count += 1
                        elif raw[i] == '}':
                            brace_count -= 1
                        if brace_count == 0:
                            raw = raw[start_idx:i + 1]
                            break
                return json.loads(raw)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error for {video_id} (attempt {attempt+1}): {e}")
            except Exception as e:
                err = str(e).lower()
                if "429" in err or "quota" in err:
                    wait = 65
                    logger.warning(f"Rate limited on {video_id}. Waiting {wait}s...")
                    time.sleep(wait)
                else:
                    wait = 5 * (2 ** attempt)
                    logger.error(f"LLM error for {video_id} (attempt {attempt+1}): {e}. Retrying in {wait}s...")
                    time.sleep(wait)
        return None

    def process_video(self, video_id: str, stories: list, music: list) -> dict:
        """Process a single video: get corrected end texts from Gemini, compute timestamps."""
        raw_path = os.path.join(self._raw_dir, f"{video_id}.json")
        if not os.path.exists(raw_path):
            logger.warning(f"Raw transcript not found for {video_id}. Skipping.")
            return {"video_id": video_id, "status": "skipped", "reason": "no_transcript"}

        if not stories and not music:
            return {"video_id": video_id, "status": "skipped", "reason": "no_segments"}

        with open(raw_path, "r", encoding="utf-8") as f:
            fragments = json.load(f)

        full_text, char_to_time_map = _reconstruct_transcript(fragments)
        if not full_text.strip():
            return {"video_id": video_id, "status": "skipped", "reason": "empty_transcript"}

        # Build prompt and call LLM
        prompt = self._build_prompt(video_id, stories, music, full_text)
        llm_result = self._call_llm(video_id, prompt)
        if not llm_result:
            return {"video_id": video_id, "status": "error", "reason": "llm_failed"}

        # Match LLM response back to our items
        llm_stories = {s["title"]: s["exact_end_text"] for s in llm_result.get("stories", [])}
        llm_music = {m["name"]: m["exact_end_text"] for m in llm_result.get("musical_segments", [])}

        stories_fixed = 0
        music_fixed = 0
        details = []

        for s in stories:
            title = s.get("title", "")
            new_end_text = llm_stories.get(title, "")
            if not new_end_text:
                details.append(f"  ⚠️  Story '{title}': LLM returned no end text")
                continue

            end_pos = _find_text_position(new_end_text, full_text)
            if end_pos == -1:
                details.append(f"  ❌ Story '{title}': end text not found in transcript: \"{new_end_text[:60]}...\"")
                continue

            new_end_time = _interpolate_time(end_pos, char_to_time_map)
            start_time = int(s.get("start_time_seconds", 0))

            # Sanity check: end must be after start and within 30 min
            if new_end_time <= start_time:
                details.append(f"  ❌ Story '{title}': end_time ({new_end_time}s) <= start_time ({start_time}s)")
                continue
            if (new_end_time - start_time) > 1800:
                details.append(f"  ❌ Story '{title}': duration {(new_end_time - start_time)//60}min > 30min, likely wrong")
                continue

            old_end = int(s.get("end_time_seconds", 0))
            s["exact_end_text"] = new_end_text
            s["end_time_seconds"] = new_end_time
            duration_min = (new_end_time - start_time) / 60
            details.append(
                f"  ✅ Story '{title}': {old_end}s → {new_end_time}s (duration: {duration_min:.1f}min)"
            )
            stories_fixed += 1

        for m in music:
            name = m.get("name", "")
            new_end_text = llm_music.get(name, "")
            if not new_end_text:
                details.append(f"  ⚠️  Music '{name}': LLM returned no end text")
                continue

            end_pos = _find_text_position(new_end_text, full_text)
            if end_pos == -1:
                details.append(f"  ❌ Music '{name}': end text not found in transcript: \"{new_end_text[:60]}...\"")
                continue

            new_end_time = _interpolate_time(end_pos, char_to_time_map)
            start_time = int(m.get("start_time_seconds", 0))

            if new_end_time <= start_time:
                details.append(f"  ❌ Music '{name}': end_time ({new_end_time}s) <= start_time ({start_time}s)")
                continue
            if (new_end_time - start_time) > 1800:
                details.append(f"  ❌ Music '{name}': duration {(new_end_time - start_time)//60}min > 30min, likely wrong")
                continue

            old_end = int(m.get("end_time_seconds", 0))
            m["exact_end_text"] = new_end_text
            m["end_time_seconds"] = new_end_time
            duration_min = (new_end_time - start_time) / 60
            details.append(
                f"  ✅ Music '{name}': {old_end}s → {new_end_time}s (duration: {duration_min:.1f}min)"
            )
            music_fixed += 1

        status = "updated" if (stories_fixed + music_fixed) > 0 else "no_changes"

        # Write to DynamoDB (unless dry-run)
        if not self.dry_run and status != "error":
            # Convert all numeric values to Decimal for DynamoDB
            def decimalize(obj):
                if isinstance(obj, float):
                    return Decimal(str(obj))
                if isinstance(obj, int):
                    return Decimal(str(obj))
                if isinstance(obj, dict):
                    return {k: decimalize(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [decimalize(i) for i in obj]
                return obj

            self._table.update_item(
                Key={'video_id': video_id},
                UpdateExpression="SET stories = :s, musical_segments = :m, llm_end_times_fixed = :fixed",
                ExpressionAttributeValues={
                    ':s': decimalize(stories),
                    ':m': decimalize(music),
                    ':fixed': True
                }
            )

        return {
            "video_id": video_id,
            "status": status,
            "stories_fixed": stories_fixed,
            "music_fixed": music_fixed,
            "details": details
        }

    def run(self, concurrency: int = 2, start_from: str = None, resume: bool = False):
        """Scan DynamoDB and process videos."""
        print(f"\n{'='*60}")
        print(f"🔧 End Text Fixer {'(DRY RUN)' if self.dry_run else '(LIVE MODE)'}")
        print(f"{'='*60}")
        print(f"Table: {self._table_name}")
        print(f"Raw transcripts: {self._raw_dir}")
        print(f"Concurrency: {concurrency}")
        if resume:
            print("Resume Mode: ON (skipping already fixed videos)")
        if start_from:
            print(f"Start From: {start_from}")
        print(f"{'='*60}\n")

        # Scan DynamoDB
        response = self._table.scan()
        items = response.get('Items', [])
        while 'LastEvaluatedKey' in response:
            response = self._table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))

        # Filter to only video items with stories or music
        video_items = []
        for item in items:
            vid = item.get("video_id")
            if not vid or item.get("type") == "book":
                continue
                
            # If resume is enabled, skip items that already have the fix flag
            if resume and item.get("llm_end_times_fixed") is True:
                continue
                
            stories = item.get("stories", [])
            music = item.get("musical_segments", [])
            if stories or music:
                video_items.append((vid, stories, music))

        # Sort alphabetically by video_id so --start-from is predictable
        video_items.sort(key=lambda x: x[0])
        
        if start_from:
            idx = next((i for i, v in enumerate(video_items) if v[0] == start_from), -1)
            if idx != -1:
                video_items = video_items[idx:]
                print(f"⏩ Fast-forwarded to {start_from}. Processing {len(video_items)} videos.")
            else:
                print(f"⚠️ Warning: --start-from {start_from} not found in pending videos. Processing all {len(video_items)}.")

        print(f"Found {len(video_items)} videos with stories/music to process.\n")

        # Process in batches of `concurrency` (2 at a time)
        stats = {"updated": 0, "skipped": 0, "error": 0, "no_changes": 0,
                 "total_stories": 0, "total_music": 0}

        def _process(args):
            vid, stories, music = args
            # Small random delay to avoid hitting Gemini simultaneously
            import random
            time.sleep(random.uniform(0.5, 2.0))
            return self.process_video(vid, stories, music)

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {executor.submit(_process, item): item[0] for item in video_items}

            for i, future in enumerate(as_completed(futures), 1):
                vid = futures[future]
                try:
                    result = future.result()
                    status = result["status"]
                    stats[status] = stats.get(status, 0) + 1
                    if status == "updated":
                        stats["total_stories"] += result.get("stories_fixed", 0)
                        stats["total_music"] += result.get("music_fixed", 0)

                    # Print progress
                    icon = {"updated": "✅", "skipped": "⏩", "error": "❌", "no_changes": "➖"}
                    print(f"[{i}/{len(video_items)}] {icon.get(status, '?')} {vid} ({status})")
                    for detail in result.get("details", []):
                        print(detail)
                    print()

                except Exception as e:
                    logger.error(f"Exception processing {vid}: {e}")
                    stats["error"] += 1

                # Rate limit: pause briefly between batches
                if i % concurrency == 0:
                    time.sleep(2)

        # Summary
        print(f"\n{'='*60}")
        print(f"📊 SUMMARY {'(DRY RUN - no changes written)' if self.dry_run else ''}")
        print(f"{'='*60}")
        print(f"Videos processed:      {len(video_items)}")
        print(f"Videos updated:        {stats['updated']}")
        print(f"Stories fixed:         {stats['total_stories']}")
        print(f"Music segments fixed:  {stats['total_music']}")
        print(f"Skipped:               {stats['skipped']}")
        print(f"No changes needed:     {stats['no_changes']}")
        print(f"Errors:                {stats['error']}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Fix end times using Gemini LLM")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing to DynamoDB")
    parser.add_argument("--concurrency", type=int, default=2,
                        help="Number of videos to process in parallel (default: 2)")
    parser.add_argument("--resume", action="store_true",
                        help="Skip videos that have already been fixed by this script")
    parser.add_argument("--start-from", type=str,
                        help="Start processing from this specific video_id (sorted alphabetically)")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    fixer = EndTextFixer(dry_run=args.dry_run)
    fixer.run(concurrency=args.concurrency, start_from=args.start_from, resume=args.resume)


if __name__ == "__main__":
    main()
