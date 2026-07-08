import os
os.environ["GOOGLE_API_KEY"] = "fake-key"

from unittest.mock import patch
from src.agents.level_1.query_synthesizer import QuerySynthesizerAgent
from src.models.intent import Intent
from src.models.customer_context import CustomerContext
from src.models.enriched_query import EnrichedQueryPackage

fake_intent = Intent(
    emotional_tone="frustrated",
    urgency="high",
    literal_query="I was charged twice",
    actual_intent="Customer wants a refund for duplicate charge",
    already_tried="Checked invoices"
)

fake_context = CustomerContext(
    customer_id="CUST_001",
    customer_name="John Doe",
    company="Acme Corp",
    subscription_tier="pro",
    team_size=10,
    account_health="good",
    past_tickets=[],
    context_summary="Pro tier customer."
)

fake_package = EnrichedQueryPackage(
    customer_id="CUST_001",
    customer_name="John Doe",
    company="Acme Corp",
    subscription_tier="pro",
    account_health="good",
    emotional_tone="frustrated",
    urgency="high",
    literal_query="I was charged twice",
    actual_intent="Customer wants a refund for duplicate charge",
    already_tried="Checked invoices",
    query_category="billing",
    priority_level="P1",
    escalation_flags=[],
    relevant_past_context="No prior ticket history on record.",
    suggested_layer2_agents=["policy_eligibility_agent", "action_response_agent"],
    enriched_brief="John Doe is a Pro tier customer at Acme Corp reporting a duplicate charge with high urgency."
)

def test_query_synthesizer():
    with patch("src.agents.level_1.query_synthesizer._chain") as mock_chain:
        mock_chain.invoke.return_value = fake_package

        result = QuerySynthesizerAgent(fake_intent, fake_context)

        assert result.query_category == "billing"
        assert result.priority_level == "P1"
        mock_chain.invoke.assert_called_once()