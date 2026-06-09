import json

def update_notebook():
    file_path = "data_pipeline/colab/pipeline.ipynb"
    with open(file_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
        
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            source = cell.get("source", [])
            
            # Check if this is Cell 9 (Embedding cell)
            is_embedding_cell = any("Step 2: Embed video transcript chunks on GPU" in line for line in source)
            if is_embedding_cell and not any("Step 3: Embed book chunks on GPU" in line for line in source):
                book_embedding_code = """
# ── Step 3: Embed book chunks on GPU ──
book_chunk_files = sorted(glob.glob("/content/repo/data_pipeline/books/processed_books_chunks/*_chunks.json"))
print(f"\\n🔢 Found {len(book_chunk_files)} book chunk files to process.")
for filepath in book_chunk_files:
    with open(filepath, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    
    needs_update = False
    print(f"🔄 Embedding chunks for {os.path.basename(filepath)}...")
    for chunk in chunks:
        if not chunk.get("embedding_vector"):
            chunk["embedding_vector"] = embedder.encode(chunk["marathi_raw"]).tolist()
            needs_update = True
    
    if needs_update:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        print(f"    ✅ Updated {len(chunks)} chunks with embeddings")
    else:
        print(f"    ⏭️ Skipped (already embedded)")
"""
                # Append the new code to the cell's source
                # Make sure it's properly split into lines with newlines
                new_lines = [line + "\n" if not line.endswith("\n") else line for line in book_embedding_code.strip("\n").split("\n")]
                source.append("\n")
                source.extend(new_lines)
                
            # Check if this is Cell 10 (Qdrant Upload cell)
            is_upload_cell = any("rebuild_hybrid_collection.py" in line for line in source)
            if is_upload_cell and not any("rebuild_books_collection.py" in line for line in source):
                source.append("!python scripts/qdrant/rebuild_books_collection.py\n")
                
            cell["source"] = source

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    update_notebook()
