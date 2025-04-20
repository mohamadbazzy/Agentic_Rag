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

# Get a dedicated vector store for ECE track
ece_track_vectorstore = get_agent_vectorstore("ece_track")

def ece_track(state: State):
    """Handle queries about the Electrical and Computer Engineering track"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    
    # IMPORTANT CHANGE: Check if documents were passed from the department handler
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
                course_docs = ece_track_vectorstore.similarity_search(
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
        search_query = f"General Electrical Engineering: {query_type} - {user_message}"
        try:
            logger.info(f"No documents from department, searching ece_namespace with query: {search_query}")

            # Retrieve relevant documents
            retriever = ece_track_vectorstore.as_retriever(
                search_kwargs={
                    "namespace": "ece_namespace",
                    "k": 10
                }
            )
            ece_docs = retriever.get_relevant_documents(search_query)

            logger.info(f"Found {len(ece_docs)} documents in ece_namespace for general ECE track")

            if ece_docs:
                context = [
                    {"content": doc.page_content, "source": doc.metadata.get("source", "unknown")}
                    for doc in ece_docs
                ]
            else:
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
            context = [{
                "content": "Basic information about the general ECE track in the ECE department at AUB's MSFEA faculty.",
                "source": "error_fallback"
            }]

    # Log the first document content to verify what we're using
    if context:
        logger.info(f"Using document with content preview: {context[0]['content'][:100]}...")

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

    thread_id = state.get("configurable", {}).get("thread_id") if hasattr(state, "get") else None
    response = llm.invoke(messages, config={"configurable": {"thread_id": thread_id}} if thread_id else {})

    return {"messages": response}