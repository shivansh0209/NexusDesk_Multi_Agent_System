from pydantic import BaseModel, Field
from typing import Literal


class ActionResult(BaseModel):
    resolution_confidence: Literal["high", "medium", "low"] = Field(
        ...,
        description=(
            "Overall confidence in this resolution. "
            "high: both KB and Policy (where applicable) returned confident results and the response is complete. "
            "medium: one source was uncertain or missing, response is likely correct but not guaranteed. "
            "low: significant gaps in KB or Policy results, response is best-effort. "
            "Used by the L2 Supervisor to decide whether to send or escalate."
        )
    )
    requires_human: bool = Field(
        ..., 
        description=(
            "True if this ticket should be escalated to a human agent despite a response being drafted. "
            "Set to True when: resolution_confidence is low, policy explicitly requires human involvement, "
            "or the issue involves security, data loss, or enterprise-tier risk signals."
        )
    )
    system_action: str = Field(
        ...,
        description=(
            "The concrete system action that must be executed alongside or before the response. "
            "Examples: 'Issue refund via admin billing panel', 'Apply promo code PROTRIAL14 to account', "
            "'Force logout all active sessions', 'Escalate to Tier 2 engineering'. "
            "'None' if the resolution is informational only and no system action is required."
        )
    )
    response_draft: str = Field(
        ...,
        description=(
            "The complete customer-facing response to be sent. "
            "Must be professional, empathetic, and specific to this customer's issue. "
            "Must not reference internal systems, ticket IDs, agent names, or policy document IDs. "
            "Must reflect the customer's emotional tone — warmer for frustrated/panicked, direct for neutral/urgent."
        )
    )
    reasoning: str = Field(
        ...,
        description=(
            "One to two sentences explaining why this response and action were chosen. "
            "For the L2 Supervisor — not customer-facing. "
            "Must reference which inputs drove the decision (KB result, policy eligibility, confidence levels)."
        )
    )