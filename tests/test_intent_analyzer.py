import os
os.environ["GOOGLE_API_KEY"] = "fake-key"

from unittest.mock import patch
from src.agents.level_1.intent_analyzer import IntentAnalyzerAgent
from src.models.intent import Intent

def test_intent_analyzer():
    fake_intent = Intent(
        emotional_tone="frustrated",
        urgency="high",
        literal_query="I was charged twice",
        actual_intent="Customer wants a refund for a duplicate charge",
        already_tried="Checked invoices"
    )

    with patch("src.agents.level_1.intent_analyzer._chain") as mock_chain:
        mock_chain.invoke.return_value = fake_intent

        result = IntentAnalyzerAgent("I was charged twice this month")

        assert result.emotional_tone == "frustrated"
        assert result.urgency == "high"
        mock_chain.invoke.assert_called_once()