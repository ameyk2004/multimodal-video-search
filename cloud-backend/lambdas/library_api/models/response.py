from pydantic import BaseModel, Field
from typing import List, Optional

# For GET /videos
class LibraryVideoSummary(BaseModel):
    video_id: str
    title: str = "प्रवचन"
    topics: List[str] = Field(default_factory=list)
    topic_count: int = 0
    query_count: int = 0

class VideosListResponse(BaseModel):
    videos: List[LibraryVideoSummary]

# For GET /videos/{video_id}
class VerseItem(BaseModel):
    verse_text: str
    source_or_author: Optional[str] = ""

class StorySummary(BaseModel):
    title: str
    title_english: Optional[str] = ""
    moral: Optional[str] = ""
    start_time_seconds: int = 0
    end_time_seconds: int = 0

class VideoDetailResponse(BaseModel):
    video_id: str
    title: str = "प्रवचन"
    topics: List[str] = Field(default_factory=list)
    queries: List[str] = Field(default_factory=list)
    practices: List[str] = Field(default_factory=list)
    verses: List[VerseItem] = Field(default_factory=list)
    stories: List[StorySummary] = Field(default_factory=list)

# For GET /music
class MusicalSegmentItem(BaseModel):
    video_id: str
    type: str
    name: str
    name_english: Optional[str] = ""
    saint: Optional[str] = ""
    saint_english: Optional[str] = ""
    exact_start_text: Optional[str] = ""
    start_time_seconds: int = 0
    end_time_seconds: int = 0

class MusicListResponse(BaseModel):
    segments: List[MusicalSegmentItem]

# For GET /books
class LibraryBookSummary(BaseModel):
    video_id: str
    title: str = "अज्ञात पुस्तक"
    author: str = "अज्ञात"
    topics: List[str] = Field(default_factory=list)
    question_count: int = 0
    mood: str = ""

class BooksListResponse(BaseModel):
    books: List[LibraryBookSummary]

class BookDetailResponse(BaseModel):
    video_id: str
    title: str = "अज्ञात पुस्तक"
    author: str = "अज्ञात"
    date_written: str = "अज्ञात"
    summary: str = ""
    for_whom: str = ""
    mood: str = ""
    structure_type: str = ""
    topics: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)
    key_learnings: List[str] = Field(default_factory=list)
    table_of_contents: list = Field(default_factory=list)
