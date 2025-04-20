from langchain_openai import ChatOpenAI
from app.core.config import OPENAI_API_KEY
from app.models.schemas import State
from app.db.vector_store import get_agent_vectorstore
import logging
import re

logger = logging.getLogger(__name__)

llm = ChatOpenAI(api_key=OPENAI_API_KEY, model_name="gpt-4o")
ece_vectorstore = get_agent_vectorstore("ece")

def ece_department(state: State):
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")

    course_match = re.search(r'(EECE)\s*(\d{3})', user_message, re.IGNORECASE)
    course_code = f"{course_match.group(1)} {course_match.group(2)}" if course_match else None

    search_query = f"Electrical and Computer Engineering: {query_type} - {user_message}"
    context = []

    try:
        logger.info(f"Searching ece_namespace with query: {search_query}")

        if course_code:
            logger.info(f"Detected course code: {course_code}")
            
            # Use exact metadata filtering which works according to our tests
            logger.info(f"Searching with exact course code filter: {course_code}")
            course_docs = ece_vectorstore.similarity_search(
                "course information",  # Generic query that will rely on filtering
                k=5,
                namespace="ece_namespace",
                filter={"course_code": {"$eq": course_code}}
            )
            
            logger.info(f"Found {len(course_docs)} documents with course filter")
            
            if course_docs:
                ece_docs = course_docs
            else:
                # If no exact match, fall back to direct semantic search
                logger.info(f"No exact matches found, trying with semantic search for course code")
                ece_docs = ece_vectorstore.similarity_search(
                    course_code,
                    k=5,
                    namespace="ece_namespace"
                )
                logger.info(f"Found {len(ece_docs)} documents with semantic search")
        else:
            ece_docs = ece_vectorstore.similarity_search(
                search_query,
                k=3,
                namespace="ece_namespace"
            )

        logger.info(f"Found {len(ece_docs)} documents in ece_namespace")
        
        # Log document metadata to see what's available
        if ece_docs:
            for i, doc in enumerate(ece_docs[:2]):  # Log first 2 docs
                logger.info(f"Doc {i+1} metadata: {doc.metadata}")
                logger.info(f"Doc {i+1} content preview: {doc.page_content[:100]}...")

        if ece_docs:
            context = [
                {"content": doc.page_content, "source": doc.metadata.get("source", "unknown")}
                for doc in ece_docs
            ]
        else:
            logger.warning("No documents found in ece_namespace, using fallback content")
            context = [{
                "content": """
                The Electrical and Computer Engineering (ECE) department at AUB offers ABET-accredited BE degrees,
                as well as ME and PhD programs. The department has three main tracks: Computer Science and Engineering (CSE),
                Computer and Communications Engineering (CCE), and general Electrical and Computer Engineering (ECE).
                """,
                "source": "fallback_info"
            }]

    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        context = [{
            "content": "Basic information about Electrical and Computer Engineering at AUB's MSFEA faculty.",
            "source": "error_fallback"
        }]

    context_str = "\n".join([c["content"] for c in context])

    prompt = f"""
    You are the academic advisor for the Electrical and Computer Engineering (ECE) department at AUB's MSFEA you can answer general questions about the department but if the question is about a specific track Return only the track abbreviation (CSE, CCE, or ECE) without any explanation..

    Determine which specific track within ECE this query is most directly related to:
    Query: {user_message}

    Choose from:
    - CSE (Computer Science and Engineering): For queries specifically about computer architecture, hardware design, VLSI, embedded systems, IoT devices, operating systems, or hardware-software integration.
    - CCE (Computer and Communications Engineering): For queries specifically about telecommunications, networking, wireless systems, information theory, security, or signal processing for communications.
    - ECE (General Electrical and Computer Engineering): For queries about general ECE topics, power systems, control systems, electronics, signals & systems, or topics that span multiple tracks.

    IMPORTANT ROUTING GUIDELINES:
    1. If the query explicitly mentions a track by name (CSE, CCE) or its distinctive specializations, choose that track.
    2. If the query is about general ECE topics, curriculum overview, admission, or faculty, choose "ECE".
    3. If the query discusses topics across multiple tracks or is comparing tracks, choose "ECE".
    4. If the query is vague or could potentially apply to multiple tracks, choose "ECE".
    5. ONLY choose CSE or CCE if the query is SPECIFICALLY about topics unique to those tracks.
    6. When in doubt, choose "ECE" rather than a specific track.
    7. Never force a query into CSE or CCE unless it is clearly about their specialized topics.
    """

    thread_id = state.get("configurable", {}).get("thread_id") if hasattr(state, "get") else None
    response = llm.invoke([{"role": "user", "content": prompt}], config={"configurable": {"thread_id": thread_id}} if thread_id else {})

    track = response.content.strip().upper()
    if track not in {"CSE", "CCE", "ECE"}:
        track = "ECE"

    # Direct modification of state instead of just returning values
    # This is more compatible with different LangGraph versions
    if hasattr(state, "update"):
        # If state is a dict-like object with update method
        state.update({
            "track": track,
            "documents": context
        })
        logger.info(f"Updated state with {len(context)} documents for track {track}")
        return state
    else:
        # Fall back to returning values if state can't be updated directly
        logger.info(f"Returning {len(context)} documents for track {track}")
        return {
            "track": track, 
            "documents": context
        }