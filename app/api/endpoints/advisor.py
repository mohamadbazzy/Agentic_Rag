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
        
        # Process using the graph-based workflow
        result = process_query(text)
        
        # Return result in the expected format
        return result
            
    except Exception as e:
        # Return a friendly error message
        logger.error(f"Error in query_advisor: {str(e)}", exc_info=True)
        return {
            "content": "Sorry, there was an error processing your request. Please try again.",
            "department": "MSFEA Advisor"
        }
