from pydantic import BaseModel, Field
from typing import List, Optional

class SearchResultItem(BaseModel):
    marathi_raw: str
    score: float
    type: str = "video"  # "video" or "book"
    video_id: Optional[str] = None
    start_time: Optional[float] = None
    book_name: Optional[str] = None
    page_number: Optional[int] = None

class RelatedQueryItem(BaseModel):
    query: str
    type: str  # 'direct', 'tangential', 'wildcard'

class SearchResponse(BaseModel):
    query: str
    translated_query: str
    translation_error: str
    results: List[SearchResultItem]
    related_queries: List[RelatedQueryItem] = Field(default_factory=list)
