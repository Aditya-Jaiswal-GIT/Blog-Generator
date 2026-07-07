from typing import TypedDict

class BlogState(TypedDict):
    topic: str
    research_notes: str
    article: str
    editor_feedback: str
    human_feedback: str
    is_approved: bool
    current_stage: str