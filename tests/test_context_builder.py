import os
os.environ["GOOGLE_API_KEY"] = "fake-key"

from unittest.mock import patch
from src.agents.level_1.context_builder import ContextBuilderAgent
from src.models.customer_context import CustomerContext, PastTicketSummary

fake_context = CustomerContext(
    customer_id="CUST_001",
    customer_name="John Doe",
    company="Acme Corp",
    subscription_tier="pro",
    team_size=10,
    account_health="good",
    past_tickets=[],
    context_summary="Pro tier customer with good account health and no past tickets."
)

def test_context_builder():
    with patch("src.agents.level_1.context_builder._customer_collection") as mock_customers, \
         patch("src.agents.level_1.context_builder._tickets_collection"), \
         patch("src.agents.level_1.context_builder._chain") as mock_chain:

        mock_customers.get.return_value = {
            "ids": ["CUST_001"],
            "documents": ["John Doe at Acme Corp"],
            "metadatas": [{"account_status": "active", "past_ticket_ids": "[]"}]
        }
        mock_chain.invoke.return_value = fake_context

        result = ContextBuilderAgent("CUST_001")

        assert result.customer_id == "CUST_001"
        assert result.subscription_tier == "pro"
        mock_chain.invoke.assert_called_once()

def test_context_builder_inactive_account():
    with patch("src.agents.level_1.context_builder._customer_collection") as mock_customers:
        mock_customers.get.return_value = {
            "ids": ["CUST_002"],
            "documents": ["Jane"],
            "metadatas": [{"account_status": "inactive", "past_ticket_ids": "[]"}]
        }
        try:
            ContextBuilderAgent("CUST_002")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass