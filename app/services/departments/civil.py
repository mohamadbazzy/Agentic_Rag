from langchain_openai import ChatOpenAI
from app.core.config import OPENAI_API_KEY
from app.models.schemas import State

# Initialize OpenAI LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model_name="gpt-3.5-turbo"
)

def civil_department(state: State):
    """Handle queries about the Civil Engineering department"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    context = state.get("context", [])
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the Civil and Environmental Engineering (CEE) department at AUB's Maroun Semaan Faculty of Engineering and Architecture (MSFEA).
    
    The student is asking about: {query_type}
    
    IMPORTANT: Only answer questions specifically related to Civil and Environmental Engineering. If the question involves other departments, politely explain that you can only advise on CEE matters and suggest they consult the appropriate department advisor.
    
    Department Specifics:
    - The department offers a BE in Civil Engineering (accredited by ABET)
    - Master's programs include ME in Civil Engineering with various specializations
    - PhD in Civil Engineering is available
    - Focus areas include: structural engineering, construction management, transportation, water resources, geotechnical, and environmental engineering
    
    Use the following information to help answer their question:
    {context_str}
    
    Important: Only answer from the information provided. If you don't know the answer, say so.

    Respond in a professional, helpful manner appropriate for an academic advisor at AUB.
    """
    
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    response = llm.invoke(messages)
    
    return {"messages": response}
