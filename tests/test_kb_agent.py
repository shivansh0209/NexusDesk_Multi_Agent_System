import os
os.environ["GOOGLE_API_KEY"] = "fake-key"

from unittest.mock import patch
from src.agents.level_2.kb_agent import run_kb_agent
from src.models.kb_result import KBResult

fake_kb_result = KBResult(
    found=True,
    confidence="high",
    matched_ticket_ids=["TKT_001"],
    resolution_steps=["Step 1: Check billing", "Step 2: Issue refund"],
    resolution_summary="Duplicate charge confirmed, refund issued.",
    recommended_action="Issue full refund via admin billing panel.",
    caveat="Nothing mentioned"
)

def test_kb_agent():
    with patch("src.agents.level_2.kb_agent._tickets_collection") as mock_col, \
         patch("src.agents.level_2.kb_agent._chain") as mock_chain:

        mock_col.query.return_value = {
            "documents": [["Resolved duplicate charge by issuing refund."]],
            "metadatas": [[{"category": "billing", "subscription_tier": "pro"}]],
            "distances": [[0.12]]
        }
        mock_chain.invoke.return_value = fake_kb_result

        result = run_kb_agent("Refund for duplicate charge", "billing", "pro")

        assert result.found is True
        assert result.confidence == "high"
        mock_chain.invoke.assert_called_once()

def test_kb_agent_empty_intent_raises():
    try:
        run_kb_agent("", "billing", "pro")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass