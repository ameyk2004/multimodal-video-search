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
    moral: Optional[str] = ""
    start_time_seconds: int = 0

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
    saint: Optional[str] = ""
    exact_start_text: Optional[str] = ""
    start_time_seconds: int = 0

class MusicListResponse(BaseModel):
    segments: List[MusicalSegmentItem]
