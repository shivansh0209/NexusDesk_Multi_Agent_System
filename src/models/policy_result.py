from pydantic import BaseModel, Field
from typing import Literal


class PolicyResult(BaseModel):
    found: bool = Field(..., description="True if a relevant policy was found for this query category and subscription tier.")
    confidence: Literal["high", "medium", "low", "none"] = Field(..., description="high: exact category and tier match. medium: related policy, partially applicable. low: loosely related. none: no useful match.")
    matched_policy_ids: list[str] = Field(default_factory=list, description="IDs of the policies used. Empty list if found is False.")
    is_eligible: bool = Field(..., description="Whether the customer is entitled to what they are requesting based on their subscription tier and the matched policy.")
    policy_summary: str = Field(..., description="One to two sentences summarizing what the relevant policy says and how it applies to this customer. Empty string if found is False.")
    recommended_action: str = Field(..., description="The concrete action the Action agent should take based on this policy. " )
    caveat: str = Field(..., description="Any conditions, edge cases, or restrictions that limit eligibility or affect the recommended action. 'None' if no caveats apply.")