from pydantic import BaseModel, Field
from typing import Literal


class EnrichedQueryPackage(BaseModel):
    customer_id: str = Field(..., description="Unique customer ID from CustomerContext.")
    customer_name: str = Field(..., description="Customer's full name from CustomerContext.")
    company: str = Field(..., description="Customer's company name from CustomerContext.")
    subscription_tier: Literal["free", "pro", "enterprise"] = Field(
        ...,
        description="Current subscription tier. Impacts policy eligibility, SLAs, and feature access."
    )
    account_health: Literal["good", "neutral", "at_risk"] = Field(
        ...,
        description="CRM churn risk signal. 'at_risk' indicates low usage, unpaid bills, or past issues."
    )

    # --- Query Intelligence (passed through from Intent) ---
    emotional_tone: Literal["angry", "frustrated", "confused", "urgent", "panicked", "neutral"] = Field(
        ...,
        description="Dominant emotional tone of the raw query. Used to calibrate response tone."
    )
    urgency: Literal["high", "medium", "low"] = Field(
        ...,
        description="Time-sensitivity based on deadlines, business impact, or work blockages."
    )
    literal_query: str = Field(
        ...,
        description="Cleaned, compressed single-sentence version of the customer's exact words."
    )
    actual_intent: str = Field(
        ...,
        description="The core underlying goal or need, which may differ from the literal wording."
    )
    already_tried: str = Field(
        ...,
        description="Steps the user already attempted. Defaults to 'Nothing mentioned'."
    )

    # --- Synthesized by Agent 3 ---
    query_category: Literal[
        "billing", "integration", "data_loss", "security",
        "feature_access", "account_access", "performance", "other"
    ] = Field(
        ...,
        description="Support ticket category derived from actual_intent, used for routing."
    )
    priority_level: Literal["P0", "P1", "P2", "P3"] = Field(
        ...,
        description="Computed routing priority (P0=highest, P3=lowest) based on worst-case combination of risk factors."
    )
    escalation_flags: list[Literal[
        "data_loss",
        "security_incident",
        "at_risk_account",
        "past_unresolved_ticket"
    ]] = Field(
        default_factory=list,
        description="Applicable system red flags (e.g., 'data_loss_category', 'security_incident'). Empty list if none."
    )
    relevant_past_context: str = Field(
        ...,
        description="Focused summary of relevant past tickets (IDs, issues, resolutions). State if no history or no relevance exists."
    )
    suggested_layer2_agents: list[Literal[
        "knowledge_base_agent",
        "policy_eligibility_agent",
        "action_response_agent"
    ]] = Field(
        ...,
        description="Target Layer 2 agents based on need. Include 'action_response_agent' unless purely informational."
    )
    enriched_brief: str = Field(
        ...,
        description="Dense 5-7 sentence handoff paragraph summarizing tier, health, intent, emotion, history, and risks."
    )