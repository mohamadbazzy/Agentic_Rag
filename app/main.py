from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response as FastAPIResponse
from app.api.router import api_router
from app.models.schemas import State, QueryRequest
from app.services.routing import route_to_department
from app.services.advisor import process_query as advisor
from app.services.advisor import memory as advisor_memory
from app.services.whatsapp_handler import handle_whatsapp_message
from app.services.utils import ensure_compatible_state, add_message_to_state
import logging
from twilio.twiml.messaging_response import MessagingResponse
import json
import uuid
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Academic Advisor API",
    description="API for the Academic Advisor System",
    version="0.1.0",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only. In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_router, prefix="/api")

# Simple in-memory store for WhatsApp sessions
whatsapp_sessions = {}

def get_messages(state_obj):
    """Safely get messages from either a TypedDict State or a regular dict"""
    if isinstance(state_obj, dict):
        return state_obj.get('messages', [])
    return []

def set_messages(state_obj, messages):
    """Safely set messages in either a TypedDict State or a regular dict"""
    if isinstance(state_obj, dict):
        state_obj['messages'] = messages
    return state_obj

def ensure_state(obj):
    """Ensure the object is a proper State object"""
    if isinstance(obj, State):
        return obj
    elif isinstance(obj, dict) and "messages" in obj:
        return State(messages=obj["messages"])
    else:
        return State(messages=[])

# Helper function to safely check if a session exists
def session_exists(session_id):
    """Safely check if a session exists in memory"""
    try:
        # First try to use exists method if available
        if hasattr(advisor_memory, 'exists'):
            return advisor_memory.exists(session_id)
        
        # Otherwise try to get the session and see if it succeeds
        try:
            advisor_memory.get(session_id)
            return True
        except:
            return False
    except Exception as e:
        logger.error(f"Error checking session existence: {str(e)}")
        return False

@app.get("/")
async def root():
    return {"message": "Welcome to the Academic Advisor API"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"},
    )

@app.post("/api/reset")
async def reset():
    # Add logic to reset the conversation state
    return {"message": "Conversation reset successfully"}

@app.post("/api/query")
async def query(query_request: QueryRequest, request: Request):
    """
    Process a query and generate a response
    """
    try:
        # Extract session_id from cookies or headers, or generate a new one
        session_id = request.cookies.get("session_id") or request.headers.get("X-Session-ID")
        is_new_session = False
        
        if not session_id:
            # Generate a new session ID
            session_id = str(uuid.uuid4())
            is_new_session = True
            logger.info(f"Created new session: {session_id}")
        else:
            logger.info(f"Using existing session: {session_id}")
        
        # Process the query with the session ID
        response = advisor(query_request.text, session_id)
        
        # Create the response
        response_obj = JSONResponse(content=response.dict())
        
        # Set the session cookie if it's a new session
        if is_new_session:
            response_obj.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                max_age=86400 * 7,  # 7 days
                samesite="lax"
            )
        
        return response_obj
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"An error occurred: {str(e)}"}
        )

@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    try:
        # Debug log
        logger.info("WhatsApp webhook called!")
        
        # Get form data from the Twilio request
        form_data = await request.form()
        
        # Extract the message and sender info
        incoming_msg = form_data.get('Body', '').strip()
        sender = form_data.get('From', '')
        
        logger.info(f"Received message: '{incoming_msg}' from {sender}")
        
        # Handle reset command
        if incoming_msg.lower() in ["reset", "restart", "start over"]:
            # We'll use the sender as the session ID
            # The memory will be automatically reset on the next query
            response = MessagingResponse()
            response.message("Conversation has been reset. How can I help you with your academic inquiries?")
            return FastAPIResponse(content=str(response), media_type="application/xml")
        
        # Use the sender phone number as the session ID
        session_id = sender
        
        try:
            # Process the message with the LangGraph memory system
            response_obj = advisor(incoming_msg, session_id)
            response_text = response_obj.content
            
            # Format and return response
            response = MessagingResponse()
            response.message(response_text)
            
            logger.info(f"Sending WhatsApp response: {str(response)}")
            return FastAPIResponse(content=str(response), media_type="application/xml")
            
        except Exception as e:
            logger.error(f"Error calling advisor: {str(e)}")
            # Create a fallback response
            response = MessagingResponse()
            response.message(f"Sorry, I encountered an error processing your question: {str(e)}")
            return FastAPIResponse(content=str(response), media_type="application/xml")
            
    except Exception as e:
        import traceback
        logger.error(f"Error in WhatsApp webhook: {str(e)}")
        logger.error(traceback.format_exc())
        
        response = MessagingResponse()
        response.message("I apologize, but I encountered an error. Please try again or type 'reset' to start over.")
        return FastAPIResponse(content=str(response), media_type="application/xml")

@app.post("/api/reset/{session_id}")
async def reset_session(session_id: str):
    """
    Reset a conversation session
    """
    try:
        # Check if the session exists
        if session_exists(session_id):
            # Delete the session from memory
            try:
                if hasattr(advisor_memory, 'delete'):
                    advisor_memory.delete(session_id)
                # If delete is not supported, we can try other approaches
                # like putting an empty state
                else:
                    empty_state = {
                        "messages": [],
                        "is_valid": True,
                    }
                    advisor_memory.put(session_id, empty_state)
                
                return {"message": f"Session {session_id} reset successfully"}
            except Exception as e:
                logger.error(f"Error deleting session: {str(e)}")
                return {"message": f"Session {session_id} could not be fully reset: {str(e)}"}
        else:
            return {"message": f"Session {session_id} not found or already reset"}
            
    except Exception as e:
        logger.error(f"Error resetting session: {str(e)}")
        return JSONResponse(
            status_code=500, 
            content={"detail": f"An error occurred while resetting the session: {str(e)}"}
        )

# Additional routes as needed
