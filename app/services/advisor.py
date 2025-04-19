from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.models.schemas import State
from app.services.supervisor import supervisor
from app.services.departments.chemical import chemical_department
from app.services.departments.mechanical import mechanical_department
from app.services.departments.civil import civil_department
from app.services.departments.ece import ece_department
from app.services.departments.msfea_advisor import msfea_advisor
from app.services.departments.Industrial import industrial_department
from app.services.tracks.cse import cse_track
from app.services.tracks.ece import ece_track
from app.services.tracks.cce import cce_track
from app.services.routing import route_to_department, route_to_ece_track
from app.services.schedule_helper import schedule_helper
from langchain_openai import ChatOpenAI
from app.core.config import OPENAI_API_KEY
from app.db.vector_store import vectorstore, get_agent_vectorstore
from app.models.schemas import QueryResponse
import logging
from app.services.utils import ensure_compatible_state, get_last_user_message
import re
import json

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model_name="gpt-4o"
)

# Get a dedicated vector store for advisor
advisor_vectorstore = get_agent_vectorstore("advisor")

# Create a memory saver for persistent conversation history
memory = MemorySaver()

# Add a function to detect calendar integration requests
def detect_calendar_request(message):
    """
    Detect if the user is asking to add their schedule to Google Calendar
    
    Args:
        message (str): The user's message
        
    Returns:
        bool: True if calendar integration is requested
    """
    # Keywords related to calendar integration
    calendar_keywords = [
        "add to google", "google calendar", "sync calendar", "add to calendar",
        "put in google", "save to google", "export to google", "google integration",
        "calendar integration", "sync with google", "add schedule to google"
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in calendar_keywords)

def process_query(query_text: str, session_id: str = None) -> QueryResponse:
    """
    Process a student query and generate a response
    
    Args:
        query_text: The query text from the user
        session_id: Optional session ID for retrieving conversation history
    """
    try:
        # Create the chat graph
        graph = build_graph()
        
        # Create the initial state or retrieve from memory if session_id is provided
        if session_id:
            # Try to safely check if session exists
            session_exists = False
            try:
                # First try to use exists method if available
                if hasattr(memory, 'exists'):
                    session_exists = memory.exists(session_id)
                else:
                    # Otherwise try to get the session and see if it succeeds
                    try:
                        memory.get(session_id)
                        session_exists = True
                    except:
                        session_exists = False
            except Exception as e:
                logger.error(f"Error checking session existence: {str(e)}")
                session_exists = False
                
            if session_exists:
                # Retrieve existing conversation state
                state = memory.get(session_id)
                # Add the new user message
                state["messages"].append({"role": "user", "content": query_text})
            else:
                # Create a new state
                state = {
                    "messages": [{"role": "user", "content": query_text}],
                    "is_valid": True,
                }
        else:
            # Create a new state
            state = {
                "messages": [{"role": "user", "content": query_text}],
                "is_valid": True,
            }
        
        # Execute the graph with the state
        result = graph.invoke(state, config={"configurable": {"thread_id": session_id}})
        
        # Save the updated state if session_id is provided
        if session_id:
            try:
                # Try the most common ways to call put() with different parameters
                try:
                    # Simple version first
                    memory.put(session_id, result)
                except TypeError:
                    try:
                        # Try with empty dicts for metadata and versions
                        memory.put(session_id, result, {}, {})
                    except TypeError:
                        # Try with pending_sends parameter
                        memory.put(session_id, result, {}, {}, pending_sends={})
            except Exception as e:
                # Just log the error but continue - the conversation will work
                # but won't be saved for next time
                logger.error(f"Error saving session: {str(e)}")
        
        # Extract the response content
        if "messages" in result and len(result["messages"]) > 0:
            response_content = result["messages"][-1].content
            
            # Check for schedule data
            schedule_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', response_content)
            if schedule_match:
                try:
                    schedule_data = json.loads(schedule_match.group(1))
                    if schedule_data.get('is_schedule') == True:
                        # Add indication about Google Calendar
                        response_content = response_content.replace(
                            "```json", 
                            "You can add this schedule to your Google Calendar by clicking the 'Add to Google Calendar' button below.\n\n```json"
                        )
                except Exception as e:
                    logger.error(f"Error processing schedule data: {str(e)}")
        else:
            response_content = "I'm sorry, I couldn't process your request."
        
        # Get the routing path
        path = result.get("path", [])
        department = determine_department_from_path(path)
        
        # Check if the user is asking to add their schedule to Google Calendar
        if detect_calendar_request(query_text):
            # Create a response with instructions on how to add to Google Calendar
            calendar_info = {
                "content": (
                    "I'd be happy to help you add your class schedule to your Google Calendar! "
                    "To do this, I need your permission to access your Google Calendar. "
                    "\n\n"
                    "First, let me know if you have a specific schedule you want to add, or if you want "
                    "to add the schedule we've discussed. When you're ready, click the 'Add to Google Calendar' "
                    "button that appears with your schedule, and you'll be asked to sign in to your Google account. "
                    "\n\n"
                    "Once you grant permission, I'll add all your classes as recurring events to your calendar. "
                    "I'll also check for any potential conflicts with your existing calendar events."
                ),
                "department": "MSFEA Advisor"
            }
            return calendar_info
        
        # Create response with path info
        return QueryResponse(
            content=response_content,
            department=department,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return QueryResponse(
            content=f"I apologize, but an error occurred: {str(e)}",
            department="Error Handler"
        )

def extract_content_from_llm_response(result):
    """Extract content from LLM response"""
    try:
        print(f"Extracting content from: {type(result)}")
        
        # If result is a dictionary with 'messages' key
        if isinstance(result, dict) and 'messages' in result:
            messages = result['messages']
            print(f"Found messages: {type(messages)}")
            
            # Check if messages is an AIMessage object (from langchain)
            if hasattr(messages, 'content'):
                # This is for langchain AIMessage objects
                return messages.content
                
            # If messages is a list, get the last one
            elif isinstance(messages, list) and len(messages) > 0:
                last_message = messages[-1]
                if isinstance(last_message, dict) and 'content' in last_message:
                    return last_message['content']
        
        # Direct content in result
        if isinstance(result, dict) and 'content' in result:
            return result['content']
            
        return "No content available - extraction failed"
    except Exception as e:
        print(f"Error extracting content: {str(e)}")
        return "Error extracting response content"

def build_graph():
    """
    Build the agent workflow graph
    """
    # Create a new state graph
    graph = StateGraph(State)
    
    # Add nodes
    graph.add_node("supervisor", supervisor)
    graph.add_node("chemical", chemical_department)
    graph.add_node("mechanical", mechanical_department)
    graph.add_node("civil", civil_department)
    graph.add_node("ece", ece_department)
    graph.add_node("industrial", industrial_department)
    graph.add_node("msfea_advisor", msfea_advisor)
    graph.add_node("cse", cse_track)
    graph.add_node("cce", cce_track)
    graph.add_node("ece_track", ece_track)
    graph.add_node("schedule_helper", schedule_helper)
    graph.add_node("invalid_handler", invalid_query_handler)  # Add the new node
    
    # Define edges
    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_to_department,
        {
            "Chemical Engineering and Advanced Energy (CHEE)": "chemical",
            "Mechanical Engineering (MECH)": "mechanical",
            "Civil and Environmental Engineering (CEE)": "civil",
            "Industrial Engineering and Management (ENMG)": "industrial",
            "Electrical and Computer Engineering (ECE)": "ece",
            "MSFEA Advisor": "msfea_advisor",
            "Schedule Helper": "schedule_helper",
            "Invalid": "invalid_handler"  # Route to invalid_handler instead of END
        }
    )
    
    # Connect invalid_handler to END
    graph.add_edge("invalid_handler", END)
    
    # Add conditional edges for ECE routes
    graph.add_conditional_edges(
        "ece",
        route_to_ece_track,
        {
            "cse": "cse",
            "cce": "cce",
            "ece_track": "ece_track"
        }
    )
    
    # Connect all department nodes to END
    graph.add_edge("chemical", END)
    graph.add_edge("mechanical", END)
    graph.add_edge("civil", END)
    graph.add_edge("industrial", END)
    graph.add_edge("msfea_advisor", END)
    graph.add_edge("cse", END)
    graph.add_edge("cce", END)
    graph.add_edge("ece_track", END)
    
    # Compile the graph with memory checkpointer
    return graph.compile(checkpointer=memory)

