from typing import Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

# Define the state for our graph
class State(TypedDict):
    messages: Annotated[list, add_messages]
    context: List[Dict[str, Any]]
    department: Optional[str]
    track: Optional[str]
    query_type: Optional[str]
