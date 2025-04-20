from langchain_openai import ChatOpenAI
from app.core.config import OPENAI_API_KEY
from app.models.schemas import State
from app.db.vector_store import get_agent_vectorstore
import logging
import re

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model_name="gpt-4o"
)

# Get a dedicated vector store for CSE track
cse_vectorstore = get_agent_vectorstore("cse")

def cse_track(state: State):
    """Handle queries about the Computer Science and Engineering track"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    
    # Check if documents were passed from the department handler
    department_docs = state.get("documents", [])
    logger.info(f"Received {len(department_docs)} documents from department handler")
    
    # Direct search for course codes if we have no documents but the user is asking about a course
    if not department_docs:
        # Check if the user message contains a course code
        course_match = re.search(r'(EECE)\s*(\d{3})', user_message, re.IGNORECASE)
        if course_match:
            course_code = f"{course_match.group(1)} {course_match.group(2)}"
            logger.info(f"No documents passed but detected course code: {course_code}. Doing direct search.")
            try:
                # Search directly for the course
                course_docs = cse_vectorstore.similarity_search(
                    "course information", 
                    k=5,
                    namespace="ece_namespace",
                    filter={"course_code": {"$eq": course_code}}
                )
                
                if course_docs:
                    logger.info(f"Direct course search found {len(course_docs)} documents")
                    department_docs = [
                        {"content": doc.page_content, "source": doc.metadata.get("source", "unknown")}
                        for doc in course_docs
                    ]
            except Exception as e:
                logger.error(f"Error in direct course search: {str(e)}")
    
    # Use the documents from department if available, otherwise do our own search
    if department_docs:
        logger.info("Using documents from department handler or direct course search")
        context = department_docs
    else:
        # Only do our own search if no documents were passed
        search_query = f"Computer Science and Engineering: {query_type} - {user_message}"
        
        try:
            # Debug output to track the search
            logger.info(f"No documents from department, searching cse_namespace with query: {search_query}")
            
            # Ensure we're using the correct vectorstore and namespace
            cse_docs = cse_vectorstore.similarity_search(
                search_query, 
                k=3,
                namespace="cse_namespace",  # Explicitly specify namespace
                filter={"track": "cse"}  # Add a filter for CSE track
            )
            
            logger.info(f"Found {len(cse_docs)} documents in cse_namespace")
            
            if cse_docs:
                context = [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} 
                        for doc in cse_docs]
            else:
                # Fallback to hardcoded information if no docs found
                logger.warning("No documents found in cse_namespace, using fallback content")
                context = [{
                    "content": """
                    The Computer Science and Engineering (CSE) track at AUB focuses on computer architecture, 
                    hardware design, VLSI, embedded systems, IoT devices, operating systems, and hardware-software 
                    integration. CSE graduates typically work in hardware design, system architecture, embedded systems 
                    development, and IoT applications.
                    """,
                    "source": "fallback_info"
                }]
        except Exception as e:
            logger.error(f"Error retrieving documents from cse_namespace: {str(e)}")
            # Use fallback content in case of error
            context = [{
                "content": "Basic information about the CSE track in the ECE department at AUB's MSFEA faculty.",
                "source": "error_fallback"
            }]
    
    # Log the first document content to verify what we're using
    if context:
        logger.info(f"Using document with content preview: {context[0]['content'][:100]}...")
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the Computer Science and Engineering (CSE) track in the Electrical and Computer 
    Engineering department at AUB's Maroun Semaan Faculty of Engineering and Architecture (MSFEA).
    
    The student is asking about: {query_type}
    
    IMPORTANT: Only answer questions specifically related to the CSE track. If the question involves other tracks 
    or departments, politely explain that you can only advise on CSE matters and suggest they consult the appropriate advisor.
    
    CSE Track Specifics:
    - Part of the ECE department's undergraduate program
    - Focuses on computer architecture, hardware design, embedded systems, and IoT
    - Strong emphasis on hardware-software integration
    
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