def determine_department(text):
    """Determine which department the query is about"""
    text_lower = text.lower()
    
    if "chemical" in text_lower or "chee" in text_lower or "chen" in text_lower:
        return "Chemical Engineering and Advanced Energy (CHEE)"
    elif "mechanical" in text_lower or "mech" in text_lower:
        return "Mechanical Engineering (MECH)"
    elif "civil" in text_lower or "cee" in text_lower:
        return "Civil and Environmental Engineering (CEE)"
    elif "electrical" in text_lower or "computer" in text_lower or "ece" in text_lower:
        return "Electrical and Computer Engineering (ECE)"
    elif "industrial" in text_lower or "enmg" in text_lower:
        return "Industrial Engineering and Management (ENMG)"
    else:
        return "MSFEA Advisor"

def chemical_department_handler(text):
    """Basic handler for chemical engineering queries"""
    return "The Chemical Engineering and Advanced Energy (CHEE) department at AUB offers BE, ME, and PhD programs in Chemical Engineering. The department focuses on chemical processes, petroleum engineering, and advanced energy technologies."

def mechanical_department_handler(text):
    """Basic handler for mechanical engineering queries"""
    return "The Mechanical Engineering (MECH) department offers programs covering thermofluids, design, materials, and manufacturing. The department offers BE, ME, and PhD degrees, all accredited by ABET."

def civil_department_handler(text):
    """Basic handler for civil engineering queries"""
    return "The Civil and Environmental Engineering (CEE) department covers infrastructure, structural engineering, water resources, and environmental engineering. The department offers BE, ME, and PhD degrees."

def electrical_department_handler(text):
    """Basic handler for electrical engineering queries"""
    return "The Electrical and Computer Engineering (ECE) department includes electrical engineering and computer engineering with CSE and CCE tracks. The department offers BE, ME, and PhD degrees."

def industrial_department_handler(text):
    """Basic handler for industrial engineering queries"""
    return "The Industrial Engineering and Management (ENMG) department covers operations research, management, and production systems. The department offers BE, ME, and PhD degrees."

def msfea_advisor_handler(text):
    """Basic handler for general MSFEA queries"""
    return f"Thank you for your question about '{text}'. MSFEA houses 7 departments: Architecture and Design (ARCH), Biomedical Engineering (BMEN), Civil and Environmental Engineering (CEE), Chemical Engineering (CHEE), Electrical and Computer Engineering (ECE), Industrial Engineering (ENMG), and Mechanical Engineering (MECH). All departments offer accredited undergraduate and graduate programs."

def get_department_from_result(result):
    """Extract the department that handled the query from the result"""
    # Default department
    department = "MSFEA Advisor"
    
    # Check each department's name in the result path
    if "chemical" in result.get("path", []):
        department = "Chemical Engineering"
    elif "mechanical" in result.get("path", []):
        department = "Mechanical Engineering" 
    elif "civil" in result.get("path", []):
        department = "Civil Engineering"
    elif "ece" in result.get("path", []):
        department = "Electrical & Computer"
    elif "cse" in result.get("path", []):
        department = "Computer Science and Engineering"
    elif "cce" in result.get("path", []):
        department = "Computer and Communications Engineering"
    elif "industrial" in result.get("path", []):
        department = "Industrial Engineering"
    
    return department

def determine_department_from_path(path):
    """Extract department name from the graph execution path"""
    department = "MSFEA Advisor"  # Default
    
    # Map node names to user-friendly department names
    if not path:
        return department
        
    last_node = path[-1]
    
    # Department mapping
    department_map = {
        "chemical": "Chemical Engineering",
        "mechanical": "Mechanical Engineering",
        "civil": "Civil Engineering",
        "ece": "Electrical & Computer",
        "cse": "Computer Science Engineering",
        "cce": "Computer & Communications Engineering",
        "industrial": "Industrial Engineering",
        "invalid_handler": "Error Handler"
    }
    
    # Check for department in path
    for node in path:
        if node in department_map:
            department = department_map[node]
    
    return department

def invalid_query_handler(state: State):
    """Handle invalid queries and return appropriate error messages"""
    # Check if there's a response from the supervisor
    if "response" in state:
        # Add a message to the conversation with the response from the supervisor
        state["messages"].append({"role": "assistant", "content": state["response"]})
    else:
        # Fallback error message
        state["messages"].append({
            "role": "assistant", 
            "content": "Invalid query as the MSFEA advisor I can't answer such questions. Please ask a question related to engineering programs, courses, admissions, or career options."
        })
    return state
