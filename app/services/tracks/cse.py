from langchain_openai import ChatOpenAI
from app.core.config import OPENAI_API_KEY
from app.models.schemas import State

# Initialize OpenAI LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model_name="gpt-3.5-turbo"
)

def cse_track(state: State):
    """Handle queries about the Computer Systems Engineering track"""
    user_message = state["messages"][-1].content
    query_type = state.get("query_type", "General")
    context = state.get("context", [])
    
    context_str = "\n".join([item["content"] for item in context])
    
    system_message = f"""
    You are an academic advisor for the Computer Systems Engineering (CSE) track within the ECE department.
    
    The student is asking about: {query_type}
    
    Use the following information to help answer their question:
    {context_str}
    
    If you don't have specific information, provide general guidance about Computer Systems Engineering.
    Focus on topics like computer architecture, operating systems, embedded systems, and hardware-software integration.
    """
    
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    response = llm.invoke(messages)
    
    return {"messages": response}
