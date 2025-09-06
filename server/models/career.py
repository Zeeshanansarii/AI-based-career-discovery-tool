from pydantic import BaseModel
from typing import List

class Career(BaseModel):
    title: str
    description: str
    skills: List[str]
    industry: str
    vector: List[float] # FAISS indexing