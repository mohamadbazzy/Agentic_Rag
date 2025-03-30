from langgraph.graph import StateGraph, START, END
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

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model_name="gpt-4o"
)

# Get a dedicated vector store for advisor
advisor_vectorstore = get_agent_vectorstore("advisor")

def process_query(text):
    """Process user query and return appropriate response"""
    try:
        # Create a simple state with the user message
        state = {"messages": [{"role": "user", "content": text}]}
        
        # Determine the department
        department = determine_department(text)
        
        # Process based on department
        if department == "Chemical Engineering and Advanced Energy (CHEE)":
            result = chemical_department(state)
            print(f"Raw result from department handler: {type(result)}")
            if isinstance(result, dict):
                print(f"Keys in result: {result.keys()}")
                if "messages" in result:
                    print(f"Type of messages: {type(result['messages'])}")
                    print(f"Messages content: {result['messages']}")
            content = extract_content_from_llm_response(result)
            print(f"Department Handler Result: {result}")
            print(f"Extracted Content: {content}")
            return {
                "content": content,
                "department": result["department"] if "department" in result else "MSFEA Advisor"
            }
        elif department == "Mechanical Engineering (MECH)":
            result = mechanical_department(state)
            content = extract_content_from_llm_response(result)
            print(f"Department Handler Result: {result}")
            print(f"Extracted Content: {content}")
            return {
                "content": content,
                "department": result["department"] if "department" in result else "MSFEA Advisor"
            }
        elif department == "Civil and Environmental Engineering (CEE)":
            result = civil_department(state)
            content = extract_content_from_llm_response(result)
            print(f"Department Handler Result: {result}")
            print(f"Extracted Content: {content}")
            return {
                "content": content,
                "department": result["department"] if "department" in result else "MSFEA Advisor"
            }
        elif department == "Electrical and Computer Engineering (ECE)":
            result = ece_department(state)
            content = extract_content_from_llm_response(result)
            print(f"Department Handler Result: {result}")
            print(f"Extracted Content: {content}")
            return {
                "content": content,
                "department": result["department"] if "department" in result else "MSFEA Advisor"
            }
        elif department == "Industrial Engineering and Management (ENMG)":
            result = industrial_department(state)
            content = extract_content_from_llm_response(result)
            print(f"Department Handler Result: {result}")
            print(f"Extracted Content: {content}")
            return {
                "content": content,
                "department": result["department"] if "department" in result else "MSFEA Advisor"
            }
        else:
            # Use the MSFEA advisor for general queries
            result = msfea_advisor(state)
            content = extract_content_from_llm_response(result)
            print(f"Department Handler Result: {result}")
            print(f"Extracted Content: {content}")
            return {
                "content": content,
                "department": result["department"] if "department" in result else "MSFEA Advisor"
            }
    except Exception as e:
        logger.error(f"Error in process_query: {str(e)}", exc_info=True)
        return {
            "content": "I apologize, but I encountered an error while processing your question. Please try again or ask something different.",
            "department": "MSFEA Advisor"
        }

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
            "Invalid": END
        }
    )
    
    # Add conditional edges for ECE routes
    graph.add_conditional_edges(
        "ece",
        route_to_ece_track,
        {
            "CSE": "cse",
            "CCE": "cce",
            "ECE": "ece_track"
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
    
    return graph.compile()

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
