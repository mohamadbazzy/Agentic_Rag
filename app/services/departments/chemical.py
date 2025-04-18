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

# Get a dedicated vector store for chemical department
chemical_vectorstore = get_agent_vectorstore("chemical")

def chemical_department(state: State):
    """Handle queries about the Chemical Engineering department"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    
    # Always retrieve from chemical's namespace, regardless of passed context
    search_query = f"Chemical Engineering: {query_type} - {user_message}"
    
    try:
        # Debug output to track the search
        logger.info(f"Searching chemical_namespace with query: {search_query}")
        
        # Ensure we're using the correct vectorstore and namespace
        chem_docs = chemical_vectorstore.similarity_search(
            search_query, 
            k=3,
            namespace="chemical_namespace",  # Explicitly specify namespace
            filter={"department": "chemical"}  # Add a filter for chemical department
        )
        
        logger.info(f"Found {len(chem_docs)} documents in chemical_namespace")
        
        if chem_docs:
            context = [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} 
                    for doc in chem_docs]
        else:
            # Fallback to hardcoded information if no docs found
            logger.warning("No documents found in chemical_namespace, using fallback content")
            context = [{
                "content": """
                The Chemical Engineering and Advanced Energy (CHEE) department at AUB offers ABET-accredited BE degrees, 
                as well as ME and PhD programs. Focus areas include process design, petroleum engineering, advanced energy, 
                thermodynamics, and reaction engineering. The department has strong research programs in energy, sustainability, 
                and process optimization.
                """,
                "source": "fallback_info"
            }]
    except Exception as e:
        logger.error(f"Error retrieving documents from chemical_namespace: {str(e)}")
        # Use fallback content in case of error
        context = [{
            "content": "The Chemical Engineering and Advanced Energy department offers undergraduate and graduate programs focused on chemical processes, petroleum engineering, and advanced energy technologies.",
            "source": "error_fallback"
        }]
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the Chemical Engineering and Advanced Energy (CHEE) department at AUB's Maroun Semaan Faculty of Engineering and Architecture (MSFEA).
    
    The student is asking about: {query_type}
    
    IMPORTANT: Only answer questions specifically related to Chemical Engineering and Advanced Energy. If the question involves other departments, politely explain that you can only advise on CHEE matters and suggest they consult the appropriate department advisor.
    
    Department Specifics:
    - The department offers a BE in Chemical Engineering (accredited by ABET)
    - Master's programs include ME in Chemical Engineering and various specializations in energy-related fields
    - PhD in Chemical Engineering is available
    
    Use the following information to answer the question:
    {context_str}
    Important: Only answer from the information provided. If you don't know the answer, say so.
    If you don't have specific information requested, provide general guidance about Chemical Engineering at AUB while acknowledging the limits of your knowledge.
    
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
