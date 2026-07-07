import json
from langchain_google_genai import ChatGoogleGenerativeAI
from src.models.action_result import ActionResult
from src.models.enriched_query import EnrichedQueryPackage
from src.models.kb_result import KBResult
from src.models.policy_result import PolicyResult
from src.prompts.action_agent import ACTION_AGENT_PROMPT
from src.utils.logger import get_logger

logger = get_logger(__name__)

_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2).with_structured_output(ActionResult)
_chain = ACTION_AGENT_PROMPT | _llm


def run_action_agent(
    package: EnrichedQueryPackage,
    kb_result: KBResult | None = None,
    policy_result: PolicyResult | None = None
) -> ActionResult:
    """
    Synthesizes KB and Policy results into a customer-facing response and system action.

    Args:
        package (EnrichedQueryPackage): The full enriched query package from Layer 1.
        kb_result (KBResult | None): Output from the KB agent. None if KB agent was not invoked.
        policy_result (PolicyResult | None): Output from the Policy agent. None if Policy agent was not invoked.

    Returns:
        ActionResult: Final resolution containing the response draft, system action, and confidence.
    """
    if kb_result is None and policy_result is None:
        raise ValueError("At least one of kb_result or policy_result must be provided.")

    try:
        return _chain.invoke({
            "enriched_package": json.dumps(package.model_dump(), indent=2),
            "kb_result": json.dumps(kb_result.model_dump(), indent=2) if kb_result else "Not invoked.",
            "policy_result": json.dumps(policy_result.model_dump(), indent=2) if policy_result else "Not invoked."
        })

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"[Action Agent] Failed for customer '{package.customer_id}': {e}")
        raise RuntimeError(f"Action agent failed: {e}") from e