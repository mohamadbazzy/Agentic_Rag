from langchain_openai import ChatOpenAI
from app.core.config import OPENAI_API_KEY
from app.models.schemas import State

# Initialize OpenAI LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model_name="gpt-3.5-turbo"
)

def ece_department(state: State):
    """
    Handle queries about the ECE department and determine which track within ECE
    the query is about
    """
    user_message = state["messages"][-1].content
    
    # Determine which ECE track the query is about
    prompt = f"""
    Determine which track within the Electrical and Computer Engineering (ECE) department this query is about:
    Query: {user_message}
    
    Choose from: 
    - CSE (Computer Systems Engineering)
    - ECE (Electrical and Computer Engineering general)
    - CCE (Computer and Communications Engineering)
    
    If the query is general or doesn't specify a track, choose ECE.
    
    Return only the track abbreviation without any explanation.
    """
    
    track_response = llm.invoke([{"role": "user", "content": prompt}])
    track = track_response.content.strip()
    
    return {"track": track}
