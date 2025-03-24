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
    model_name="gpt-3.5-turbo"
)

# Get a dedicated vector store for ECE track
ece_track_vectorstore = get_agent_vectorstore("ece_track")

def ece_track(state: State):
    """Handle queries about the general Electrical and Computer Engineering track"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    
    # Always retrieve from ECE track's namespace, regardless of passed context
    search_query = f"General Electrical Engineering: {query_type} - {user_message}"
    
    try:
        # Debug output to track the search
        logger.info(f"Searching ece_namespace with query: {search_query}")
        
        # For the general ECE track, we can use the same namespace as the department but with a more specific filter
        ece_docs = ece_track_vectorstore.similarity_search(
            search_query, 
            k=3,
            namespace="ece_namespace",  # Use the ECE department namespace
            filter={"track": "general_ece"}  # Filter for general ECE content (not track-specific)
        )
        
        logger.info(f"Found {len(ece_docs)} documents in ece_namespace for general ECE track")
        
        if ece_docs:
            context = [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} 
                    for doc in ece_docs]
        else:
            # Fallback to hardcoded information if no docs found
            logger.warning("No documents found in ece_namespace for general ECE track, using fallback content")
            context = [{
                "content": """
                The general Electrical and Computer Engineering track at AUB covers a broad range of topics including 
                power systems, control systems, electronics, signals & systems, and general electrical engineering principles. 
                This track provides a well-rounded education suitable for diverse career paths in electrical engineering.
                """,
                "source": "fallback_info"
            }]
    except Exception as e:
        logger.error(f"Error retrieving documents from ece_namespace for general ECE track: {str(e)}")
        # Use fallback content in case of error
        context = [{
            "content": "Basic information about the general ECE track in the ECE department at AUB's MSFEA faculty.",
            "source": "error_fallback"
        }]
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the general Electrical and Computer Engineering track in the Electrical and Computer 
    Engineering department at AUB's Maroun Semaan Faculty of Engineering and Architecture (MSFEA).
    
    The student is asking about: {query_type}
    
    IMPORTANT: Your focus is on general electrical engineering topics - power systems, control systems, electronics, 
    and signals & systems. For CSE or CCE specific topics, suggest they consult those specialized track advisors.
    
    General ECE Track Specifics:
    - Part of the ECE department's undergraduate program
    - Provides a broad foundation in electrical engineering principles
    - Includes power systems, control systems, electronics, and signals & systems
    - Offers flexibility to specialize in various electrical engineering domains
    
    Use the following information to help answer their question:
    {context_str}
    
    Important: Only answer from the information provided. If you don't know the answer, say so.
    Respond in a professional, helpful manner appropriate for an academic advisor at AUB.
    """
    
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    response = llm.invoke(messages)
    
    return {"messages": response}
