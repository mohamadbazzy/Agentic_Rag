from langgraph.graph import StateGraph, START, END
from app.models.schemas import State
from app.services.supervisor import supervisor
from app.services.departments.chemical import chemical_department
from app.services.departments.mechanical import mechanical_department
from app.services.departments.civil import civil_department
from app.services.departments.ece import ece_department
from app.services.departments.msfea_advisor import msfea_advisor
from app.services.tracks.cse import cse_track
from app.services.tracks.ece import ece_track
from app.services.tracks.cce import cce_track
from app.services.routing import route_to_department, route_to_ece_track

def create_advisor_graph():
    """Create the LangGraph for the academic advisor system"""
    # Build the graph
    graph_builder = StateGraph(State)

    # Add nodes to the graph
    graph_builder.add_node("supervisor", supervisor)
    graph_builder.add_node("msfea_advisor", msfea_advisor)
    graph_builder.add_node("chemical_department", chemical_department)
    graph_builder.add_node("mechanical_department", mechanical_department)
    graph_builder.add_node("civil_department", civil_department)
    graph_builder.add_node("ece_department", ece_department)
    graph_builder.add_node("cse_track", cse_track)
    graph_builder.add_node("ece_track", ece_track)
    graph_builder.add_node("cce_track", cce_track)

    # Add edges to the graph
    graph_builder.add_edge(START, "supervisor")
    graph_builder.add_conditional_edges(
        "supervisor",
        route_to_department,
        {
            "msfea_advisor": "msfea_advisor",
            "chemical_department": "chemical_department",
            "mechanical_department": "mechanical_department",
            "civil_department": "civil_department",
            "ece_department": "ece_department"
        }
    )

    graph_builder.add_conditional_edges(
        "ece_department",
        route_to_ece_track,
        {
            "cse_track": "cse_track",
            "ece_track": "ece_track",
            "cce_track": "cce_track"
        }
    )

    # Connect all final nodes to END
    graph_builder.add_edge("msfea_advisor", END)
    graph_builder.add_edge("chemical_department", END)
    graph_builder.add_edge("mechanical_department", END)
    graph_builder.add_edge("civil_department", END)
    graph_builder.add_edge("cse_track", END)
    graph_builder.add_edge("ece_track", END)
    graph_builder.add_edge("cce_track", END)

    # Compile the graph
    return graph_builder.compile()

# Create the advisor graph
advisor_graph = create_advisor_graph()

def process_query(user_input: str):
    """Process a user query through the advisor graph"""
    # Initialize state with empty values
    initial_state = {
        "messages": [{"role": "user", "content": user_input}],
        "context": [],
        "department": None,
        "track": None,
        "query_type": None
    }
    
    # Process through the graph
    result = None
    department = None
    query_type = None
    
    for event in advisor_graph.stream(initial_state):
        # Check if supervisor returned an invalid query response
        if "supervisor" in event:
            supervisor_result = event["supervisor"]
            
            # If supervisor returned a direct response (invalid query), return it immediately
            if "is_valid" in supervisor_result and supervisor_result["is_valid"] is False:
                return {
                    "response": supervisor_result["response"],
                    "department": "MSFEA",  # Use MSFEA instead of "Invalid"
                    "query_type": "General"  # Use General instead of "Invalid Query"
                }
                
            # Otherwise get the department and query type
            department = supervisor_result.get("department", "MSFEA")
            query_type = supervisor_result.get("query_type", "General")
            
        # Get the final assistant response
        if any(node in event.keys() for node in ["msfea_advisor", "chemical_department", "mechanical_department", "civil_department", "cse_track", "ece_track", "cce_track"]):
            for node in ["msfea_advisor", "chemical_department", "mechanical_department", "civil_department", "cse_track", "ece_track", "cce_track"]:
                if node in event.keys():
                    result = event[node]["messages"].content
    
    # Perform final clean-up to ensure consistent department names
    if department and "invalid" in department.lower():
        department = "MSFEA"
    if query_type and "invalid" in query_type.lower():
        query_type = "General"
    
    # For msfea_advisor node, ensure department is MSFEA
    if any(node_name in ["msfea_advisor"] for node_name in event.keys()):
        department = "MSFEA"
    
    return {
        "response": result,
        "department": department,
        "query_type": query_type
    }
