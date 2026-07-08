import os
os.environ["GOOGLE_API_KEY"] = "fake-key"

from unittest.mock import patch
from src.agents.level_2.action_agent import run_action_agent
from src.models.action_result import ActionResult
from src.models.kb_result import KBResult
from src.models.policy_result import PolicyResult
from src.models.enriched_query import EnrichedQueryPackage

fake_action_result = ActionResult(
    resolution_confidence="high",
    requires_human=False,
    system_action="Issue full refund via admin billing panel.",
    response_draft="Hi John, we've confirmed the duplicate charge and issued a full refund.",
    reasoning="KB and Policy both confirmed eligibility with high confidence."
)

fake_package = EnrichedQueryPackage(
    customer_id="CUST_001", customer_name="John Doe", company="Acme",
    subscription_tier="pro", account_health="good",
    emotional_tone="frustrated", urgency="high",
    literal_query="Charged twice", actual_intent="Refund for duplicate charge",
    already_tried="Checked invoices", query_category="billing",
    priority_level="P1", escalation_flags=[],
    relevant_past_context="None", enriched_brief="Brief.",
    suggested_layer2_agents=["policy_eligibility_agent", "action_response_agent"]
)

fake_kb = KBResult(
    found=True, confidence="high", matched_ticket_ids=["TKT_001"],
    resolution_steps=["Issue refund"], resolution_summary="Refund issued.",
    recommended_action="Issue refund.", caveat="Nothing mentioned"
)

fake_policy = PolicyResult(
    found=True, confidence="high", matched_policy_ids=["POL_001"],
    is_eligible=True, policy_summary="Pro tier eligible for refund.",
    recommended_action="Issue refund.", caveat="Within 30 days."
)

def test_action_agent():
    with patch("src.agents.level_2.action_agent._chain") as mock_chain:
        mock_chain.invoke.return_value = fake_action_result

        result = run_action_agent(fake_package, fake_kb, fake_policy)

        assert result.resolution_confidence == "high"
        assert result.requires_human is False
        mock_chain.invoke.assert_called_once()

def test_action_agent_raises_if_no_inputs():
    try:
        run_action_agent(fake_package, None, None)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass