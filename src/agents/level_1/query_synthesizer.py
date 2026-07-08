from src.models.intent import Intent
from src.models.customer_context import CustomerContext
from src.models.enriched_query import EnrichedQueryPackage
from src.prompts.query_synthesis import QUERY_SYNTHESIS_PROMPT
from src.utils.logger import get_logger
from langchain_google_genai import ChatGoogleGenerativeAI
import json

logger = get_logger(__name__)

_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2).with_structured_output(EnrichedQueryPackage)
_chain = QUERY_SYNTHESIS_PROMPT | _llm


def QuerySynthesizerAgent(intent: Intent, customer_context: CustomerContext) -> EnrichedQueryPackage:
    """
    Synthesizes the Intent and CustomerContext into a unified EnrichedQueryPackage
    for downstream Layer 1 Supervisor routing and Layer 2 resolution.

    Args:
        intent (Intent): The analyzed intent from the Intent Analyzer agent.
        customer_context (CustomerContext): The customer context from the Context Builder agent.

    Returns:
        EnrichedQueryPackage: A fully enriched query package ready for the Layer 1 Supervisor.
    """
    try:
        return _chain.invoke({
            "intent": json.dumps(intent.model_dump(), indent=2),
            "customer_context": json.dumps(customer_context.model_dump(), indent=2)
        })
    except Exception as e:
        logger.error(f"Query synthesis failed for customer {customer_context.customer_id}: {e}")
        raise RuntimeError(f"Query synthesis failed for customer {customer_context.customer_id}: {e}") from e
