from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_400_BAD_REQUEST
import json
import logging
from typing import Optional
from app.services.google_calendar_helper import (
    get_auth_url, 
    get_token_from_code, 
    add_events_to_calendar, 
    check_for_conflicts,
    generate_google_calendar_link,
    generate_all_in_one_calendar_link
)

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/auth")
async def google_auth(request: Request, state: Optional[str] = None):
    """
    Start Google OAuth authentication flow
    """
    try:
        # Generate authentication URL to redirect user
        auth_url = get_auth_url(state)
        if not auth_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate authentication URL"
            )
        
        # Return URL for client to redirect to
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Error in google_auth: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback")
async def google_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    """
    Handle OAuth callback from Google
    """
    try:
        # Check for authentication errors
        if error:
            error_msg = f"Authentication error: {error}"
            logger.error(error_msg)
            return RedirectResponse(url="/?error=auth_failed")
        
        # Check for authorization code
        if not code:
            logger.error("No authorization code provided")
            return RedirectResponse(url="/?error=no_code")
        
        # Exchange code for tokens
        token_data = get_token_from_code(code)
        if not token_data:
            logger.error("Failed to obtain access token")
            return RedirectResponse(url="/?error=token_failed")
        
        # Redirect back to the application
        return RedirectResponse(url="/?auth=success")
    except Exception as e:
        logger.error(f"Error in google_callback: {str(e)}")
        return RedirectResponse(url="/?error=server_error")

@router.post("/add-schedule")
async def add_schedule_to_calendar(request: Request):
    """
    Add class schedule to Google Calendar
    """
    try:
        # Get request body
        data = await request.json()
        
        # Validate required fields
        if not data.get("access_token"):
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={"error": "Access token is required"}
            )
            
        if not data.get("schedule_data"):
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": "Schedule data is required"}
            )
        
        # Check for conflicts
        conflicts = check_for_conflicts(data["access_token"], data["schedule_data"])
        
        # If conflicts are found, return them to the user
        if conflicts.get("has_conflicts", False):
            return JSONResponse(
                content={
                    "status": "conflicts_found",
                    "conflicts": conflicts.get("conflicts", []),
                    "message": "Found calendar conflicts with your existing events"
                }
            )
        
        # No conflicts or explicitly confirmed to add anyway
        if not conflicts.get("error") and (not conflicts.get("has_conflicts") or data.get("force_add", False)):
            result = add_events_to_calendar(data["access_token"], data["schedule_data"])
            
            if result.get("error"):
                return JSONResponse(
                    status_code=HTTP_400_BAD_REQUEST,
                    content={"error": result["error"]}
                )
                
            return JSONResponse(
                content={
                    "status": "success",
                    "message": "Schedule successfully added to your Google Calendar",
                    "results": result.get("results", [])
                }
            )
        else:
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": conflicts.get("error", "Unknown error occurred")}
            )
            
    except Exception as e:
        logger.error(f"Error in add_schedule_to_calendar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-conflicts")
async def check_calendar_conflicts(request: Request):
    """
    Check for conflicts between schedule and existing calendar events
    """
    try:
        # Get request body
        data = await request.json()
        
        # Validate required fields
        if not data.get("access_token"):
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={"error": "Access token is required"}
            )
            
        if not data.get("schedule_data"):
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": "Schedule data is required"}
            )
        
        # Check for conflicts
        conflicts = check_for_conflicts(data["access_token"], data["schedule_data"])
        
        if conflicts.get("error"):
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": conflicts["error"]}
            )
            
        return JSONResponse(content=conflicts)
            
    except Exception as e:
        logger.error(f"Error in check_calendar_conflicts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-links")
async def generate_calendar_links(request: Request):
    """
    Generate Google Calendar links (fallback method)
    """
    try:
        # Get request body
        data = await request.json()
        
        # Validate schedule data
        if not data.get("schedule_data"):
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": "Schedule data is required"}
            )
        
        # Generate links
        links = generate_google_calendar_link(data["schedule_data"])
        
        return JSONResponse(
            content={
                "status": "success",
                "links": links
            }
        )
            
    except Exception as e:
        logger.error(f"Error in generate_calendar_links: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-events")
async def add_events_from_code(request: Request):
    """
    Exchange authorization code for token and add events to calendar
    """
    try:
        # Get request body
        data = await request.json()
        
        # Validate required fields
        if not data.get("code"):
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": "Authorization code is required"}
            )
            
        if not data.get("schedule"):
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": "Schedule data is required"}
            )
        
        # Exchange code for tokens
        token_data = get_token_from_code(data["code"])
        if not token_data or not token_data.get("access_token"):
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={"error": "Failed to obtain access token"}
            )
        
        # Extract access token
        access_token = token_data["access_token"]
        
        # Format schedule data
        schedule_data = {"schedule": data["schedule"]}
        
        # Add events to calendar
        result = add_events_to_calendar(access_token, schedule_data)
        
        if result.get("error"):
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": result["error"]}
            )
        
        # Count the number of events added
        added_count = len(result.get("results", []))
        
        return JSONResponse(
            content={
                "status": "success",
                "message": "Events successfully added to Google Calendar",
                "added_count": added_count
            }
        )
    except Exception as e:
        logger.error(f"Error in add_events_from_code: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"An error occurred: {str(e)}"}
        )

@router.post("/generate-all-link")
async def generate_full_schedule_link(request: Request):
    """
    Generate a single Google Calendar link that adds all courses at once
    """
    try:
        # Get request body
        data = await request.json()
        
        # Validate schedule data
        if not data.get("schedule_data"):
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": "Schedule data is required"}
            )
        
        # Generate the combined link
        link = generate_all_in_one_calendar_link(data["schedule_data"])
        
        if not link:
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": "Failed to generate calendar link"}
            )
        
        return JSONResponse(
            content={
                "status": "success",
                "link": link
            }
        )
            
    except Exception as e:
        logger.error(f"Error in generate_full_schedule_link: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 