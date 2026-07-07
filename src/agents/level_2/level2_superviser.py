from src.utils.logger import get_logger
from src.models.action_result import ActionResult


logger = get_logger(__name__)

def layer2_superviser_response(result: ActionResult) -> dict:
    """
    Routes the EnrichedQueryPackage to either Layer 3 (human handoff)
    or Layer 2 agents based on priority level and escalation flags.
    Args:
        package (EnrichedQueryPackage): The fully enriched query package from Agent 3.
    Returns:
        dict: Routing decision with destination and reason.
    """
    if result.requires_human or result.resolution_confidence == "low":
        reason = result.reasoning
        logger.info(f"[L2 Supervisor] Escalating to Layer 3. Reason: {reason}")
        return {
            "destination": "layer3",
            "reason": reason,
            "result": result
        }

    logger.info("Giving response to the customer")
    return {
        "destination": "layer2",
        "action": result.system_action,
        "response": result.response_draft,
        "reason": result.reasoning,
        "result": result
    }