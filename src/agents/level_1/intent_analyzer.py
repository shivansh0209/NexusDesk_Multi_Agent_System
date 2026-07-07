from src.models.intent import Intent
from src.prompts.intent_analyzer import INTENT_ANALYZER_PROMPT
from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.logger import get_logger

logger = get_logger(__name__)
_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2).with_structured_output(Intent)
_chain = INTENT_ANALYZER_PROMPT | _llm

def IntentAnalyzerAgent(customer_query: str) -> Intent:
    """
    Analyzes the intent of a customer query using the INTENT_ANALYZER_PROMPT.
    Args:
        customer_query (str): The raw customer query to analyze.
    Returns:
        Intent: A Pydantic model containing the analyzed intent information.
    """
    try:
        customer_query = customer_query.strip()
        if not customer_query:
            raise ValueError("Customer query cannot be empty.")
        return _chain.invoke({"customer_query": customer_query})
    except ValueError as ve:
        raise ve
    except Exception as e:
        logger.error(f"Error in analyzing intent: {e}")
        raise RuntimeError(f"Intent analysis failed: {e}") from e