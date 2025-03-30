from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import QueryRequest, QueryResponse
from app.services.advisor import process_query
import logging

# Set up logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/query", response_model=None)
async def query_advisor(request: dict):
    """
    Process a student query through the academic advisor system
    """
    try:
        # Handle reset request
        if request.get("reset"):
            return {
                "content": "Chat history has been reset.",
                "department": "MSFEA Advisor",
                "status": "reset"
            }
        
        # Get text and language from request
        text = request.get("text", "")
        language = request.get("language", "english")
        
        # Very basic logging without logger dependency
        print(f"Processing query: {text} (language: {language})")
        
        try:
            # Process the query with your AI advisor logic
            result = process_query(text)
            print(f"Result from process_query: {result}")
            
            # Return result directly
            return result
        except Exception as inner_e:
            print(f"Error in process_query: {str(inner_e)}")
            return {
                "content": f"Error processing your query: {str(inner_e)}. Please try again.",
                "department": "MSFEA Advisor"
            }
            
    except Exception as e:
        # Return a friendly error message
        print(f"Error in query_advisor: {str(e)}")
        return {
            "content": "Sorry, there was an error processing your request. Please try again.",
            "department": "MSFEA Advisor"
        }

@router.post("/test", response_model=None)
async def test_advisor(request: dict):
    """
    A more comprehensive test endpoint that simulates a real conversation
    """
    # Handle reset request
    if request.get("reset"):
        return {
            "content": "Chat history has been reset.",
            "department": "MSFEA Advisor",
            "status": "reset"
        }
    
    text = request.get('text', '')
    
    # Sample responses for common questions
    responses = {
        "cse": "The Computer Science and Engineering (CSE) track is part of the ECE department. It focuses on computer architecture, hardware design, embedded systems, and IoT with a strong emphasis on hardware-software integration.",
        "mech": "The Mechanical Engineering department offers a BE in Mechanical Engineering accredited by ABET. The program covers thermofluids, design, materials, and manufacturing. Master's programs include ME in Mechanical Engineering, Applied Energy, and Energy Studies.",
        "civil": "The Civil and Environmental Engineering department covers infrastructure design, structural engineering, water resources, environmental engineering, and construction management. The programs are accredited by ABET.",
        "chemical": "The Chemical Engineering department focuses on chemical processes, petroleum engineering, and advanced energy technologies. Students learn process design, thermodynamics, and reaction engineering.",
        "electrical": "The Electrical and Computer Engineering department has multiple tracks including CSE and CCE. It covers topics from electronics and power systems to networking and embedded systems.",
        "industrial": "Industrial Engineering focuses on operations research, management, and production systems. The program prepares students to optimize complex systems and processes.",
        "requirements": "Requirements for engineering majors typically include core courses, technical electives, and general education requirements. Most programs require 143-144 credits for completion.",
        "majors": "MSFEA offers majors in Architecture and Design, Biomedical Engineering, Civil and Environmental Engineering, Chemical Engineering, Electrical and Computer Engineering, Industrial Engineering, and Mechanical Engineering.",
        "default": f"Thank you for your question about '{text}'. As the MSFEA Academic Advisor, I can provide information about departments, programs, courses, and academic policies at AUB's engineering faculty."
    }
    
    # Determine appropriate response
    response_content = responses["default"]
    department = "MSFEA Advisor"
    
    # Simple keyword matching
    text_lower = text.lower()
    if "cse" in text_lower or "computer science" in text_lower:
        response_content = responses["cse"]
        department = "Electrical & Computer"
    elif "mech" in text_lower or "mechanical" in text_lower:
        response_content = responses["mech"]
        department = "Mechanical Engineering"
    elif "civil" in text_lower or "cee" in text_lower:
        response_content = responses["civil"]
        department = "Civil Engineering"
    elif "chemical" in text_lower or "chee" in text_lower:
        response_content = responses["chemical"]
        department = "Chemical Engineering"
    elif "electrical" in text_lower or "ece" in text_lower:
        response_content = responses["electrical"]
        department = "Electrical & Computer"
    elif "industrial" in text_lower or "enmg" in text_lower:
        response_content = responses["industrial"]
        department = "Industrial Engineering"
    elif "requirement" in text_lower or "credits" in text_lower or "courses" in text_lower:
        response_content = responses["requirements"]
    elif "major" in text_lower or "program" in text_lower or "offered" in text_lower:
        response_content = responses["majors"]
    
    return {
        "content": response_content,
        "department": department
    }
