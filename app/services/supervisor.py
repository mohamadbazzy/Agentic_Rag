from langchain_openai import ChatOpenAI
from app.core.config import OPENAI_API_KEY
from app.models.schemas import State
from app.db.vector_store import vectorstore

# Initialize OpenAI LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model_name="gpt-3.5-turbo"
)

def supervisor(state: State):
    """
    Main supervisor node that determines which department the query is about
    and routes to the appropriate department node
    """
    # Get the latest user message
    user_message = state["messages"][-1].content
    
    # Use the LLM to determine which department the query is about
    prompt = f"""
    Determine which engineering department this query is about:
    Query: {user_message}
    
    Choose from: Chemical, Mechanical, Civil, ECE (Electrical and Computer Engineering)
    If the query is general or doesn't specify a department or is about the faculty in general, Answer as "MSFEA Advisor".
    If the query doesn't specify a department, but is clearly about a specific department, choose the most relevant one.
    If the query is about the MSFEA program in general, answer as "MSFEA Advisor".
    If the query is empty, answer as "MSFEA Advisor".

    Return only the department name without any explanation.
    """
    
    department_response = llm.invoke([{"role": "user", "content": prompt}])
    department = department_response.content.strip()
    
    # Also determine the general type of query
    query_type_prompt = f"""
    Determine what type of information the student is looking for:
    Query: {user_message}
    
    Choose from: 
    - Curriculum (courses, requirements)
    - Career (job prospects, internships)
    - Admission (requirements, process)
    - Faculty (professors, research)
    - General (overview, comparison)
    
    Return only the query type without any explanation.
    """
    
    query_type_response = llm.invoke([{"role": "user", "content": query_type_prompt}])
    query_type = query_type_response.content.strip()
    
    # Retrieve context based on department and query type
    docs = vectorstore.similarity_search(f"{department} department {query_type} {user_message}", k=3)
    context = [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} 
               for doc in docs]
    
    return {
        "department": department,
        "query_type": query_type,
        "context": context
    }
