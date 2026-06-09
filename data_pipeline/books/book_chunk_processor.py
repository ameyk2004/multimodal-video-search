"""
BookChunkProcessor — Contextual Hierarchical Chunking Engine.

Responsibilities:
  1. Stitch raw PDF pages into one continuous string.
  2. Load LLM structural metadata (structure_type, topics).
  3. Dynamically slice the book into Chapters/Essays based on structure_type heuristics.
  4. Split those sections into semantic 1000-character chunks via LangChain.
  5. Prepend the rich Context Prefix to every single chunk.
  6. Resolve exact page numbers for chunks via binary search (bisect).
"""

import bisect
import json
import logging
import os
import re
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class BookChunkProcessor:
    _SEPARATORS = ["\n\n", "॥", "।", "\n", ".", "?", "!", " "]
    _CHUNK_SIZE = 1000
    _CHUNK_OVERLAP = 150

    def __init__(self) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            separators=self._SEPARATORS,
            chunk_size=self._CHUNK_SIZE,
            chunk_overlap=self._CHUNK_OVERLAP,
            add_start_index=True,
        )

    def process_file(
        self, filepath: str, book_name: str | None = None
    ) -> tuple[list[dict[str, Any]], list[tuple[int, int, int]], str]:
        if book_name is None:
            book_name = os.path.splitext(os.path.basename(filepath))[0]

        # 1. Load raw PDF pages
        with open(filepath, encoding="utf-8") as f:
            pages = json.load(f)

        full_text, char_map = self._stitch(pages)
        logger.info("Stitched %d pages → %d chars.", len(pages), len(full_text))

        # 2. Load enriched metadata from LLM step
        meta_path = os.path.join("data_pipeline/books/books_enriched_metadata", f"{book_name}_meta.json")
        metadata = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        else:
            logger.warning("No metadata found for %s! Falling back to continuous_text.", book_name)

        structure_type = metadata.get("structure_type", "continuous_text")
        topics = ", ".join(metadata.get("topics", []))
        
        # 3. Dynamically slice into sections
        sections = self._split_sections(full_text, structure_type)
        logger.info("Split into %d sections based on type '%s'", len(sections), structure_type)

        # 4. Process each section and add context
        chunks = []
        for sec_title, sec_text, sec_offset in sections:
            doc = Document(page_content=sec_text, metadata={"section_title": sec_title})
            lc_chunks = self._splitter.split_documents([doc])
            
            for chunk in lc_chunks:
                text = chunk.page_content.strip()
                if not text:
                    continue

                # Calculate absolute character index across the entire stitched book
                char_idx = sec_offset + chunk.metadata.get("start_index", 0)
                page_num = self.get_page_from_index(char_idx, char_map)

                # Inject Context Prefix
                context_prefix = f"पुस्तक: {book_name} | प्रकार: {structure_type}\n"
                if topics:
                    context_prefix += f"विषय: {topics}\n"
                context_prefix += f"भाग/लेख: {sec_title}\n\n"
                
                final_text = context_prefix + text

                chunks.append({
                    "video_id": book_name,  # reusing field name for compatibility
                    "book_name": book_name,
                    "page_number": page_num,
                    "char_index": char_idx,
                    "marathi_raw": final_text,
                    "type": "book",
                    "embedding_vector": [],
                })

        logger.info("Generated %d contextual chunks for %s.", len(chunks), book_name)
        return chunks, char_map, full_text

    def _split_sections(self, full_text: str, structure_type: str) -> list[tuple[str, str, int]]:
        """Returns list of (section_title, section_text, absolute_start_index)"""
        sections = []
        
        if structure_type == "numbered_essays":
            # Matches "२७. स्वतःशी तसं इतरांशी" at start of line
            pattern = r"(?m)^(?:\d+|[१२३४५६७८९०]+)\.\s+(.+)$"
        elif structure_type == "chapters":
            # Matches "अध्याय १" or "प्रकरण ५" at start of line
            pattern = r"(?m)^(?:अध्याय|प्रकरण)\s+(.+)$"
        else:
            return [("संपूर्ण पुस्तक", full_text, 0)]
            
        matches = list(re.finditer(pattern, full_text))
        if not matches:
            return [("संपूर्ण पुस्तक", full_text, 0)]
            
        # Add the front-matter (Preface, Index) before the first chapter
        if matches[0].start() > 0:
            sections.append(("प्रस्तावना / अनुक्रमणिका", full_text[:matches[0].start()], 0))
            
        for i in range(len(matches)):
            start_idx = matches[i].start()
            # The title is the full matched line
            title = matches[i].group(0).strip()
            if len(title) > 100: 
                title = title[:100] + "..."
            
            end_idx = matches[i+1].start() if i + 1 < len(matches) else len(full_text)
            section_text = full_text[start_idx:end_idx]
            sections.append((title, section_text, start_idx))
            
        return sections

    @staticmethod
    def _stitch(
        pages: list[dict],
    ) -> tuple[str, list[tuple[int, int, int]]]:
        """
        char_to_page_map is a list of:
        (char_index, page_number, text_length)
        """
        full_text = ""
        char_map: list[tuple[int, int, int]] = []

        for page in pages:
            text = (page.get("text") or "").strip()
            if not text:
                continue

            current_char_length = len(full_text)
            page_num = int(page.get("page_number", 0))
            text_len = len(text)
            
            char_map.append((current_char_length, page_num, text_len))
            # Use double newline to preserve page breaks/paragraph breaks during Langchain splitting
            full_text += text + "\n\n"

        return full_text, char_map

    @staticmethod
    def get_page_from_index(
        char_index: int,
        char_map: list[tuple[int, int, int]],
    ) -> int:
        if not char_map:
            return 0

        keys = [entry[0] for entry in char_map]
        pos = bisect.bisect_right(keys, char_index) - 1
        pos = max(pos, 0)

        _, page_num, _ = char_map[pos]
        return page_num


def process_directory(
    input_dir: str = "data_pipeline/books/books_output",
    output_dir: str = "data_pipeline/books/processed_books_chunks",
):
    import glob
    os.makedirs(output_dir, exist_ok=True)
    processor = BookChunkProcessor()

    raw_files = glob.glob(os.path.join(input_dir, "*.json"))
    if not raw_files:
        logger.info("No files found in %s", input_dir)
        return

    for filepath in raw_files:
        book_name = os.path.splitext(os.path.basename(filepath))[0]
        out_path = os.path.join(output_dir, f"{book_name}_chunks.json")

        logger.info("Contextual Chunking %s …", book_name)
        chunks, _, _ = processor.process_file(filepath, book_name)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        logger.info("Saved %d smart chunks → %s", len(chunks), out_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    process_directory()
