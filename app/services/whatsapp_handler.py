from app.services.advisor import process_query
from app.services.utils import ensure_compatible_state

def handle_whatsapp_message(message: str, session_state) -> str:
    """
    Process WhatsApp messages using the existing advisor logic
    
    Args:
        message (str): The incoming message from WhatsApp
        session_state: The current session state for this user
        
    Returns:
        str: The response to send back to the user
    """
    try:
        # Ensure we have a compatible state object
        state = ensure_compatible_state(session_state)
        
        # Add logging to track the message flow
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Processing WhatsApp message in handler: '{message}'")
        
        # Process with advisor
        try:
            response = process_query(message)
            logger.info(f"Got response from process_query: {response}")
        except Exception as e:
            logger.error(f"Error calling process_query: {str(e)}")
            # Create a valid response object manually
            from app.models.schemas import QueryResponse
            response = QueryResponse(
                content=f"Sorry, I encountered an error processing your question: {str(e)}",
                department="Error Handler"
            )
        
        # Check if response is a dict with content key
        if isinstance(response, dict) and "content" in response:
            logger.info(f"Returning content: {response['content'][:50]}...")
            return response["content"]
        # Handle QueryResponse object directly
        elif hasattr(response, 'content'):
            logger.info(f"Returning content from QueryResponse: {response.content[:50]}...")
            return response.content
        else:
            # Convert to string in case it's not one of the expected types
            response_str = str(response)
            logger.info(f"Returning string response: {response_str[:50]}...")
            return response_str
            
    except Exception as e:
        import traceback
        logger.error(f"Error in WhatsApp handler: {str(e)}")
        logger.error(traceback.format_exc())
        return f"I apologize, but I encountered an error: {str(e)}. Please try again or type 'reset' to start over." 