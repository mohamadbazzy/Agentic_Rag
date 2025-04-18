from app.models.schemas import State

def route_to_department(state: State):
    """Route to the appropriate department based on the determined department"""
    # Check if the query was marked as invalid by the supervisor
    if state.get("is_valid") is False:
        return "Invalid"
        
    department = state.get("department", "").lower()
    
    # Also check for invalid in the department name
    if "invalid" in department.lower():
        return "Invalid"

    # Route to the appropriate department FIRST
    if any(term in department.lower() for term in [
  "msfea advisor", "msfea", "general", "faculty", "advisor", "dates", "end", "start", "calendar",
  "semester",
  "break",          # covers queries like "fall semester", "spring semester"
  "exams",             # covers "final exams", "exam schedule"
  "holidays",          # essential for breaks and religious holidays
  "reading period",    # highly searched before exams
  "vacation",          # includes "Christmas vacation", etc.
  "graduation",        # commencement-related questions
  "opening ceremony",  # specific institutional event
  "commencement",      # graduation event
  "finals",            # common student shorthand for final exams
  "term dates"         # captures "term start/end" queries
]):
        return "MSFEA Advisor"
    elif "chemical" in department:
        return "Chemical Engineering and Advanced Energy (CHEE)"
    elif "mechanical" in department:
        return "Mechanical Engineering (MECH)"
    elif "civil" in department:
        return "Civil and Environmental Engineering (CEE)"
    elif any(term in department for term in ["industrial", "enmg", "management"]):
        return "Industrial Engineering and Management (ENMG)"
    elif any(term in department for term in ["ece", "electrical", "computer", "electronic"]):
        return "Electrical and Computer Engineering (ECE)"
    # Check for schedule helper keywords AFTER specific departments
    elif any(term in department.lower() for term in ["schedule", "timetable", "class time", "course time", "scheduling", "class schedule", "course schedule", "class timetable", "course timetable"]):
        return "Schedule Helper"
    else:
        # Default to MSFEA Advisor if unclear
        return "MSFEA Advisor"

def route_to_ece_track(state: State):
    """Route to the appropriate ECE track based on the determined track"""
    track = state.get("track", "").upper()  # Convert to uppercase for consistency
    
    # Be more lenient with matching - look for substrings
    if "CSE" in track:
        return "cse"
    elif "CCE" in track:
        return "cce"
    else:
        # Default to general ECE track if no specific track is detected
        return "ece_track"
