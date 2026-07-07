import json
import chromadb
from langchain_google_genai import ChatGoogleGenerativeAI
from src.models.policy_result import PolicyResult
from src.prompts.policy_agent import POLICY_AGENT_PROMPT
from src.utils.logger import get_logger

logger = get_logger(__name__)

_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2).with_structured_output(PolicyResult)
_chain = POLICY_AGENT_PROMPT | _llm

_chroma_client = chromadb.PersistentClient(path="chromadb")
_policies_collection = _chroma_client.get_collection("company_policies")


def _retrieve_chunks(actual_intent: str, query_category: str, subscription_tier: str) -> list[dict]:
    results = _policies_collection.query(
        query_texts=[actual_intent],
        n_results=3,
        where={"category": query_category},
        include=["documents", "metadatas", "distances"]
    )
    chunks = []
    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        applicable_tiers = json.loads(meta.get("applicable_tiers", "[]"))
        if subscription_tier not in applicable_tiers:
            continue
        chunks.append({"content": doc, "metadata": meta, "distance": distance})
    return chunks


def run_policy_agent(actual_intent: str, query_category: str, subscription_tier: str) -> PolicyResult:
    """
    Retrieves relevant company policies and assesses customer eligibility.

    Args:
        actual_intent (str): The customer's actual intent from the EnrichedQueryPackage.
        query_category (str): The ticket category used to filter ChromaDB results.
        subscription_tier (str): The customer's subscription tier for eligibility filtering.

    Returns:
        PolicyResult: Structured result containing eligibility, policy summary, and recommended action.
    """
    if not actual_intent or not actual_intent.strip():
        raise ValueError("actual_intent cannot be empty.")

    try:
        chunks = _retrieve_chunks(actual_intent, query_category, subscription_tier)
        logger.info(f"[Policy Agent] Retrieved {len(chunks)} policies for category '{query_category}', tier '{subscription_tier}'")

        return _chain.invoke({
            "actual_intent": actual_intent,
            "query_category": query_category,
            "subscription_tier": subscription_tier,
            "policy_chunks": json.dumps(chunks, indent=2)
        })

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"[Policy Agent] Failed for category '{query_category}', tier '{subscription_tier}': {e}")
        raise RuntimeError(f"Policy agent failed: {e}") from e