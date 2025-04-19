import requests
import json
import logging
from datetime import datetime, timedelta
import os
from urllib.parse import urlencode
import base64
import hashlib
import secrets

# Set up logging
logger = logging.getLogger(__name__)

# Google API endpoints and OAuth constants
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_API_URL = "https://www.googleapis.com/calendar/v3"

# Client credentials from environment variables
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/gcalendar/callback")
SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/calendar.events"]

def generate_code_verifier():
    """Generate a random code verifier for PKCE"""
    token = secrets.token_urlsafe(32)
    # Remove any trailing '='
    return token.replace("=", "")

def generate_code_challenge(verifier):
    """Generate a code challenge for PKCE from the verifier"""
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').replace("=", "")

def get_auth_url(state=None):
    """
    Generate an authorization URL for OAuth flow
    
    Args:
        state: Optional state parameter for OAuth
        
    Returns:
        str: Authorization URL
    """
    try:
        # Generate PKCE code verifier and challenge
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        
        # Store the code verifier for later (in production, this should be in a session or database)
        # For simplicity, we'll use an environment variable
        os.environ["GOOGLE_CODE_VERIFIER"] = code_verifier
        
        auth_params = {
            "client_id": CLIENT_ID,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        if state:
            auth_params["state"] = state
            
        auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(auth_params)}"
        return auth_url
    except Exception as e:
        logger.error(f"Error generating Google auth URL: {str(e)}")
        return None

