import os
os.environ["GOOGLE_API_KEY"] = "fake-key"

from unittest.mock import patch
from main import run_nexusdesk
from src.models.intent import Intent
from src.models.customer_context import CustomerContext
from src.models.enriched_query import EnrichedQueryPackage
from src.models.kb_result import KBResult
from src.models.policy_result import PolicyResult
from src.models.action_result import ActionResult

# ─── Shared Fakes ───────────────────────────

fake_intent = Intent(
    emotional_tone="frustrated", urgency="high",
    literal_query="I was charged twice",
    actual_intent="Refund for duplicate charge",
    already_tried="Checked invoices"
)

fake_context = CustomerContext(
    customer_id="CUST_001", customer_name="John Doe", company="Acme",
    subscription_tier="pro", team_size=10, account_health="good",
    past_tickets=[], context_summary="Pro tier customer."
)

def _make_package(**overrides):
    base = dict(
        customer_id="CUST_001", customer_name="John Doe", company="Acme",
        subscription_tier="pro", account_health="good",
        emotional_tone="frustrated", urgency="high",
        literal_query="I was charged twice",
        actual_intent="Refund for duplicate charge",
        already_tried="Checked invoices", query_category="billing",
        priority_level="P1", escalation_flags=[],
        relevant_past_context="None", enriched_brief="Brief.",
        suggested_layer2_agents=["knowledge_base_agent", "policy_eligibility_agent", "action_response_agent"]
    )
    base.update(overrides)
    return EnrichedQueryPackage(**base)

fake_kb = KBResult(
    found=True, confidence="high", matched_ticket_ids=["TKT_001"],
    resolution_steps=["Issue refund"], resolution_summary="Refund issued.",
    recommended_action="Issue refund via admin panel.", caveat="Nothing mentioned"
)

fake_policy = PolicyResult(
    found=True, confidence="high", matched_policy_ids=["POL_001"],
    is_eligible=True, policy_summary="Pro tier eligible for refund.",
    recommended_action="Issue refund.", caveat="Within 30 days."
)

fake_action_resolved = ActionResult(
    resolution_confidence="high", requires_human=False,
    system_action="Issue full refund via admin billing panel.",
    response_draft="Hi John, your refund has been processed.",
    reasoning="KB and Policy both confirmed eligibility with high confidence."
)

fake_action_needs_human = ActionResult(
    resolution_confidence="low", requires_human=True,
    system_action="None",
    response_draft="Hi John, we are escalating this to a senior agent.",
    reasoning="Low confidence — KB had no match."
)

# ─── Helper to patch all Layer 1 + 2 agents ─

def _patch_all(package, kb=None, policy=None, action=None):
    """Returns a context manager stack that wires up all agents."""
    return [
        patch("main.IntentAnalyzerAgent", return_value=fake_intent),
        patch("main.ContextBuilderAgent", return_value=fake_context),
        patch("main.QuerySynthesizerAgent", return_value=package),
        patch("main.run_kb_agent", return_value=kb or fake_kb),
        patch("main.run_policy_agent", return_value=policy or fake_policy),
        patch("main.run_action_agent", return_value=action or fake_action_resolved),
    ]


# ─── Tests ───────────────────────────────────

def test_happy_path_resolves():
    """Full pipeline resolves successfully with high confidence."""
    patches = _patch_all(package=_make_package())
    with patch("main.IntentAnalyzerAgent", return_value=fake_intent), \
         patch("main.ContextBuilderAgent", return_value=fake_context), \
         patch("main.QuerySynthesizerAgent", return_value=_make_package()), \
         patch("main.run_kb_agent", return_value=fake_kb), \
         patch("main.run_policy_agent", return_value=fake_policy), \
         patch("main.run_action_agent", return_value=fake_action_resolved):

        result = run_nexusdesk("CUST_001", "I was charged twice")

        assert result["status"] == "resolved"
        assert result["customer_id"] == "CUST_001"
        assert "response_draft" in result
        assert "system_action" in result


