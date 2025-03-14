from app.models.schemas import State

def route_to_department(state: State):
    """Route to the appropriate department based on the determined department"""
    department = state.get("department", "").lower()
    
    # Handle invalid queries (should never reach here as they're handled directly in process_query)
    if "invalid" in department.lower():
        return "msfea_advisor"  # Fallback to MSFEA advisor for invalid queries
    
    # Route to the appropriate department
    if any(term in department.lower() for term in ["msfea advisor", "msfea", "general", "faculty", "advisor"]):
        return "msfea_advisor"
    elif "chemical" in department:
        return "chemical_department"
    elif "mechanical" in department:
        return "mechanical_department"
    elif "civil" in department:
        return "civil_department"
    elif any(term in department for term in ["ece", "electrical", "computer", "electronic"]):
        return "ece_department"
    else:
        # Default to MSFEA Advisor if unclear
        return "msfea_advisor"

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
