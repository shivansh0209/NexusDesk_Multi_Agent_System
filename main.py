from src.agents.level_1.intent_analyzer import analyze_intent
from src.agents.level_1.customer_context_builder import build_context
from src.agents.level_1.query_synthesiser import synthesize_query
from src.agents.level_1.level1_superviser import layer1_supervisor
from pprint import pprint

test_query = {
    "id": "Q-001",
    "customer_id": "CUST-NEW-001",
    "raw_query": "Hi, I upgraded to Pro last week but I still can't see any analytics dashboard. Where is it?",
    "expected_category": "feature_access",
    "expected_resolution_level": 1,
    "notes": "Should be resolved at Level 1 via RAG - similar to TKT-002 but for analytics not Gantt"
  }

intent = analyze_intent(test_query["raw_query"])
context = build_context(test_query["customer_id"])
package = synthesize_query(intent, context)
routing = layer1_supervisor(package)
pprint(routing)