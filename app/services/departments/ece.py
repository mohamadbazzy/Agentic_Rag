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
    
    track_response = llm.invoke([{"role": "user", "content": prompt}])
    track = track_response.content.strip()
    
    return {"track": track}
