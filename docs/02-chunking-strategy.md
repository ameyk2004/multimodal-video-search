# Chunking Strategy for Marathi Transcripts

## The Problem
When extracting transcripts directly from YouTube (especially using `yt-dlp` or `youtube-transcript-api`), the resulting output often consists of tiny, fragmented segments. These segments can be as small as 1 to 3 words and usually lack punctuation.

If we pass these small, isolated words directly to a translation model or an embedding model, we face significant issues:
1. **Context Loss:** LLMs translate *ideas*, not words. A single word lacks the necessary context, resulting in literal and often incorrect translations.
2. **Poor Semantic Search:** Embeddings rely on rich context to match meaning. Searching for a concept will fail if the vector represents a single meaningless word rather than a complete thought.
3. **API Cost:** Hitting LLM APIs for every 2-second fragment is highly inefficient and expensive.

## The Solution: Hybrid Chunking Strategy

To resolve this, we employ a **Hybrid Chunking approach (Minimum Duration + Pause Detection)** inside `data_pipeline/chunker.py`.

### 1. Minimum Chunk Duration
We aggregate words continuously until a minimum accumulated duration is met (e.g., 30 seconds). This ensures every chunk has enough context for the LLM to understand the overarching thought.

### 2. Pause-Based Boundaries
Once the minimum duration is met, we do not cut the chunk abruptly. Instead, the chunker calculates the pause between the end time of the current word and the start time of the next word. 

If this pause exceeds our defined threshold (e.g., `1.0` seconds), it indicates that the speaker likely took a breath, paused, or finished a sentence. We use this natural gap as the boundary to finalize the chunk.

## Pipeline Integration
1. **Fetch:** `YouTubeTranscriptManager` pulls raw, word-level JSON.
2. **Chunk:** `TranscriptChunker` aggregates these into 30-60 second contextual blocks, saving the result as `_chunked.json`.
3. **Translate & Format (Cloud step):** We take these rich chunks and pass them to our Colab GPU environment (via an LLM) to get perfectly punctuated sentences and high-accuracy English translations.
4. **Embed (Cloud step):** The translated chunk is appended with video metadata (e.g., Title) and embedded for multimodal search.

This enterprise-grade chunking setup guarantees that our embeddings capture rich semantic intent and boundaries align with natural speech.
