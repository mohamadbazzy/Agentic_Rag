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

# Get a dedicated vector store for ECE department
ece_vectorstore = get_agent_vectorstore("ece")

def ece_department(state: State):
    """
    Handle queries about the ECE department and determine which track within ECE
    the query is about
    """
    user_message = state["messages"][-1]["content"]
    query_type = state.get("query_type", "General")
    
    # Always retrieve from ECE's namespace, regardless of passed context
    search_query = f"Electrical and Computer Engineering: {query_type} - {user_message}"
    
    try:
        # Debug output to track the search
        logger.info(f"Searching ece_namespace with query: {search_query}")
        
        # Ensure we're using the correct vectorstore and namespace
        ece_docs = ece_vectorstore.similarity_search(
            search_query, 
            k=3,
            namespace="ece_namespace",  # Explicitly specify namespace
            filter={"department": "ece"}  # Add a filter for ECE department
        )
        
        logger.info(f"Found {len(ece_docs)} documents in ece_namespace")
        
        if ece_docs:
            context = [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} 
                    for doc in ece_docs]
        else:
            # Fallback to hardcoded information if no docs found
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
        logger.error(f"Error retrieving documents from ece_namespace: {str(e)}")
        # Use fallback content in case of error
        context = [{
            "content": "Basic information about Electrical and Computer Engineering at AUB's MSFEA faculty.",
            "source": "error_fallback"
        }]
    
    context_str = "\n".join([item["content"] for item in context])
    
    # First determine which ECE track the query is about (keep this functionality)
    track_prompt = f"""
    You are the academic advisor for the Electrical and Computer Engineering (ECE) department at AUB's MSFEA.
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

    Return only the track abbreviation (CSE, CCE, or ECE).
    """
    
    track_response = llm.invoke([{"role": "user", "content": track_prompt}])
    track = track_response.content.strip()
    
    # Now create a custom system message based on the determined track
    track_info = {
        "CSE": "Computer Science and Engineering (CSE) track focuses on computer architecture, hardware design, VLSI, embedded systems, IoT devices, operating systems, and hardware-software integration.",
        "CCE": "Computer and Communications Engineering (CCE) track focuses on telecommunications, networking, wireless systems, information theory, security, and signal processing for communications.",
        "ECE": "General Electrical and Computer Engineering (ECE) track covers a broad range of topics including power systems, control systems, electronics, and signals & systems."
    }
    
    # Create the system message with track-specific information
    system_message = f"""
    You are an academic advisor for the Electrical and Computer Engineering (ECE) department at AUB's Maroun Semaan Faculty of Engineering and Architecture (MSFEA), with expertise in the {track} track.
    
    The student is asking about: {query_type}
    
    IMPORTANT: You specialize in the {track} track. {track_info.get(track, "")}
    
    Department Specifics:
    - The department offers a BE in Electrical and Computer Engineering (accredited by ABET)
    - The department has three main tracks: Computer Science and Engineering (CSE), Computer and Communications Engineering (CCE), and general Electrical and Computer Engineering (ECE)
    - Master's programs include ME in Electrical and Computer Engineering with various specializations
    - PhD in Electrical and Computer Engineering is available
    
    Use the following information to help answer their question:
    {context_str}
    
    Important: Only answer from the information provided. If you don't know the answer, say so.
    Respond in a professional, helpful manner appropriate for an academic advisor at AUB.
    """
    
    # Generate the response with the specialized system message
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    response = llm.invoke(messages)
    
    # Return in the same format as other departments
    return {
        "messages": response,
        "track": track,  # Keep track info for potential future use
        "department": f"Electrical & Computer ({track})"  # Include track in department name
    }
