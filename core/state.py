#state.py
from pydantic import BaseModel, Field
from typing import List, Optional

class TripState(BaseModel):
    destination: Optional[str] = None
    origin: Optional[str] = None
    duration: Optional[str] = None
    dates: Optional[str] = None
    travelers: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)
    preferences: List[str] = Field(default_factory=list)
    readiness: str = "Discovery"
    hotel_preference: Optional[str] = None
    budget: Optional[str] = None
    open_questions: List[str] = Field(default_factory=list)

    def to_compact_prompt(self) -> str:
        return f"""Current Trip State:
- Destination: {self.destination}
- Origin: {self.origin}
- Duration: {self.duration}
- Dates: {self.dates}
- Travelers: {self.travelers}
- Constraints: {', '.join(self.constraints) if self.constraints else 'None'}
- Preferences: {', '.join(self.preferences) if self.preferences else 'None'}
- Readiness: {self.readiness}
- Hotel preference: {self.hotel_preference}
- Budget: {self.budget}
"""
