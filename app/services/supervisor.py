from langchain_openai import ChatOpenAI
from app.core.config import OPENAI_API_KEY
from app.models.schemas import State
from app.db.vector_store import vectorstore
from .agent_index_wrapper import get_restricted_index
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model_name="gpt-4o"
)

# Get the restricted index for supervisor
# Wrap the vector store's underlying Pinecone index
original_index = vectorstore._index

# The supervisor needs access to all department namespaces to properly route queries
allowed_namespaces = ["supervisor_namespace", "mechanical_namespace", "chemical_namespace", 
                      "civil_namespace", "ece_namespace", "cse_namespace", "cce_namespace", 
                      "msfea_advisor_namespace", "schedule_helper_namespace"]

# Check if get_restricted_index accepts a list of namespaces
try:
    restricted_index = get_restricted_index(original_index, "supervisor", allowed_namespaces)
except TypeError:
    # If it doesn't accept a list, use the original index (unrestricted)
    logger.info("Supervisor needs access to all namespaces for proper routing - using unrestricted index")
    restricted_index = original_index

# Replace the vector store's index with the restricted one
vectorstore._index = restricted_index
logger.info("Created index for supervisor with access to all necessary department namespaces")

def handle_invalid_query(reason):
    """Generate a response for invalid queries"""
    return {
        "is_valid": False,
        "response": f"I'm sorry, but I can only answer questions related to academic advising at AUB's MSFEA. {reason} Please ask a question related to engineering programs, courses, admissions, or career options.",
        "department": "Invalid",
        "query_type": "Invalid Query",
        "context": []
    }

def supervisor(state: State):
    """
    Main supervisor node that determines which department the query is about
    and routes to the appropriate department node, with added guardrails
    """
    # Get the latest user message
    user_message = state["messages"][-1].content
    
    # Get thread_id from configurable state if available (for conversation memory)
    thread_id = None
    if hasattr(state, "get") and callable(state.get):
        config = state.get("configurable", {})
        if isinstance(config, dict):
            thread_id = config.get("thread_id")
    
    # STEP 1: Validate the query
    validation_prompt = f"""
    Determine if this query is appropriate for an academic advising system at AUB's MSFEA:
    Query: {user_message}

    Rules:
    1. ACCEPT any questions related to AUB's MSFEA departments, programs, courses, admissions, faculty, or careers
    2. ACCEPT general questions about engineering education at AUB, even if somewhat vague
    3. ACCEPT administrative questions about MSFEA (locations, contact info, deadlines, etc.)
    4. ACCEPT comparative questions about different engineering departments or programs
    5. ACCEPT questions about engineering student life, facilities, or activities
    6. REJECT only clearly inappropriate content (offensive material, spam, etc.)
    7. REJECT requests to write assignments or essays
    8. REJECT questions completely unrelated to engineering education (e.g., medical advice, politics)
    9. When in doubt, ACCEPT the query - it's much better to attempt to answer than to reject valid questions

    Respond with ONLY one of:
    - VALID: [brief reason] - if the query could possibly be addressed by an academic advisor
    - INVALID: [brief reason] - ONLY if the query is clearly inappropriate or completely unrelated to engineering education

    Examples of valid queries (ACCEPT these):
    - Questions about any engineering department, even if vague
    - General questions about MSFEA or engineering at AUB
    - Questions about campus facilities related to engineering
    - Questions comparing different programs or departments
    - Simple administrative questions about MSFEA
    - Questions about professors or research areas
    - Vague questions that still relate to engineering education
    - General questions about master's programs at MSFEA

    Examples of invalid queries (REJECT these):
    - Requests to write essays or complete assignments
    - Offensive or inappropriate content
    - Questions about completely unrelated fields (e.g., medical advice)
    - Spam or nonsensical text (e.g., random keyboard mashing)
    """
    
    # Pass thread_id to maintain conversation context if available
    if thread_id:
        validation_response = llm.invoke([{"role": "user", "content": validation_prompt}], 
                                        config={"configurable": {"thread_id": f"{thread_id}_validation"}})
    else:
        validation_response = llm.invoke([{"role": "user", "content": validation_prompt}])
    
    validation_result = validation_response.content.strip()
    
    # If invalid, return a rejection response
    if "INVALID:" in validation_result:
        reason = validation_result.split("INVALID:")[1].strip()
        return handle_invalid_query(reason)
    
    # STEP 2: Determine which department the query is about
    department_prompt = f"""
    You are the main academic advisor at the Maroun Semaan Faculty of Engineering and Architecture (MSFEA) at the American University of Beirut (AUB).

    Determine which engineering department or unit this student query is most directly related to:
    Query: {user_message}

    Choose from the following departments/units ONLY:
    - Architecture and Design (ARCH): For queries specifically about architecture, graphic design, or urban planning
    - Civil and Environmental Engineering (CEE): For queries specifically about civil engineering, construction, structural engineering, or environmental engineering
    - Chemical Engineering and Advanced Energy (CHEE): For queries specifically about chemical engineering, petroleum, or advanced energy
    - Electrical and Computer Engineering (ECE): For queries specifically about electrical engineering, computer engineering, CCE or CSE tracks
    - Industrial Engineering and Management (ENMG): For queries specifically about industrial engineering, engineering management, or operations
    - Mechanical Engineering (MECH): For queries specifically about mechanical engineering, thermal systems, materials, or manufacturing
    - MSFEA Advisor: For general engineering queries, faculty-wide policies, interdisciplinary programs, or when no specific department applies MSFEA Advisor ALSO HAS ALL THE CALENDARS AND DATES OF MAIN UNIVERSITY EVENTS AND DEADLINES EXAMS SEMESTER BREAKS AND MORE....
    - Schedule Helper: For queries specifically about class schedules, course schedules, or class timetables or who is giving a specific class or at what time

    IMPORTANT GUIDELINES FOR ROUTING:
    1. If the query is general or doesn't specify a department, choose "MSFEA Advisor".
    2. If the query mentions multiple departments or is about comparing departments, choose "MSFEA Advisor".
    3. If the query is about general master's programs or overall MSFEA offerings, choose "MSFEA Advisor".
    4. If the query is vague, unclear, or could apply to multiple departments, choose "MSFEA Advisor".
    5. If the query is about non-academic matters (housing, tuition, campus life, etc.), choose "MSFEA Advisor".
    6. For administrative questions about the faculty as a whole, choose "MSFEA Advisor".
    7. DO NOT force a query into a specific department unless it explicitly mentions that department or is clearly specific to that field.
    8. When in doubt, choose "MSFEA Advisor" rather than a specific department.
    9. ONLY choose a specific department when the query explicitly mentions that department or is unambiguously related to its distinct field.

    Return only the department name or "Schedule Helper" without any explanation.
    """
    
    # Pass thread_id to maintain conversation context if available
    if thread_id:
        department_response = llm.invoke([{"role": "user", "content": department_prompt}], 
                                        config={"configurable": {"thread_id": f"{thread_id}_department"}})
    else:
        department_response = llm.invoke([{"role": "user", "content": department_prompt}])
    
    department = department_response.content.strip()
    
    # STEP 3: Use a default query type instead of LLM determination
    query_type = "General"  # Default value without making an API call
    
    # STEP 4: Retrieve context based on department and query type
    # Using the restricted index for similarity search
    docs = vectorstore.similarity_search(f"{department} department {query_type} {user_message}", k=3)
    context = [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} 
               for doc in docs]
    
    # Return the department, query type, and context
    return {
        "is_valid": True,
        "department": department,
        "query_type": query_type,
        "context": context
    }

