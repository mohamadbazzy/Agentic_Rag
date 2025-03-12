from app.models.schemas import State

def route_to_department(state: State):
    """Route to the appropriate department based on the determined department"""
    department = state.get("department", "").lower()
    
    if "chemical" in department:
        return "chemical_department"
    elif "mechanical" in department:
        return "mechanical_department"
    elif "civil" in department:
        return "civil_department"
    elif "ece" in department or "electrical" in department or "computer" in department:
        return "ece_department"
    else:
        # Default to ECE if unclear
        return "ece_department"

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
