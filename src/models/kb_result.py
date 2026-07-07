from pydantic import BaseModel, Field
from typing import Literal

class KBResult(BaseModel):
    found: bool = Field(..., description="Indicates whether a relevant knowledge base article was found at all or not.")
    confidence: Literal["high", "medium", "low", "none"] = Field(..., description="high: near-exact match. medium: related but not exact. low: loosely related. none: no useful match.")
    matched_ticket_ids: list[str] = Field(..., description="List of ticket IDs that matched the query.")
    resolution_steps: list[str] = Field(..., description="List of steps to resolve the issue.")
    resolution_summary: str = Field(..., description="A brief summary of the resolution.")
    recommended_action: str = Field(..., description="The concrete action the Action agent should take to help the customer based on the knowledge base article. ")
    caveat: str = Field(..., description="Any caveats or additional information the agent flagged as uncertain or incomplete.")