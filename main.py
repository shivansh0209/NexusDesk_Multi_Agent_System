import sys
from src.utils.logger import get_logger
from src.agents.level_1.intent_analyzer import IntentAnalyzerAgent
from src.agents.level_1.context_builder import ContextBuilderAgent
from src.agents.level_1.query_synthesizer import QuerySynthesizerAgent
from src.agents.level_1.level1_superviser import Layer1Supervisor
from src.agents.level_2.kb_agent import run_kb_agent
from src.agents.level_2.policy_agent import run_policy_agent
from src.agents.level_2.action_agent import run_action_agent
from src.agents.level_2.level2_superviser import layer2_superviser_response
from src.models.enriched_query import EnrichedQueryPackage
from src.models.kb_result import KBResult
from src.models.policy_result import PolicyResult

logger = get_logger(__name__)


def _handle_human_handoff(reason: str, package: EnrichedQueryPackage, response_draft: str | None = None) -> dict:
    """
    Packages a human handoff briefing for Layer 3.
    In production this would push to a ticket queue, CRM, or Slack.
    """
    logger.info(f"[Layer 3] Human handoff triggered for customer '{package.customer_id}'. Reason: {reason}")
    return {
        "status": "escalated_to_human",
        "customer_id": package.customer_id,
        "customer_name": package.customer_name,
        "priority": package.priority_level,
        "reason": reason,
        "enriched_brief": package.enriched_brief,
        "draft_for_agent": response_draft,  # Pre-written draft the human agent can use or discard
    }


def _run_layer2(package: EnrichedQueryPackage) -> dict:
    """
    Runs the appropriate Layer 2 agents based on the Layer 1 Supervisor's
    agent suggestion list, then passes results to the Action Agent and
    finally the Layer 2 Supervisor for a final routing decision.
    """
    agents = package.suggested_layer2_agents
    logger.info(f"[Layer 2] Running agents for '{package.customer_id}': {agents}")

    kb_result: KBResult | None = None
    policy_result: PolicyResult | None = None

    # --- Knowledge Base Agent ---
    if "knowledge_base_agent" in agents:
        try:
            kb_result = run_kb_agent(
                actual_intent=package.actual_intent,
                query_category=package.query_category,
                subscription_tier=package.subscription_tier,
            )
            logger.info(f"[KB Agent] Done. found={kb_result.found}, confidence={kb_result.confidence}")
        except Exception as e:
            logger.error(f"[KB Agent] Failed: {e}")
            # Non-fatal — Action Agent can still run on policy result alone

    # --- Policy & Eligibility Agent ---
    if "policy_eligibility_agent" in agents:
        try:
            policy_result = run_policy_agent(
                actual_intent=package.actual_intent,
                query_category=package.query_category,
                subscription_tier=package.subscription_tier,
            )
            logger.info(f"[Policy Agent] Done. found={policy_result.found}, eligible={policy_result.is_eligible}")
        except Exception as e:
            logger.error(f"[Policy Agent] Failed: {e}")
            # Non-fatal — Action Agent can still run on kb result alone

    # --- Guard: Action Agent needs at least one upstream result ---
    if kb_result is None and policy_result is None:
        reason = "Both KB and Policy agents failed or were not invoked — cannot generate a resolution."
        logger.error(f"[Layer 2] {reason}")
        return _handle_human_handoff(reason=reason, package=package)

    # --- Action & Response Agent ---
    try:
        action_result = run_action_agent(
            package=package,
            kb_result=kb_result,
            policy_result=policy_result,
        )
        logger.info(
            f"[Action Agent] Done. confidence={action_result.resolution_confidence}, "
            f"requires_human={action_result.requires_human}"
        )
    except Exception as e:
        logger.error(f"[Action Agent] Failed: {e}")
        return _handle_human_handoff(
            reason=f"Action agent crashed: {e}",
            package=package,
        )

    # --- Layer 2 Supervisor ---
    l2_decision = layer2_superviser_response(action_result)

    if l2_decision["destination"] == "layer3":
        return _handle_human_handoff(
            reason=l2_decision["reason"],
            package=package,
            response_draft=action_result.response_draft,
        )

    # Resolution successful — return final output
    logger.info(f"[Layer 2] Resolved. Action: {action_result.system_action}")
    return {
        "status": "resolved",
        "customer_id": package.customer_id,
        "customer_name": package.customer_name,
        "response_draft": action_result.response_draft,
        "system_action": action_result.system_action,
        "resolution_confidence": action_result.resolution_confidence,
        "reasoning": action_result.reasoning,
    }



