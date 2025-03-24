from app.models.schemas import State

def route_to_department(state: State):
    """Route to the appropriate department based on the determined department"""
    department = state.get("department", "").lower()
    
    # Handle invalid queries (should never reach here as they're handled directly in process_query)
    if "invalid" in department.lower():
        return "Invalid"
    
    # Route to the appropriate department
    if any(term in department.lower() for term in ["msfea advisor", "msfea", "general", "faculty", "advisor"]):
        return "MSFEA Advisor"
    elif "chemical" in department:
        return "Chemical Engineering and Advanced Energy (CHEE)"
    elif "mechanical" in department:
        return "Mechanical Engineering (MECH)"
    elif "civil" in department:
        return "Civil and Environmental Engineering (CEE)"
    elif any(term in department for term in ["ece", "electrical", "computer", "electronic"]):
        return "Electrical and Computer Engineering (ECE)"
    else:
        # Default to MSFEA Advisor if unclear
        return "MSFEA Advisor"

def route_to_ece_track(state: State):
    """Route to the appropriate ECE track based on the determined track"""
    track = state.get("track", "").upper()
    
    if "CSE" in track:
        return "cse_track"
    elif "CCE" in track:
        return "cce_track"
    else:
        # Default to general ECE track
        return "ece_track"
