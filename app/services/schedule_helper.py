from langchain_openai import ChatOpenAI
from app.core.config import OPENAI_API_KEY
from app.models.schemas import State
from app.db.vector_store import get_agent_vectorstore
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model_name="gpt-4o"
)

# Get a dedicated vector store for schedule helper
schedule_helper_vectorstore = get_agent_vectorstore("schedule_maker")

def schedule_helper(state: State):
    """
    Handle queries about course scheduling, conflicts, and classroom locations
    """
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    
    # Always retrieve from schedule helper's namespace, regardless of passed context
    search_query = f"Course Scheduling: {query_type} - {user_message}"
    
    try:
        # Get information from vector store
        docs = schedule_helper_vectorstore.similarity_search(
            search_query,
            k=15  
        )
        context = [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} 
                  for doc in docs]
        logger.info(f"Retrieved {len(context)} documents from schedule_maker_namespace")
    except Exception as e:
        logger.error(f"Error retrieving documents from schedule_maker_namespace: {str(e)}")
        # Use fallback content in case of error
        context = [{
            "content": "Basic information about course scheduling at AUB.",
            "source": "error_fallback"
        }]
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are a scheduling assistant for students at the American University of Beirut (AUB).
    
    The student is asking about: "{user_message}"
    
    Your primary responsibilities:
    1. Help students resolve scheduling conflicts
    2. Provide information about course timings and locations
    3. Suggest alternative sections when there are conflicts
    4. Help optimize student schedules to minimize gaps or create preferred time blocks
    
    Course Information Guidelines:
    - Each course has multiple sections with different meeting times and locations
    - Course sections are identified by numbers (e.g., CMPS 200 Section 1)
    - Meeting times include days of the week and start/end times
    - Locations include building names and room numbers
    - Some courses may have associated lab or discussion sections
    
    When analyzing schedule conflicts:
    - Check if two courses occur at the same time or have overlapping times
    - Consider travel time between buildings for back-to-back classes
    - Factor in student preferences (e.g., no early morning classes, compact schedule, etc.)
    
    Use the following information to help answer their question:
    {context_str}
    
    If you don't have specific information about course times or locations, explain that you can provide general scheduling advice but may need more details about specific courses to resolve conflicts.
    
    Respond in a professional, helpful manner appropriate for a university scheduling assistant.
    """
    
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    response = llm.invoke(messages)
    
    return {"messages": response}