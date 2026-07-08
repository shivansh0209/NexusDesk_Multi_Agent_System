# No LLM involved — pure logic, no mock needed
from src.agents.level_1.level1_superviser import Layer1Supervisor
from src.models.enriched_query import EnrichedQueryPackage

def _make_package(**overrides):
    base = dict(
        customer_id="CUST_001", customer_name="John Doe", company="Acme",
        subscription_tier="pro", account_health="good",
        emotional_tone="neutral", urgency="medium",
        literal_query="I was charged twice",
        actual_intent="Refund for duplicate charge",
        already_tried="Nothing", query_category="billing",
        priority_level="P1", escalation_flags=[],
        relevant_past_context="None", enriched_brief="Brief here.",
        suggested_layer2_agents=["policy_eligibility_agent", "action_response_agent"]
    )
    base.update(overrides)
    return EnrichedQueryPackage(**base)

def test_routes_to_layer2():
    package = _make_package()
    result = Layer1Supervisor(package)
    assert result["destination"] == "layer2"

def test_p0_routes_to_layer3():
    package = _make_package(priority_level="P0")
    result = Layer1Supervisor(package)
    assert result["destination"] == "layer3"

def test_critical_flag_routes_to_layer3():
    package = _make_package(escalation_flags=["security_incident"])
    result = Layer1Supervisor(package)
    assert result["destination"] == "layer3"