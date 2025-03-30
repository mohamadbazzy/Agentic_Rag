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

# Get a dedicated vector store for mechanical department
mechanical_vectorstore = get_agent_vectorstore("mechanical")

def mechanical_department(state: State):
    """Handle queries about the Mechanical Engineering department"""
    user_message = state["messages"][-1]["content"]
    query_type = state.get("query_type", "General")
    
    # Always retrieve from mechanical's namespace, regardless of passed context
    # More specific search query to target mechanical engineering content
    search_query = f"Mechanical Engineering: {query_type} - {user_message}"
    
    try:
        # Debug output to track the search
        logger.info(f"Searching mechanical_namespace with query: {search_query}")
        
        # Ensure we're using the correct vectorstore and namespace
        mech_docs = mechanical_vectorstore.similarity_search(
            search_query, 
            k=3,
            namespace="mechanical_namespace",  # Explicitly specify namespace
            filter={"department": "mechanical"}  # Add a filter for mechanical department
        )
        
        logger.info(f"Found {len(mech_docs)} documents in mechanical_namespace")
        
        if mech_docs:
            context = [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} 
                    for doc in mech_docs]
        else:
            # Fallback to hardcoded information if no docs found
            logger.warning("No documents found in mechanical_namespace, using fallback content")
            context = [{
                "content": """
                The Mechanical Engineering department at AUB offers ABET-accredited BE degrees, 
                as well as ME and PhD programs. Focus areas include thermofluids, design, 
                materials, manufacturing, and mechatronics. The department is known for its 
                strong research programs and industry connections.
                """,
                "source": "fallback_info"
            }]
    except Exception as e:
        logger.error(f"Error retrieving documents from mechanical_namespace: {str(e)}")
        # Use fallback content in case of error
        context = [{
            "content": "Basic information about Mechanical Engineering at AUB's MSFEA faculty.",
            "source": "error_fallback"
        }]
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the Mechanical Engineering (MECH) department at AUB's Maroun Semaan Faculty of Engineering and Architecture (MSFEA).
    
    The student is asking about: {query_type}
    
    IMPORTANT: Only answer questions specifically related to Mechanical Engineering. If the question involves other departments, politely explain that you can only advise on MECH matters and suggest they consult the appropriate department advisor.
    
    Department Specifics:
    - The department offers a BE in Mechanical Engineering (accredited by ABET)
    - Master's programs include ME in Mechanical Engineering, Applied Energy, and Energy Studies
    - PhD in Mechanical Engineering is available

    
    Use the following information to help answer their question:
    {context_str}
    

    If you don't have specific information requested, provide general guidance about Mechanical Engineering at AUB while acknowledging the limits of your knowledge.
    Important: answer only from the context provided and don't make up any information
    Respond in a professional, helpful manner appropriate for an academic advisor at AUB.
    """
    
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    response = llm.invoke(messages)
    
    return {
        "messages": response,
        "department": "Mechanical Engineering (MECH)"
    }
