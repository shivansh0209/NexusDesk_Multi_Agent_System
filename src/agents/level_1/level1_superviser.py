from src.models.enriched_query import EnrichedQueryPackage
from src.utils.logger import get_logger

logger = get_logger(__name__)

CRITICAL_FLAGS = {"data_loss", "security_incident", "at_risk_account", "past_unresolved_ticket"}

def Layer1Supervisor(package: EnrichedQueryPackage) -> dict:
    """
    Routes the EnrichedQueryPackage to either Layer 3 (human handoff)
    or Layer 2 agents based on priority level and escalation flags.
    Args:
        package (EnrichedQueryPackage): The fully enriched query package from Agent 3.
    Returns:
        dict: Routing decision with destination and reason.
    """
    triggered_flags = CRITICAL_FLAGS & set(package.escalation_flags)

    if package.priority_level == "P0" or triggered_flags:
        reason = f"Priority: {package.priority_level} | Flags: {', '.join(triggered_flags) if triggered_flags else 'none'}"
        logger.info(f"[L1 Supervisor] Escalating {package.customer_id} to Layer 3. Reason: {reason}")
        return {
            "destination": "layer3",
            "reason": reason,
            "package": package
        }

    logger.info(f"[L1 Supervisor] Routing {package.customer_id} to Layer 2 agents: {package.suggested_layer2_agents}")
    return {
        "destination": "layer2",
        "agents": package.suggested_layer2_agents,
        "package": package
    }