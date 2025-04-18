from langchain_openai import ChatOpenAI
from app.core.config import OPENAI_API_KEY
from app.models.schemas import State
from app.db.vector_store import get_agent_vectorstore
import logging
from app.services.utils import get_last_user_message

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model_name="gpt-4o"
)

# Get a dedicated vector store for MSFEA advisor
msfea_advisor_vectorstore = get_agent_vectorstore("msfea_advisor")

def msfea_advisor(state: State):
    """Handle general queries about the Maroun Semaan Faculty of Engineering and Architecture"""
    # Safely get the user message
    user_message = get_last_user_message(state)
    query_type = state.get("query_type", "General")
    
    # Always retrieve from MSFEA advisor's namespace, regardless of passed context
    search_query = f"MSFEA Faculty: {query_type} - {user_message}"
    
    try:
        # Debug output to track the search
        logger.info(f"Searching msfea_advisor_namespace with query: {search_query}")
        
        # Ensure we're using the correct vectorstore and namespace
        msfea_docs = msfea_advisor_vectorstore.similarity_search(
            search_query, 
            k=3,
            namespace="msfea_advisor_namespace",  # Explicitly specify namespace
        )
        
        logger.info(f"Found {len(msfea_docs)} documents in msfea_advisor_namespace")
        
        if msfea_docs:
            context = [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} 
                    for doc in msfea_docs]
        else:
            # Fallback to hardcoded information if no docs found
            logger.warning("No documents found in msfea_advisor_namespace, using fallback content")
            context = [{
                "content": """
                The Maroun Semaan Faculty of Engineering and Architecture (MSFEA) at AUB houses 7 departments:
                Architecture and Design (ARCH), Biomedical Engineering (BMEN), Civil and Environmental Engineering (CEE),
                Chemical Engineering and Advanced Energy (CHEE), Electrical and Computer Engineering (ECE),
                Industrial Engineering and Management (ENMG), and Mechanical Engineering (MECH).
                Each department offers Bachelor of Engineering degrees (BE), all accredited by ABET.
                """,
                "source": "fallback_info"
            }]
    except Exception as e:
        logger.error(f"Error retrieving documents from msfea_advisor_namespace: {str(e)}")
        # Use fallback content in case of error
        context = [{
            "content": "Basic information about the Maroun Semaan Faculty of Engineering and Architecture at AUB.",
            "source": "error_fallback"
        }]
    
    context_str = "\n".join([item["content"] for item in context])
    
    logger.info(f"Constructed context_str: {context_str[:500]}...") # Log the context string (truncated)

    system_message = f"""
    You are the main academic advisor for the Maroun Semaan Faculty of Engineering and Architecture (MSFEA) at the American University of Beirut (AUB).
    
    The student is asking about: "{user_message}"
    
    IMPORTANT: Your role is to provide general information about MSFEA as a whole. You should give balanced information that covers ALL departments when relevant, not favoring any single department. For very department-specific questions, suggest consulting the appropriate department advisor.
    
    MSFEA Faculty Specifics:
    - MSFEA houses 7 departments: Architecture and Design (ARCH), Biomedical Engineering (BMEN), Civil and Environmental Engineering (CEE), Chemical Engineering and Advanced Energy (CHEE), Electrical and Computer Engineering (ECE), Industrial Engineering and Management (ENMG), and Mechanical Engineering (MECH)
    - Each department offers Bachelor of Engineering degrees (BE), all accredited by ABET
    - MSFEA offers various master's programs across all departments
    - PhD programs are available in all engineering disciplines
    - MSFEA is renowned for its rigorous curriculum, distinguished faculty, and state-of-the-art facilities
    
    For degree programs:
    - Undergraduate: All engineering departments offer ABET-accredited BE degrees (typically 143-144 credits)
    - Masters: ME (professional) and MS (research-focused) degrees available in all departments
    - PhD: Available in all engineering disciplines
    - Various minors and certificate programs are also available
    
    For admissions queries:
    - Undergraduate admissions are competitive based on high school grades, SAT scores, and English proficiency
    - Graduate admissions require a bachelor's degree in relevant field, strong GPA, GRE (for some programs), and English proficiency
    - Fall and spring admission cycles are available for most programs
    
    For departmental overviews:
    - Architecture and Design (ARCH): Focuses on architectural design, urbanism, and graphic design
    - Biomedical Engineering (BMEN): Combines engineering with medical sciences for healthcare applications
    - Civil and Environmental Engineering (CEE): Covers infrastructure, structural engineering, water resources, environmental engineering
    - Chemical Engineering (CHEE): Focuses on chemical processes, petroleum, and advanced energy
    - Electrical and Computer Engineering (ECE): Includes electrical engineering, computer engineering with CSE and CCE tracks
    - Industrial Engineering (ENMG): Covers operations research, management, and production systems
    - Mechanical Engineering (MECH): Includes thermofluids, design, materials, and manufacturing
    
    Use the following information to help answer their question:
    {context_str}

    If the question is to calculate the GPA of a student, you should use the following formula:
    A+ : 4.3
    A : 4
    A- : 3.7
    B+ : 3.3
    B : 3
    B- : 2.7
    C+ : 2.3
    C : 2
    C- : 1.7
    D+ : 1.3
    D : 1
    F : 0
    Only output the GPA as a number, Saying your GPA IS ... and as a letter grade it is...
    Important: Only answer from the information provided. If you don't know the answer, say so.
    
    Respond in a professional, helpful manner appropriate for an academic advisor at AUB.
    """

    logger.info(f"Final system_message (check for context): {system_message[:500]}...") # Log the final prompt (truncated)

    # Assume LLM call happens shortly after this
    # Example structure (actual call might differ slightly):
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    
    # Get thread_id from configurable state if available (for conversation memory)
    thread_id = None
    if hasattr(state, "get") and callable(state.get):
        config = state.get("configurable", {})
        if isinstance(config, dict):
            thread_id = config.get("thread_id")

    # Invoke the LLM
    if thread_id:
        response = llm.invoke(messages, config={"configurable": {"thread_id": f"{thread_id}_msfea"}}) 
    else:
        response = llm.invoke(messages)

    # Update the state with the response
    state["messages"] = state["messages"] + [{"role": "assistant", "content": response.content}]
    state["response"] = response.content  # Store the latest response
    state["department"] = "MSFEA Advisor" # Set the department context

    return state # Return the updated state