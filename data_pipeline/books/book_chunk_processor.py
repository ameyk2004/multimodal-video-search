"""
BookChunkProcessor — Zero-Drift Page Mapping Engine.

Responsibilities:
  1. Stitch raw PDF pages into one continuous string.
  2. Build an absolute char_to_page_map (character index → Page number).
  3. Split the stitched text into semantic chunks via LangChain with
     add_start_index=True so every chunk carries its exact origin offset.
  4. Resolve exact page numbers for chunks via binary search (bisect).
"""

import bisect
import json
import logging
import os
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class BookChunkProcessor:
    _SEPARATORS = ["\n\n", "\n", "॥", "।", ".", "?", "!", " "]
    _CHUNK_SIZE = 700
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

        with open(filepath, encoding="utf-8") as f:
            pages = json.load(f)

        full_text, char_map = self._stitch(pages)
        logger.info("Stitched %d pages → %d chars.", len(pages), len(full_text))

        doc = Document(page_content=full_text, metadata={"book_name": book_name})
        lc_chunks = self._splitter.split_documents([doc])
        logger.info("LangChain produced %d chunks.", len(lc_chunks))

        chunks = self._resolve_chunk_pages(lc_chunks, char_map, book_name)
        return chunks, char_map, full_text

    def resolve_story_page(
        self,
        exact_start_text: str,
        char_map: list[tuple[int, int, int]],
        full_text: str,
    ) -> int | None:
        char_idx = full_text.find(exact_start_text)
        if char_idx == -1:
            snippet = exact_start_text.strip()[:20]
            char_idx = full_text.find(snippet)
            if char_idx == -1:
                return None

        return self.get_page_from_index(char_idx, char_map)

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
            full_text += text + " "

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

    def _resolve_chunk_pages(
        self,
        lc_chunks: list[Document],
        char_map: list[tuple[int, int, int]],
        book_name: str,
    ) -> list[dict[str, Any]]:
        resolved: list[dict[str, Any]] = []
        for chunk in lc_chunks:
            text = chunk.page_content.strip()
            if not text:
                continue

            char_idx = chunk.metadata.get("start_index", 0)
            page_num = self.get_page_from_index(char_idx, char_map)

            resolved.append(
                {
                    "video_id": book_name,  # reusing field name for compatibility later if needed, but semantically book_name
                    "book_name": book_name,
                    "page_number": page_num,
                    "char_index": char_idx,
                    "marathi_raw": text,
                    "type": "book",
                    "embedding_vector": [],
                }
            )

        return resolved

def process_directory(
    input_dir: str = "data_pipeline/books/books_output",
    output_dir: str = "data_pipeline/books/processed_books_chunks",
):
    import glob
    os.makedirs(output_dir, exist_ok=True)
    processor = BookChunkProcessor()

    for filepath in glob.glob(os.path.join(input_dir, "*.json")):
        book_name = os.path.splitext(os.path.basename(filepath))[0]
        out_path = os.path.join(output_dir, f"{book_name}_chunks.json")

        if os.path.exists(out_path):
            logger.info("Skipping %s — chunks already exist.", book_name)
            continue

        logger.info("Processing %s …", book_name)
        chunks, _, _ = processor.process_file(filepath, book_name)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        logger.info("Saved %d chunks → %s", len(chunks), out_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    process_directory()
