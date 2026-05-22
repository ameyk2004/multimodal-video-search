"""
TranscriptProcessor — Zero-Drift Timestamp Mapping Engine.

Responsibilities:
  1. Stitch raw YouTube fragments into one continuous Marathi string.
  2. Build an absolute char_to_time_map (character index → YouTube seconds).
  3. Split the stitched text into semantic chunks via LangChain with
     add_start_index=True so every chunk carries its exact origin offset.
  4. Resolve exact YouTube timestamps for chunks via binary search (bisect).
  5. Resolve exact YouTube timestamps for LLM-extracted story snippets
     via str.find() + the same bisect helper — one source of truth.

Usage (Colab / local):
    from data_pipeline.transcript_processor import TranscriptProcessor

    processor = TranscriptProcessor()
    chunks, char_map, full_text = processor.process_file("data_pipeline/output/9RAqjOZEOh4.json")
    story_time = processor.resolve_story_time("तिथे सोन आहे फक्त", char_map, full_text)
"""

import bisect
import json
import logging
import os
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class TranscriptProcessor:
    """
    Converts a raw YouTube transcript JSON into time-anchored semantic chunks
    with zero timestamp drift, using an absolute character-index mapping.
    """

    # ── Configuration ──────────────────────────────────────────────────────────
    _SEPARATORS = ["\n\n", "\n", "॥", "।", ".", "?", "!", " "]
    _CHUNK_SIZE = 700
    _CHUNK_OVERLAP = 150

    def __init__(self) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            separators=self._SEPARATORS,
            chunk_size=self._CHUNK_SIZE,
            chunk_overlap=self._CHUNK_OVERLAP,
            add_start_index=True,   # ← Critical: attaches absolute char offset
        )
        logger.info(
            "TranscriptProcessor ready — chunk_size=%d overlap=%d",
            self._CHUNK_SIZE,
            self._CHUNK_OVERLAP,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────

    def process_file(
        self, filepath: str, video_id: str | None = None
    ) -> tuple[list[dict[str, Any]], list[tuple[int, float]], str]:
        """
        Full pipeline for one raw transcript file.

        Returns
        -------
        chunks       : list of dicts ready for embedding / Qdrant upload.
        char_map     : sorted list of (char_index, youtube_seconds) tuples.
        full_text    : the stitched Marathi string (kept for story lookup).
        """
        if video_id is None:
            video_id = os.path.splitext(os.path.basename(filepath))[0]

        with open(filepath, encoding="utf-8") as f:
            fragments = json.load(f)

        full_text, char_map = self._stitch(fragments)
        logger.info("Stitched %d fragments → %d chars.", len(fragments), len(full_text))

        doc = Document(page_content=full_text, metadata={"video_id": video_id})
        lc_chunks = self._splitter.split_documents([doc])
        logger.info("LangChain produced %d chunks.", len(lc_chunks))

        chunks = self._resolve_chunk_timestamps(lc_chunks, char_map, video_id)
        return chunks, char_map, full_text

    def resolve_story_time(
        self,
        exact_start_text: str,
        char_map: list[tuple[int, float]],
        full_text: str,
    ) -> float | None:
        """
        Map an LLM-extracted story snippet to its exact YouTube start time.

        Parameters
        ----------
        exact_start_text : verbatim first 5-10 words from the LLM output.
        char_map         : the map returned by process_file().
        full_text        : the stitched string returned by process_file().

        Returns None (with a warning) if the text cannot be located.
        """
        char_idx = full_text.find(exact_start_text)
        if char_idx == -1:
            # Graceful fallback: try stripping and searching the first 20 chars
            snippet = exact_start_text.strip()[:20]
            char_idx = full_text.find(snippet)
            if char_idx == -1:
                logger.warning(
                    "exact_start_text not found in full_text. snippet=%r", snippet
                )
                return None

        return self.get_time_from_index(char_idx, char_map)

    # ─────────────────────────────────────────────────────────────────────────
    # CORE HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _stitch(
        fragments: list[dict],
    ) -> tuple[str, list[tuple[int, float]]]:
        """
        Step 1 — Build full_text and char_to_time_map.

        char_to_time_map is a sorted list of (char_index, start_time_seconds)
        tuples.  Sorted order is guaranteed because we append in iteration order.
        """
        full_text = ""
        char_map: list[tuple[int, float]] = []

        for fragment in fragments:
            text = (fragment.get("text") or fragment.get("marathi_raw") or "").strip()
            if not text:
                continue

            current_char_length = len(full_text)           # absolute offset
            start_time = float(fragment.get("start_time", 0.0))
            char_map.append((current_char_length, start_time))   # record mapping

            full_text += text + " "                        # single space separator

        return full_text, char_map

    @staticmethod
    def get_time_from_index(
        char_index: int,
        char_map: list[tuple[int, float]],
    ) -> float:
        """
        Step 3 helper — Binary-search the char_map for a char_index.

        Finds the largest recorded char_index ≤ char_index (i.e., the fragment
        that was *in progress* at that position) and returns its start_time.

        Uses bisect_right on the sorted list of (char_index, start_time) tuples
        — comparing only the first element is default list behaviour in Python
        when all first elements are unique (which they are here).
        """
        if not char_map:
            return 0.0

        # Extract the char-index keys once for bisect (or use a view)
        keys = [entry[0] for entry in char_map]

        # bisect_right gives the insertion point AFTER any exact match
        pos = bisect.bisect_right(keys, char_index) - 1
        pos = max(pos, 0)   # clamp; never go negative

        return char_map[pos][1]

    def _resolve_chunk_timestamps(
        self,
        lc_chunks: list[Document],
        char_map: list[tuple[int, float]],
        video_id: str,
    ) -> list[dict[str, Any]]:
        """
        Step 3 — Attach exact YouTube timestamps to every LangChain chunk.
        Returns a list of clean dicts ready for the embedding step.
        """
        resolved: list[dict[str, Any]] = []
        for chunk in lc_chunks:
            text = chunk.page_content.strip()
            if not text:
                continue

            # LangChain guarantees start_index when add_start_index=True
            char_idx = chunk.metadata.get("start_index", 0)
            youtube_start = self.get_time_from_index(char_idx, char_map)

            resolved.append(
                {
                    "video_id": video_id,
                    "start_time": youtube_start,      # exact, zero-drift
                    "char_index": char_idx,           # kept for debugging
                    "marathi_raw": text,
                    "english_translated": "",          # filled in Colab by NLLB
                    "embedding_vector": [],            # filled in Colab by BGE-M3
                }
            )

        return resolved


# ── Convenience batch runner ─────────────────────────────────────────────────

def process_directory(
    input_dir: str = "data_pipeline/output",
    output_dir: str = "data_pipeline/processed_chunks",
) -> None:
    """
    Batch-process every raw .json in input_dir and save resolved chunk lists.
    Idempotent: skips files whose output already exists.
    """
    import glob

    os.makedirs(output_dir, exist_ok=True)
    processor = TranscriptProcessor()

    for filepath in glob.glob(os.path.join(input_dir, "*.json")):
        # Skip already-processed _enriched files in the same directory
        if "_enriched" in filepath or "_meta" in filepath:
            continue

        video_id = os.path.splitext(os.path.basename(filepath))[0]
        out_path = os.path.join(output_dir, f"{video_id}_chunks.json")

        if os.path.exists(out_path):
            logger.info("Skipping %s — chunks already exist.", video_id)
            continue

        logger.info("Processing %s …", video_id)
        chunks, _, _ = processor.process_file(filepath, video_id)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        logger.info("Saved %d chunks → %s", len(chunks), out_path)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s %(name)s — %(message)s",
    )
    process_directory()