def _run_layer1(customer_id: str, customer_query: str) -> EnrichedQueryPackage:
    """
    Runs the full Layer 1 pipeline:
      Agent 1 (Intent Analyzer) -> Agent 2 (Context Builder) -> Agent 3 (Query Synthesizer)
    Returns the EnrichedQueryPackage.
    """
    # Agent 1 — Intent Analysis
    logger.info(f"[Intent Analyzer] Analyzing query for customer '{customer_id}'...")
    intent = IntentAnalyzerAgent(customer_query)
    logger.info(f"[Intent Analyzer] tone={intent.emotional_tone}, urgency={intent.urgency}")

    # Agent 2 — Customer Context
    logger.info(f"[Context Builder] Fetching context for customer '{customer_id}'...")
    customer_context = ContextBuilderAgent(customer_id)
    logger.info(f"[Context Builder] tier={customer_context.subscription_tier}, health={customer_context.account_health}")

    # Agent 3 — Query Synthesis
    logger.info(f"[Query Synthesizer] Synthesizing enriched package...")
    package = QuerySynthesizerAgent(intent, customer_context)
    logger.info(
        f"[Query Synthesizer] category={package.query_category}, "
        f"priority={package.priority_level}, "
        f"flags={package.escalation_flags}"
    )

    return package



def run_nexusdesk(customer_id: str, customer_query: str) -> dict:
    """
    Full NexusDesk orchestration pipeline.

    Flow:
      Layer 1 (Intent -> Context -> Synthesis)
        L1 Supervisor -> Layer 3 (P0 / critical flags)
                      -> Layer 2 (KB + Policy + Action)
                           L2 Supervisor -> Layer 3 (low confidence / human required)
                                        -> Customer Response

    Args:
        customer_id (str): Unique customer identifier (must exist in ChromaDB).
        customer_query (str): Raw customer support message.

    Returns:
        dict: Final result with status, response, and any system actions.
    """
    logger.info(f"{'='*60}")
    logger.info(f"[NexusDesk] New ticket — customer_id='{customer_id}'")
    logger.info(f"[NexusDesk] Query: {customer_query[:120]}{'...' if len(customer_query) > 120 else ''}")
    logger.info(f"{'='*60}")

    # Layer 1
    try:
        package = _run_layer1(customer_id, customer_query)
    except ValueError as ve:
        # Structured domain errors: inactive account, empty query, customer not found
        logger.error(f"[Layer 1] Domain error: {ve}")
        return {"status": "error", "message": str(ve)}
    except Exception as e:
        logger.error(f"[Layer 1] Unexpected failure: {e}")
        return {"status": "error", "message": f"Layer 1 pipeline failed: {e}"}

    # Layer 1 Supervisor
    l1_decision = Layer1Supervisor(package)
    logger.info(f"[L1 Supervisor] Decision: {l1_decision['destination'].upper()}")

    if l1_decision["destination"] == "layer3":
        return _handle_human_handoff(
            reason=l1_decision["reason"],
            package=package,
        )

    # Layer 2
    try:
        return _run_layer2(package)
    except Exception as e:
        logger.error(f"[Layer 2] Unexpected failure: {e}")
        return _handle_human_handoff(
            reason=f"Layer 2 pipeline crashed unexpectedly: {e}",
            package=package,
        )


if __name__ == "__main__":
    import json

    # Accept args from CLI: python main.py <customer_id> "<query>"
    if len(sys.argv) == 3:
        _customer_id = sys.argv[1]
        _customer_query = sys.argv[2]
    else:
        # Default test case
        _customer_id = "CUST_001"
        _customer_query = (
            "I just noticed I was charged twice this month and I have a client demo tomorrow. "
            "I need this fixed immediately — I already checked my invoices and both show as paid."
        )

    result = run_nexusdesk(_customer_id, _customer_query)

    print("\n" + "=" * 60)
    print("NEXUSDESK RESULT")
    print("=" * 60)
    print(json.dumps(result, indent=2))