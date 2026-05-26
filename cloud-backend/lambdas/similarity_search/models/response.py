from pydantic import BaseModel, Field
from typing import List

class SearchResultItem(BaseModel):
    video_id: str
    marathi_raw: str
    start_time: float
    score: float

class RelatedQueryItem(BaseModel):
    query: str
    type: str  # 'direct', 'tangential', 'wildcard'

class SearchResponse(BaseModel):
    query: str
    translated_query: str
    translation_error: str
    results: List[SearchResultItem]
    related_queries: List[RelatedQueryItem] = Field(default_factory=list)
