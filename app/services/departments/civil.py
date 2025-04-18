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

# Get a dedicated vector store for civil department
civil_vectorstore = get_agent_vectorstore("civil")

def civil_department(state: State):
    """Handle queries about the Civil Engineering department"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    
    # Always retrieve from civil's namespace, regardless of passed context
    search_query = f"Civil Engineering: {query_type} - {user_message}"
    
    try:
        # Debug output to track the search
        logger.info(f"Searching civil_namespace with query: {search_query}")
        
        # Ensure we're using the correct vectorstore and namespace
        civil_docs = civil_vectorstore.similarity_search(
            search_query, 
            k=3,
            namespace="civil_namespace",  # Explicitly specify namespace
            filter={"department": "civil"}  # Add a filter for civil department
        )
        
        logger.info(f"Found {len(civil_docs)} documents in civil_namespace")
        
        if civil_docs:
            context = [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} 
                    for doc in civil_docs]
        else:
            # Fallback to hardcoded information if no docs found
            logger.warning("No documents found in civil_namespace, using fallback content")
            context = [{
                "content": """
                The Civil and Environmental Engineering (CEE) department at AUB offers ABET-accredited BE degrees, 
                as well as ME and PhD programs. Focus areas include structural engineering, construction management, 
                transportation, water resources, geotechnical, and environmental engineering. The department has strong 
                research programs in sustainability, infrastructure development, and environmental solutions.
                """,
                "source": "fallback_info"
            }]
    except Exception as e:
        logger.error(f"Error retrieving documents from civil_namespace: {str(e)}")
        # Use fallback content in case of error
        context = [{
            "content": "The Civil and Environmental Engineering department offers programs covering infrastructure design, structural engineering, water resources, environmental engineering, and construction management.",
            "source": "error_fallback"
        }]
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the Civil and Environmental Engineering (CEE) department at AUB's Maroun Semaan Faculty of Engineering and Architecture (MSFEA).
    
    The student is asking about: {query_type}
    
    IMPORTANT: Only answer questions specifically related to Civil and Environmental Engineering. If the question involves other departments, politely explain that you can only advise on CEE matters and suggest they consult the appropriate department advisor.
    
    Department Specifics:
    - The department offers a BE in Civil Engineering (accredited by ABET)
    - Master's programs include ME in Civil Engineering with various specializations
    - PhD in Civil Engineering is available
    - Focus areas include: structural engineering, construction management, transportation, water resources, geotechnical, and environmental engineering
    
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
