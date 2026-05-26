from pydantic import BaseModel, Field
from typing import List, Optional

class StoryItem(BaseModel):
    video_id: str
    title: str
    moral: Optional[str] = ""
    character_or_saint: Optional[str] = ""
    normalized_saint_name: Optional[str] = ""
    associated_topics: List[str] = Field(default_factory=list)
    exact_start_text: Optional[str] = ""
    start_time_seconds: int = 0
    thumbnail_url: str
    youtube_url: str

class StoriesResponse(BaseModel):
    stories: List[StoryItem]
