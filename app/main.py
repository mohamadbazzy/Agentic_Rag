from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response as FastAPIResponse
from app.api.router import api_router
from app.models.schemas import State
from app.services.routing import route_to_department
from app.services.advisor import process_query as advisor
from app.services.whatsapp_handler import handle_whatsapp_message
from app.services.utils import ensure_compatible_state, add_message_to_state
import logging
from twilio.twiml.messaging_response import MessagingResponse
import json

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

# Simple in-memory store (replace with database in production)
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
            whatsapp_sessions[sender] = {"messages": []}
            response = MessagingResponse()
            response.message("Conversation has been reset. How can I help you with your academic inquiries?")
            return FastAPIResponse(content=str(response), media_type="application/xml")
        
        # Initialize session if needed
        if sender not in whatsapp_sessions:
            whatsapp_sessions[sender] = {"messages": []}
        
        # Add message to session using our utility
        whatsapp_sessions[sender] = add_message_to_state(
            whatsapp_sessions[sender], "user", incoming_msg
        )
            
        try:
            # Create a state-like object that's guaranteed to be compatible
            session_state = ensure_compatible_state(whatsapp_sessions[sender])

            # Use your handler function
            response_text = handle_whatsapp_message(incoming_msg, session_state)

            # Save conversation history
            whatsapp_sessions[sender] = add_message_to_state(
                whatsapp_sessions[sender], "assistant", response_text
            )

            # Format and return response
            response = MessagingResponse()
            response.message(response_text)

            # Add debugging log to see the actual response being sent
            logger.info(f"Sending WhatsApp response: {str(response)}")

            return FastAPIResponse(content=str(response), media_type="application/xml")
            
        except Exception as e:
            # Enhanced error logging
            logger.error(f"Error processing WhatsApp message: {str(e)}", exc_info=True)
            
            # Fallback for majors question - this seems to be the specific question that failed
            if "major" in incoming_msg.lower() or "program" in incoming_msg.lower() or "msfea" in incoming_msg.lower():
                response_data = {
                    "content": "MSFEA offers undergraduate majors in Architecture, Civil, Chemical, Electrical and Computer (with CCE and CSE tracks), Industrial, and Mechanical Engineering. All programs are ABET accredited. Would you like more information about any specific program?",
                    "department": "MSFEA Advisor"
                }
            else:
                response_data = {
                    "content": "I apologize, but I encountered an error processing your request. Please try again with a different question or type 'reset' to start over.",
                    "department": "MSFEA Advisor"
                }
                
            # Send the response
            response = MessagingResponse()
            response.message(response_data["content"])
            return FastAPIResponse(content=str(response), media_type="application/xml")
            
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {str(e)}", exc_info=True)
        response = MessagingResponse()
        response.message("I apologize, but I encountered an error. Please try again or type 'reset' to start over.")
        return FastAPIResponse(content=str(response), media_type="application/xml")

# Additional routes as needed
