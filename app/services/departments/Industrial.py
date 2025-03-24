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

# Get a dedicated vector store for industrial department
industrial_vectorstore = get_agent_vectorstore("industrial")

def industrial_department(state: State):
    """Handle queries about the Industrial Engineering department"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    
    # Always retrieve from industrial's namespace, regardless of passed context
    search_query = f"Industrial Engineering: {query_type} - {user_message}"
    
    try:
        # Debug output to track the search
        logger.info(f"Searching industrial_namespace with query: {search_query}")
        
        # Ensure we're using the correct vectorstore and namespace
        industrial_docs = industrial_vectorstore.similarity_search(
            search_query, 
            k=3,
            namespace="industrial_namespace",  # Explicitly specify namespace
            filter={"department": "industrial"}  # Add a filter for industrial department
        )
        
        logger.info(f"Found {len(industrial_docs)} documents in industrial_namespace")
        
        if industrial_docs:
            context = [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} 
                    for doc in industrial_docs]
        else:
            # Fallback to hardcoded information if no docs found
            logger.warning("No documents found in industrial_namespace, using fallback content")
            context = [{
                "content": """
                The Industrial Engineering Program extends over a four-year period and is offered
                exclusively on a daytime, on-campus basis. The program is offered in eleven terms
                whereby eight terms are 16-week Fall/Spring semesters given over four years, and three
                terms are eight-week summer terms taken during the first three years of the program.
                In the summer term of the third year (Term IX), students are required to participate in a
                practical training program with a local, regional or international organization. The entire
                program is equivalent to five academic years but is completed in four calendar years
                with three summer terms.
                """,
                "source": "fallback_info"
            }]
    except Exception as e:
        logger.error(f"Error retrieving documents from industrial_namespace: {str(e)}")
        # Use fallback content in case of error
        context = [{
            "content": "Basic information about Industrial Engineering at AUB's MSFEA faculty.",
            "source": "error_fallback"
        }]
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the Industrial Engineering department at AUB's Maroun Semaan Faculty of Engineering and Architecture (MSFEA).
    
    The student is asking about: {query_type}
    
    IMPORTANT: Only answer questions specifically related to Industrial Engineering. If the question involves other departments, politely explain that you can only advise on ENMG matters and suggest they consult the appropriate department advisor.
    
    Answer the question based on the following information dont use any other information:
    {context_str}
    
    If you don't have specific information requested, provide general guidance about Industrial Engineering at AUB while acknowledging the limits of your knowledge.
    Important: answer only from the context provided and don't make up any information and tell the user to visit the department website for more information
    Respond in a professional, helpful manner appropriate for an academic advisor at AUB.
    """
    
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    response = llm.invoke(messages)
    
    return {"messages": response}
