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

# Get a dedicated vector store for CCE track
cce_vectorstore = get_agent_vectorstore("cce")

def cce_track(state: State):
    """Handle queries about the Computer and Communications Engineering track"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    
    # Always retrieve from CCE's namespace, regardless of passed context
    search_query = f"Computer and Communications Engineering: {query_type} - {user_message}"
    
    try:
        # Debug output to track the search
        logger.info(f"Searching cce_namespace with query: {search_query}")
        
        # Ensure we're using the correct vectorstore and namespace
        cce_docs = cce_vectorstore.similarity_search(
            search_query, 
            k=3,
            namespace="cce_namespace",  # Explicitly specify namespace
            filter={"track": "cce"}  # Add a filter for CCE track
        )
        
        logger.info(f"Found {len(cce_docs)} documents in cce_namespace")
        
        if cce_docs:
            context = [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} 
                    for doc in cce_docs]
        else:
            # Fallback to hardcoded information if no docs found
            logger.warning("No documents found in cce_namespace, using fallback content")
            context = [{
                "content": """
                The Computer and Communications Engineering (CCE) track at AUB focuses on telecommunications, 
                networking, wireless systems, information theory, security, and signal processing for communications. 
                CCE graduates typically work in telecommunications, networking, cybersecurity, and wireless technologies.
                """,
                "source": "fallback_info"
            }]
    except Exception as e:
        logger.error(f"Error retrieving documents from cce_namespace: {str(e)}")
        # Use fallback content in case of error
        context = [{
            "content": "Basic information about the CCE track in the ECE department at AUB's MSFEA faculty.",
            "source": "error_fallback"
        }]
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the Computer and Communications Engineering (CCE) track in the Electrical and Computer 
    Engineering department at AUB's Maroun Semaan Faculty of Engineering and Architecture (MSFEA).
    
    The student is asking about: {query_type}
    
    IMPORTANT: Only answer questions specifically related to the CCE track. If the question involves other tracks 
    or departments, politely explain that you can only advise on CCE matters and suggest they consult the appropriate advisor.
    
    CCE Track Specifics:
    - Part of the ECE department's undergraduate program
    - Focuses on telecommunications, networking, wireless systems, and information security
    - Strong emphasis on communications technology and signal processing
    
    Use the following information to help answer their question:
    {context_str}
    
    Important: Only answer from the information provided. If you don't know the answer, say so.
    Respond in a professional, helpful manner appropriate for an academic advisor at AUB.
    """
    
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    
    # Get thread_id from configurable state if available (for conversation memory)
    thread_id = None
    if hasattr(state, "get") and callable(state.get):
        config = state.get("configurable", {})
        if isinstance(config, dict):
            thread_id = config.get("thread_id")
    
    # Pass thread_id to maintain conversation context if available
    if thread_id:
        response = llm.invoke(messages, config={"configurable": {"thread_id": thread_id}})
    else:
        response = llm.invoke(messages)
    
    return {"messages": response}
