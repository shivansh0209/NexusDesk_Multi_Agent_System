import json
import chromadb
from langchain_google_genai import ChatGoogleGenerativeAI
from src.models.kb_result import KBResult
from src.prompts.kb_query import KB_AGENT_PROMPT
from src.utils.logger import get_logger

logger = get_logger(__name__)

_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2).with_structured_output(KBResult)
_chain = KB_AGENT_PROMPT | _llm

_chroma_client = chromadb.PersistentClient(path="chromadb")
_tickets_collection = _chroma_client.get_collection("resolved_tickets")


def _retrieve_chunks(actual_intent: str, query_category: str, subscription_tier: str) -> list[dict]:
    results = _tickets_collection.query(
        query_texts=[actual_intent],
        n_results=3,
        where={"category": query_category, "subscription_tier": subscription_tier},
        include=["documents", "metadatas", "distances"]
    )
    chunks = []
    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunks.append({"content": doc, "metadata": meta, "distance": distance})
    return chunks


def run_kb_agent(actual_intent: str, query_category: str, subscription_tier: str) -> KBResult:
    """
    Retrieves relevant knowledge base chunks and extracts a structured resolution.

    Args:
        actual_intent (str): The customer's actual intent from the EnrichedQueryPackage.
        query_category (str): The ticket category used to filter ChromaDB results.
        subscription_tier (str): The customer's subscription tier for relevance filtering.

    Returns:
        KBResult: Structured result containing resolution steps, confidence, and caveats.
    """
    if not actual_intent or not actual_intent.strip():
        raise ValueError("actual_intent cannot be empty.")

    try:
        chunks = _retrieve_chunks(actual_intent, query_category, subscription_tier)
        logger.info(f"[KB Agent] Retrieved {len(chunks)} chunks for category '{query_category}'")

        return _chain.invoke({
            "actual_intent": actual_intent,
            "query_category": query_category,
            "subscription_tier": subscription_tier,
            "kb_chunks": json.dumps(chunks, indent=2)
        })

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"[KB Agent] Failed for intent '{actual_intent}': {e}")
        raise RuntimeError(f"KB agent failed: {e}") from e