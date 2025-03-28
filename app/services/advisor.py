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

def process_query(query_text: str) -> QueryResponse:
    """
    Process a student query and generate a response
    """
    try:
        # Create the chat graph
        graph = build_graph()
        
        # Create the initial state
        state = {
            "messages": [{"role": "user", "content": query_text}],
            "is_valid": True,
        }
        
        # Execute the graph
        result = graph.invoke(state)
        
        # Extract the response from the final state
        if "messages" in result and len(result["messages"]) > 0:
            response_content = result["messages"][-1].content
        else:
            response_content = "I'm sorry, I couldn't process your request."
            
        # Get context if available
        context = result.get("context", [])
        
        return QueryResponse(
            response=response_content,
            context=context
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise

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
