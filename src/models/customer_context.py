from pydantic import BaseModel, Field
from typing import Literal

class PastTicketSummary(BaseModel):
    ticket_id: str = Field(..., description="The ticket ID")
    category: str = Field(..., description="Category of the past ticket")
    resolution_summary: str = Field(..., description="Brief summary of how it was resolved")
    was_successful: bool = Field(..., description="Whether the resolution was successful")

class CustomerContext(BaseModel):
    customer_id: str = Field(..., description="Unique customer identifier")
    customer_name: str = Field(..., description="Name of the customer")
    company: str = Field(..., description="Company the customer belongs to")
    subscription_tier: Literal["free", "pro", "enterprise"] = Field(..., description="Current subscription tier")
    team_size: int = Field(..., description="Number of team members on the account")
    account_health: Literal["good", "neutral", "at_risk"] = Field(..., description="Current account health status")
    past_tickets: list[PastTicketSummary] = Field(default_factory=list, description="Summaries of past support tickets")
    context_summary: str = Field(..., description="A synthesized natural language summary of the customer context for downstream agents")