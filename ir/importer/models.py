from dataclasses import dataclass
from typing import Optional


@dataclass
class NoteModel:
    title: str
    content: str
    url: str
    priority: Optional[str]
