from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    user_id: str
    interests: List[str]
    essay_drafts: Optional[List[dict]] = []
    last_accessed: Optional[str] = None