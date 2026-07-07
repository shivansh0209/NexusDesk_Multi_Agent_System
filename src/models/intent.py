from pydantic import BaseModel, Field, field_validator
from typing import Literal

class Intent(BaseModel):
    emotional_tone: Literal["angry", "frustrated", "confused", "urgent", "panicked", "neutral"] = Field(..., description="Emotional tone of the customer query")
    urgency: Literal["high", "medium", "low"] = Field(..., description="Urgency level of the request")
    literal_query: str = Field(..., description="What the customer literally said")
    actual_intent: str = Field(..., description="What the customer actually wants beyond what they said")
    already_tried: str = Field(..., description="Steps the customer has already attempted before reaching out")