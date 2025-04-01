from typing import Dict, Any, Union, List
from app.models.schemas import State

def ensure_compatible_state(state_obj: Any) -> Dict[str, Any]:
    """
    Ensures the state object is compatible with all handlers by converting
    it to a standard dictionary format with required keys.
    
    Args:
        state_obj: Can be a State object, dictionary, string, or any other input
        
    Returns:
        Dict with standardized format containing at minimum a 'messages' key
    """
    # Case 1: It's already a dictionary with messages
    if isinstance(state_obj, dict) and "messages" in state_obj:
        return state_obj
        
    # Case 2: It's a string (like a single message)
    elif isinstance(state_obj, str):
        return {"messages": [{"role": "user", "content": state_obj}]}
        
    # Case 3: It has a messages attribute (like a State object or similar)
    elif hasattr(state_obj, 'messages'):
        # Convert object's messages to dict representation
        try:
            messages = state_obj.messages
            return {"messages": messages}
        except:
            # Fallback if access fails
            return {"messages": []}
    
    # Case 4: Unknown/unsupported type
    else:
        return {"messages": []}

def get_last_user_message(state: Dict[str, Any]) -> str:
    """
    Safely extracts the last user message from a state object
    
    Args:
        state: A state dictionary with 'messages' key
        
    Returns:
        The content of the last user message, or empty string if none found
    """
    try:
        if "messages" in state and len(state["messages"]) > 0:
            # Find the last message with role=user
            user_messages = [m for m in state["messages"] if m.get("role") == "user"]
            if user_messages:
                return user_messages[-1].get("content", "")
        return ""
    except Exception:
        return ""

def add_message_to_state(state: Dict[str, Any], role: str, content: str) -> Dict[str, Any]:
    """
    Safely adds a new message to a state object
    
    Args:
        state: A state dictionary
        role: The role of the message sender (e.g., 'user', 'assistant')
        content: The message content
        
    Returns:
        Updated state dictionary with the new message added
    """
    state = ensure_compatible_state(state)
    if "messages" not in state:
        state["messages"] = []
        
    state["messages"].append({"role": role, "content": content})
    return state 