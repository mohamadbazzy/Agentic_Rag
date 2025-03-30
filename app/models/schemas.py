from typing import Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pydantic import BaseModel

# Define the state for our graph
class State(TypedDict):
    messages: Annotated[list, add_messages]
    context: List[Dict[str, Any]]
    department: Optional[str]
    track: Optional[str]
    query_type: Optional[str]

# New models for API request/response
class QueryRequest(BaseModel):
    """Model for incoming query requests"""
    text: str
    
class QueryResponse(BaseModel):
    """Model for query responses"""
    content: str
    department: Optional[str] = "MSFEA Advisor"
    
    # Optional fields for additional data
    status: Optional[str] = None
    
class ErrorResponse(BaseModel):
    """Model for error responses"""
    detail: str
