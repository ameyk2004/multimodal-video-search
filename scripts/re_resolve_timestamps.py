"""
Re-resolve timestamps for all existing enriched_metadata files.

Uses the raw transcripts in output/ to rebuild the char_map with interpolation,
then re-resolves start_time_seconds for stories and musical_segments
WITHOUT re-calling Gemini.

Usage:
    python scripts/re_resolve_timestamps.py
    python scripts/re_resolve_timestamps.py --dry-run   # preview changes only
"""

import bisect
import glob
import json
import logging
import os
import re
import string
import sys
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = "data_pipeline/output"
META_DIR = "data_pipeline/enriched_metadata"


def reconstruct_transcript(fragments: list) -> tuple[str, list]:
    """Build full_text and char_to_time_map with duration for interpolation."""
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
        current_char_length += text_len + 1

    full_text = " ".join(full_text_parts)
    return full_text, char_to_time_map


def interpolate_time(char_index: int, char_map: list) -> float:
    """Binary search + proportional interpolation within a fragment."""
    if not char_map:
        return 0.0

    keys = [entry[0] for entry in char_map]
    pos = bisect.bisect_right(keys, char_index) - 1
    pos = max(pos, 0)

    frag_char_start, start_time, duration, text_len = char_map[pos]
    chars_into = char_index - frag_char_start

    if text_len <= 0:
        ratio = 0.0
    else:
        ratio = min(max(chars_into / text_len, 0.0), 1.0)

    interpolated_time = start_time + (duration * ratio)
    return round(interpolated_time, 3)


def find_text_in_transcript(start_text: str, full_text: str) -> int:
    """Find exact_start_text in full_text with progressive regex fallback."""
    start_index = full_text.find(start_text)
    if start_index != -1:
        return start_index

    # Fallback: progressive regex word matching
    words = start_text.split()
    clean_words = [w.strip(string.punctuation) for w in words if w.strip(string.punctuation)]

    if clean_words:
        for length in [15, 10, 7, 5, 3]:
            for offset in [0, 1, 2]:
                if offset + length <= len(clean_words):
                    pattern_words = clean_words[offset : offset + length]
                    pattern = r'[\s,.\?!;:\"\'\-]+'.join(re.escape(w) for w in pattern_words)
                    match = re.search(pattern, full_text)
                    if match:
                        return match.start()

    return -1


def main():
    parser = argparse.ArgumentParser(description="Re-resolve timestamps in enriched_metadata without re-calling Gemini.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    args = parser.parse_args()

    meta_files = sorted(glob.glob(os.path.join(META_DIR, "*_meta.json")))
    logger.info(f"Found {len(meta_files)} metadata files in {META_DIR}")

    total_updated = 0
    total_items_fixed = 0
    total_items_unchanged = 0
    total_items_failed = 0

    for meta_path in meta_files:
        video_id = os.path.basename(meta_path).replace("_meta.json", "")
        raw_path = os.path.join(RAW_DIR, f"{video_id}.json")

        if not os.path.exists(raw_path):
            logger.warning(f"⚠️  No raw transcript for {video_id} — skipping")
            continue

        with open(raw_path, encoding="utf-8") as f:
            fragments = json.load(f)
        with open(meta_path, encoding="utf-8") as f:
            metadata = json.load(f)

        full_text, char_map = reconstruct_transcript(fragments)

        items_to_resolve = metadata.get("stories", []) + metadata.get("musical_segments", [])
        if not items_to_resolve:
            continue

        file_changed = False

        for item in items_to_resolve:
            start_text = item.get("exact_start_text", "")
            if not start_text:
                continue

            old_time = item.get("start_time_seconds", 0.0)
            start_index = find_text_in_transcript(start_text, full_text)

            if start_index == -1:
                item_name = item.get("title", item.get("name", "?"))
                logger.warning(f"  ❌ Cannot locate text for '{item_name}' in {video_id}")
                total_items_failed += 1
                continue

            new_time = interpolate_time(start_index, char_map)
            diff = abs(new_time - old_time)

            if diff > 0.5:  # Only count as changed if > 0.5s difference
                item_name = item.get("title", item.get("name", "?"))
                logger.info(f"  [{video_id}] {item_name[:50]}")
                logger.info(f"    OLD: {old_time:.1f}s  →  NEW: {new_time:.1f}s  (Δ {diff:.1f}s)")
                item["start_time_seconds"] = new_time
                file_changed = True
                total_items_fixed += 1
            else:
                total_items_unchanged += 1

        if file_changed:
            total_updated += 1
            if not args.dry_run:
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 50}")
    print(f"{'DRY RUN — ' if args.dry_run else ''}TIMESTAMP RE-RESOLUTION SUMMARY")
    print(f"{'=' * 50}")
    print(f"Meta files scanned:     {len(meta_files)}")
    print(f"Files updated:          {total_updated}")
    print(f"Items re-resolved:      {total_items_fixed}")
    print(f"Items unchanged (<0.5s):{total_items_unchanged}")
    print(f"Items failed (no text): {total_items_failed}")
    if args.dry_run:
        print(f"\n⚠️  DRY RUN — no files were modified. Remove --dry-run to apply.")
    else:
        print(f"\n✅ Done! Re-upload to DynamoDB with: python scripts/dynamo_uploader.py")


if __name__ == "__main__":
    main()
