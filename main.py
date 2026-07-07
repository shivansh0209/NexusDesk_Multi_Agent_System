from src.agents.level_1.intent_analyzer import IntentAnalyzerAgent
from GenAI.NexusDesk.src.agents.level_1.context_builder import ContextBuilderAgent
from GenAI.NexusDesk.src.agents.level_1.query_synthesizer import QuerySynthesizerAgent
from src.agents.level_1.level1_superviser import Layer1Supervisor
from pprint import pprint

test_query = {
    "id": "Q-001",
    "customer_id": "CUST-NEW-001",
    "raw_query": "Hi, I upgraded to Pro last week but I still can't see any analytics dashboard. Where is it?",
    "expected_category": "feature_access",
    "expected_resolution_level": 1,
    "notes": "Should be resolved at Level 1 via RAG - similar to TKT-002 but for analytics not Gantt"
  }

intent = IntentAnalyzerAgent(test_query["raw_query"])
context = ContextBuilderAgent(test_query["customer_id"])
package = QuerySynthesizerAgent(intent, context)
routing = Layer1Supervisor(package)
pprint(routing)