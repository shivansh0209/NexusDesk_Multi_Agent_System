import chromadb
import json
from src.models.customer_context import CustomerContext
from GenAI.NexusDesk.src.prompts.context_builder import CONTEXT_BUILDER_PROMPT
from src.utils.logger import get_logger
from langchain_google_genai import ChatGoogleGenerativeAI

logger = get_logger(__name__)

_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2).with_structured_output(CustomerContext)
_chain = CONTEXT_BUILDER_PROMPT | _llm

_chroma_client = chromadb.PersistentClient(path="chromadb")
_customer_collection = _chroma_client.get_collection("customer_profiles")
_tickets_collection = _chroma_client.get_collection("resolved_tickets")


def _fetch_customer_profile(customer_id: str) -> dict:
    result = _customer_collection.get(ids=[customer_id], include=["documents", "metadatas"])
    if not result["ids"]:
        raise ValueError(f"Customer {customer_id} not found.")
    return {
        "content": result["documents"][0],
        "metadata": result["metadatas"][0]
    }


def _fetch_past_tickets(ticket_ids: list[str]) -> list[dict]:
    if not ticket_ids:
        return []
    result = _tickets_collection.get(ids=ticket_ids, include=["documents", "metadatas"])
    return [
        {"id": id_,"content": doc, "metadata": meta}
        for id_, doc, meta in zip(result["ids"], result["documents"], result["metadatas"])
    ]


def ContextBuilderAgent(customer_id: str) -> CustomerContext:
    """
    Builds a structured customer context profile for downstream agents.
    Args:
        customer_id (str): The unique customer identifier.
    Returns:
        CustomerContext: A Pydantic model containing the full customer context.
    """
    try:
        customer_data = _fetch_customer_profile(customer_id)

        account_status = customer_data["metadata"].get("account_status")
        if account_status != "active":
            raise ValueError(f"Customer {customer_id} account is not active. Status: {account_status}")

        past_ticket_ids = json.loads(customer_data["metadata"].get("past_ticket_ids", "[]"))
        past_tickets_data = _fetch_past_tickets(past_ticket_ids)

        return _chain.invoke({
            "customer_profile": json.dumps(customer_data, indent=2),
            "past_tickets": json.dumps(past_tickets_data, indent=2)
        })

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Context building failed for customer {customer_id}: {e}")
        raise RuntimeError(f"Context building failed for customer {customer_id}: {e}") from e