def get_token_from_code(auth_code):
    """
    Exchange authorization code for access token
    
    Args:
        auth_code: Authorization code from OAuth flow
        
    Returns:
        dict: Token data
    """
    try:
        # Get the code verifier we stored earlier
        code_verifier = os.environ.get("GOOGLE_CODE_VERIFIER", "")
        
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier
        }
        
        response = requests.post(GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        return token_data
    except Exception as e:
        logger.error(f"Error getting Google token from code: {str(e)}")
        return None

def refresh_access_token(refresh_token):
    """
    Refresh an expired access token
    
    Args:
        refresh_token: Refresh token from previous authentication
        
    Returns:
        str: New access token
    """
    try:
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        response = requests.post(GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        return token_data.get("access_token")
    except Exception as e:
        logger.error(f"Error refreshing access token: {str(e)}")
        return None

def parse_time(time_str):
    """
    Parse a time string like "9:00 am" or "3:30 pm" to hours and minutes in 24-hour format
    
    Args:
        time_str (str): Time string in "h:mm am/pm" format
        
    Returns:
        tuple: (hour, minute) in 24-hour format
    """
    try:
        # Handle various time formats
        time_str = time_str.lower().strip()
        is_pm = 'pm' in time_str
        time_str = time_str.replace('am', '').replace('pm', '').strip()
        
        if ':' in time_str:
            hour_str, minute_str = time_str.split(':')
            hour = int(hour_str)
            minute = int(minute_str)
        else:
            hour = int(time_str)
            minute = 0
            
        # Convert to
        if is_pm and hour < 12:
            hour += 12
        elif not is_pm and hour == 12:
            hour = 0
            
        return hour, minute
    except Exception as e:
        logger.error(f"Error parsing time: {str(e)}")
        # Default to 9:00 if parsing fails
        return 9, 0

def add_events_to_calendar(access_token, schedule_data):
    """
    Add class schedule to Google Calendar
    
    Args:
        access_token: Access token for Google Calendar API
        schedule_data: Dictionary with schedule information
        
    Returns:
        dict: Results of calendar operations
    """
    try:
        if not access_token or not schedule_data or not schedule_data.get('schedule'):
            return {"error": "Invalid access token or schedule data"}
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Create event for each course in the schedule
        results = []
        
        for course in schedule_data['schedule']:
            # For each meeting time, create a separate event
            for meeting in course.get('meetings', []):
                # Parse the days to create recurring events
                weekdays = meeting.get('days', [])
                
                # Get start and end times
                start_time = meeting.get('start_time', '9:00 am')
                end_time = meeting.get('end_time', '10:00 am')
                
                # Parse times
                start_hour, start_minute = parse_time(start_time)
                end_hour, end_minute = parse_time(end_time)
                
                # For each day in the course schedule
                for day in weekdays:
                    # Calculate the next occurrence of this day
                    today = datetime.now()
                    day_mapping = {
                        "MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2, 
                        "THURSDAY": 3, "FRIDAY": 4, "SATURDAY": 5, "SUNDAY": 6
                    }
                    target_day = day_mapping.get(day.upper(), 0)
                    current_day = today.weekday()
                    days_ahead = (target_day - current_day) % 7
                    
                    if days_ahead == 0:  # If today is the target day, start next week
                        days_ahead = 7
                        
                    next_day = today + timedelta(days=days_ahead)
                    
                    # Create start and end datetime objects
                    start_datetime = next_day.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                    end_datetime = next_day.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
                    
                    # Format datetimes for Google Calendar API
                    start_str = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")
                    end_str = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")
                    
                    # Create the event data
                    event_data = {
                        "summary": f"{course['course_code']} - {course.get('title', 'Class')}",
                        "location": meeting.get('location', 'AUB Campus'),
                        "description": f"Course: {course['course_code']}\nSection: {course.get('section', '')}\nInstructor: {course.get('instructor', 'TBA')}",
                        "start": {
                            "dateTime": start_str,
                            "timeZone": "Asia/Beirut"  # Use Beirut time zone for AUB
                        },
                        "end": {
                            "dateTime": end_str,
                            "timeZone": "Asia/Beirut"
                        },
                        "recurrence": [
                            # Repeat weekly for 15 weeks (typical semester length)
                            "RRULE:FREQ=WEEKLY;COUNT=15"
                        ],
                        "reminders": {
                            "useDefault": False,
                            "overrides": [
                                {"method": "popup", "minutes": 10}
                            ]
                        }
                    }
                    
                    # Create the event in Google Calendar
                    event_url = f"{GOOGLE_CALENDAR_API_URL}/calendars/primary/events"
                    response = requests.post(event_url, headers=headers, json=event_data)
                    response.raise_for_status()
                    results.append(response.json())
        
        return {"success": True, "results": results}
    except Exception as e:
        logger.error(f"Error adding events to Google Calendar: {str(e)}")
        return {"error": str(e)}

def check_for_conflicts(access_token, schedule_data):
    """
    Check for conflicts between the schedule and existing calendar events
    
    Args:
        access_token: Access token for Google Calendar API
        schedule_data: Dictionary with schedule information
        
    Returns:
        dict: Conflict information
    """
    try:
        if not access_token or not schedule_data or not schedule_data.get('schedule'):
            return {"error": "Invalid access token or schedule data"}
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Set the date range for checking conflicts (next 30 days)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        
        # Format dates for Google Calendar API
        time_min = start_date.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        time_max = end_date.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        
        # Get existing calendar events
        calendar_url = f"{GOOGLE_CALENDAR_API_URL}/calendars/primary/events?timeMin={time_min}&timeMax={time_max}&singleEvents=true"
        response = requests.get(calendar_url, headers=headers)
        response.raise_for_status()
        
        existing_events = response.json().get('items', [])
        
        # Check for conflicts
        conflicts = []
        
        for course in schedule_data['schedule']:
            for meeting in course.get('meetings', []):
                # For each day in the course schedule
                for day in meeting.get('days', []):
                    # Parse meeting time
                    start_time = meeting.get('start_time', '9:00 am')
                    end_time = meeting.get('end_time', '10:00 am')
                    
                    start_hour, start_minute = parse_time(start_time)
                    end_hour, end_minute = parse_time(end_time)
                    
                    # Check against existing events
                    day_mapping = {
                        "MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2, 
                        "THURSDAY": 3, "FRIDAY": 4, "SATURDAY": 5, "SUNDAY": 6
                    }
                    day_index = day_mapping.get(day.upper(), 0)
                    
                    for event in existing_events:
                        # Skip events without start or end
                        if 'start' not in event or 'end' not in event:
                            continue
                            
                        # Get event start and end times
                        event_start = None
                        event_end = None
                        
                        # Parse datetime depending on the format
                        if 'dateTime' in event['start']:
                            event_start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                            event_end = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
                        elif 'date' in event['start']:
                            # All-day event
                            continue
                        
                        # If the event is on the same day of the week
                        if event_start and event_start.weekday() == day_index:
                            # Create a comparable datetime for the course meeting
                            meeting_date = event_start.date()
                            meeting_start = datetime.combine(meeting_date, datetime.min.time().replace(hour=start_hour, minute=start_minute))
                            meeting_end = datetime.combine(meeting_date, datetime.min.time().replace(hour=end_hour, minute=end_minute))
                            
                            # Check for overlap
                            if (meeting_start < event_end and meeting_end > event_start):
                                conflicts.append({
                                    "course": f"{course['course_code']} - {course.get('title', 'Class')}",
                                    "meeting_day": day,
                                    "meeting_time": f"{start_time} - {end_time}",
                                    "conflicting_event": event.get('summary', 'Unknown Event'),
                                    "event_time": f"{event_start.strftime('%I:%M %p')} - {event_end.strftime('%I:%M %p')}"
                                })
        
        if conflicts:
            return {
                "has_conflicts": True,
                "conflicts": conflicts
            }
        else:
            return {
                "has_conflicts": False
            }
    except Exception as e:
        logger.error(f"Error checking for calendar conflicts: {str(e)}")
        return {"error": str(e)}

def generate_google_calendar_link(schedule_data):
    """
    Generate a Google Calendar link for the schedule (fallback method)
    
    Args:
        schedule_data: Dictionary with schedule information
        
    Returns:
        list: List of Google Calendar links for each class session
    """
    if not schedule_data or not schedule_data.get('schedule'):
        return []
    
    links = []
    
    for course in schedule_data['schedule']:
        # For each meeting time, create a separate event link
        for meeting in course.get('meetings', []):
            # Get start and end times
            start_time = meeting.get('start_time', '9:00 am')
            end_time = meeting.get('end_time', '10:00 am')
            
            # Parse times
            start_hour, start_minute = parse_time(start_time)
            end_hour, end_minute = parse_time(end_time)
            
            # For each day in the course schedule
            for day in meeting.get('days', []):
                # Calculate the next occurrence of this day
                today = datetime.now()
                day_mapping = {
                    "MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2, 
                    "THURSDAY": 3, "FRIDAY": 4, "SATURDAY": 5, "SUNDAY": 6
                }
                target_day = day_mapping.get(day.upper(), 0)
                current_day = today.weekday()
                days_ahead = (target_day - current_day) % 7
                
                if days_ahead == 0:  # If today is the target day, start next week
                    days_ahead = 7
                    
                next_day = today + timedelta(days=days_ahead)
                
                # Create start and end datetime objects
                start_datetime = next_day.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                end_datetime = next_day.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
                
                # Format dates for Google Calendar URL
                start_formatted = start_datetime.strftime("%Y%m%dT%H%M%S")
                end_formatted = end_datetime.strftime("%Y%m%dT%H%M%S")
                
                # Create event parameters
                event_params = {
                    "action": "TEMPLATE",
                    "text": f"{course['course_code']} - {course.get('title', 'Class')}",
                    "details": f"Course: {course['course_code']}\nSection: {course.get('section', '')}\nInstructor: {course.get('instructor', 'TBA')}",
                    "location": meeting.get('location', 'AUB Campus'),
                    "dates": f"{start_formatted}/{end_formatted}",
                    "recur": "RRULE:FREQ=WEEKLY;COUNT=15"  # Repeat weekly for 15 weeks (typical semester length)
                }
                
                # Generate URL
                calendar_url = f"https://www.google.com/calendar/render?{urlencode(event_params)}"
                links.append({
                    "day": day,
                    "time": f"{start_time} - {end_time}",
                    "course": course['course_code'],
                    "url": calendar_url
                })
    
    return links 