def test_l1_supervisor_escalates_p0_to_layer3():
    """P0 priority should skip Layer 2 entirely and go to human handoff."""
    with patch("main.IntentAnalyzerAgent", return_value=fake_intent), \
         patch("main.ContextBuilderAgent", return_value=fake_context), \
         patch("main.QuerySynthesizerAgent", return_value=_make_package(priority_level="P0")), \
         patch("main.run_kb_agent") as mock_kb:

        result = run_nexusdesk("CUST_001", "We have a security breach")

        assert result["status"] == "escalated_to_human"
        assert result["priority"] == "P0"
        mock_kb.assert_not_called()  # Layer 2 should never run


def test_l1_supervisor_escalates_critical_flag_to_layer3():
    """Critical escalation flag should trigger human handoff from L1 Supervisor."""
    with patch("main.IntentAnalyzerAgent", return_value=fake_intent), \
         patch("main.ContextBuilderAgent", return_value=fake_context), \
         patch("main.QuerySynthesizerAgent", return_value=_make_package(escalation_flags=["security_incident"])), \
         patch("main.run_kb_agent") as mock_kb:

        result = run_nexusdesk("CUST_001", "Someone accessed my account")

        assert result["status"] == "escalated_to_human"
        mock_kb.assert_not_called()


def test_l2_supervisor_escalates_low_confidence_to_layer3():
    """Low confidence action result should escalate to human from L2 Supervisor."""
    with patch("main.IntentAnalyzerAgent", return_value=fake_intent), \
         patch("main.ContextBuilderAgent", return_value=fake_context), \
         patch("main.QuerySynthesizerAgent", return_value=_make_package()), \
         patch("main.run_kb_agent", return_value=fake_kb), \
         patch("main.run_policy_agent", return_value=fake_policy), \
         patch("main.run_action_agent", return_value=fake_action_needs_human):

        result = run_nexusdesk("CUST_001", "I was charged twice")

        assert result["status"] == "escalated_to_human"
        assert result["draft_for_agent"] is not None  # draft should still be passed to human


def test_layer1_domain_error_returns_error_status():
    """Inactive account or missing customer should return error, not crash."""
    with patch("main.IntentAnalyzerAgent", return_value=fake_intent), \
         patch("main.ContextBuilderAgent", side_effect=ValueError("Customer CUST_999 not found.")):

        result = run_nexusdesk("CUST_999", "I need help")

        assert result["status"] == "error"
        assert "CUST_999" in result["message"]


def test_kb_agent_failure_is_non_fatal():
    """If KB agent crashes, pipeline should still resolve using policy result alone."""
    with patch("main.IntentAnalyzerAgent", return_value=fake_intent), \
         patch("main.ContextBuilderAgent", return_value=fake_context), \
         patch("main.QuerySynthesizerAgent", return_value=_make_package()), \
         patch("main.run_kb_agent", side_effect=RuntimeError("ChromaDB unavailable")), \
         patch("main.run_policy_agent", return_value=fake_policy), \
         patch("main.run_action_agent", return_value=fake_action_resolved):

        result = run_nexusdesk("CUST_001", "I was charged twice")

        assert result["status"] == "resolved"


def test_both_agents_failing_triggers_handoff():
    """If both KB and Policy crash, pipeline should fall back to human handoff."""
    with patch("main.IntentAnalyzerAgent", return_value=fake_intent), \
         patch("main.ContextBuilderAgent", return_value=fake_context), \
         patch("main.QuerySynthesizerAgent", return_value=_make_package()), \
         patch("main.run_kb_agent", side_effect=RuntimeError("KB down")), \
         patch("main.run_policy_agent", side_effect=RuntimeError("Policy down")):

        result = run_nexusdesk("CUST_001", "I was charged twice")

        assert result["status"] == "escalated_to_human"