# No LLM — pure logic
from src.agents.level_2.level2_superviser import layer2_superviser_response
from src.models.action_result import ActionResult

def _make_result(**overrides):
    base = dict(
        resolution_confidence="high",
        requires_human=False,
        system_action="Issue refund.",
        response_draft="Hi John, your refund has been processed.",
        reasoning="High confidence from KB and Policy."
    )
    base.update(overrides)
    return ActionResult(**base)

def test_resolves_to_customer():
    result = layer2_superviser_response(_make_result())
    assert result["destination"] == "layer2"
    assert "response" in result

def test_low_confidence_escalates():
    result = layer2_superviser_response(_make_result(resolution_confidence="low"))
    assert result["destination"] == "layer3"

def test_requires_human_escalates():
    result = layer2_superviser_response(_make_result(requires_human=True))
    assert result["destination"] == "layer3"