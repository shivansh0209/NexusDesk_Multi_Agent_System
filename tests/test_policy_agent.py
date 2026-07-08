import os
os.environ["GOOGLE_API_KEY"] = "fake-key"

import json
from unittest.mock import patch
from src.agents.level_2.policy_agent import run_policy_agent
from src.models.policy_result import PolicyResult

fake_policy_result = PolicyResult(
    found=True,
    confidence="high",
    matched_policy_ids=["POL_001"],
    is_eligible=True,
    policy_summary="Pro tier customers are eligible for full refunds within 30 days.",
    recommended_action="Issue full refund via admin billing panel.",
    caveat="Refund only applicable within 30-day window."
)

def test_policy_agent():
    with patch("src.agents.level_2.policy_agent._policies_collection") as mock_col, \
         patch("src.agents.level_2.policy_agent._chain") as mock_chain:

        mock_col.query.return_value = {
            "documents": [["Pro customers eligible for full refund within 30 days."]],
            "metadatas": [[{"category": "billing", "applicable_tiers": json.dumps(["pro", "enterprise"])}]],
            "distances": [[0.10]]
        }
        mock_chain.invoke.return_value = fake_policy_result

        result = run_policy_agent("Refund for duplicate charge", "billing", "pro")

        assert result.is_eligible is True
        assert result.found is True
        mock_chain.invoke.assert_called_once()

def test_policy_agent_empty_intent_raises():
    try:
        run_policy_agent("", "billing", "pro")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass