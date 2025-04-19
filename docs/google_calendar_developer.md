# Google Calendar Integration Developer Guide

This document provides technical details about the Google Calendar integration for developers who need to understand, maintain, or extend this functionality.

## Architecture Overview

The Google Calendar integration consists of the following components:

1. **API Endpoints** (`app/api/endpoints/gcalendar.py`): FastAPI routes that handle OAuth flow and calendar operations

2. **Helper Service** (`app/services/google_calendar_helper.py`): Core functionality for calendar operations

3. **Frontend Integration** (`frontend/script.js`): Client-side code for the user interface and OAuth flow

4. **Configuration** (`.env`): Environment variables for API credentials

## API Endpoints

The following endpoints handle the Google Calendar integration:

- `GET /api/gcalendar/auth`: Initiates OAuth flow and returns an authorization URL
- `GET /api/gcalendar/callback`: Handles OAuth callback and exchanges code for tokens
- `POST /api/gcalendar/add-schedule`: Adds schedule to Google Calendar
- `POST /api/gcalendar/check-conflicts`: Checks for conflicts with existing calendar events
- `POST /api/gcalendar/generate-links`: Generates direct Google Calendar links (fallback method)

## Authentication Flow

The Google Calendar integration uses OAuth 2.0 with the Authorization Code flow and PKCE (Proof Key for Code Exchange) for enhanced security:

1. Generate a code verifier (random string) and derived code challenge
2. Redirect user to Google's authorization page with code challenge
3. User grants permission, Google redirects back with authorization code
4. Exchange authorization code + original code verifier for access token
5. Use access token for API calls to Google Calendar

## Helper Service Functions

Key functions in `app/services/google_calendar_helper.py`:

- `get_auth_url()`: Generates OAuth authorization URL with PKCE
- `get_token_from_code()`: Exchanges authorization code for tokens
- `refresh_access_token()`: Refreshes an expired access token
- `add_events_to_calendar()`: Adds class schedule to Google Calendar
- `check_for_conflicts()`: Checks for conflicts with existing events
- `generate_google_calendar_link()`: Generates direct Google Calendar URLs

## Data Structures

### Schedule Format

The application expects schedule data in this format:

```json
{
  "is_schedule": true,
  "schedule": [
    {
      "course_code": "EECE 230",
      "section": "1",
      "title": "Introduction to Computation",
      "meetings": [
        {
          "days": ["MONDAY", "WEDNESDAY"],
          "start_time": "9:00 am",
          "end_time": "10:15 am",
          "location": "IOEC 234"
        }
      ],
      "instructor": "Dr. Smith"
    }
  ]
}
```

### Google Calendar Event Format

Events are created with the following structure:

```json
{
  "summary": "EECE 230 - Introduction to Computation",
  "location": "IOEC 234",
  "description": "Course: EECE 230\nSection: 1\nInstructor: Dr. Smith",
  "start": {
    "dateTime": "2023-09-05T09:00:00",
    "timeZone": "Asia/Beirut"
  },
  "end": {
    "dateTime": "2023-09-05T10:15:00",
    "timeZone": "Asia/Beirut"
  },
  "recurrence": [
    "RRULE:FREQ=WEEKLY;COUNT=15"
  ],
  "reminders": {
    "useDefault": false,
    "overrides": [
      {"method": "popup", "minutes": 10}
    ]
  }
}
```

## Implementation Details

### PKCE Implementation

The system implements PKCE for enhanced security:

```python
def generate_code_verifier():
    token = secrets.token_urlsafe(32)
    return token.replace("=", "")

def generate_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').replace("=", "")
```

### Time Parsing

The system parses various time formats:

```python
def parse_time(time_str):
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
        
    # Convert to 24-hour format
    if is_pm and hour < 12:
        hour += 12
    elif not is_pm and hour == 12:
        hour = 0
        
    return hour, minute
```

### Conflict Detection

The system detects conflicts by:

1. Retrieving events from the user's calendar for a 30-day period
2. For each class session, checking if it overlaps with any existing events
3. Reporting conflicts to allow the user to decide whether to proceed

## Frontend Integration

The frontend handles:

1. Displaying the "Add to Google Calendar" button for schedules
2. Managing the OAuth flow in the browser
3. Showing loading states and results
4. Providing a fallback mechanism using direct Google Calendar links

## Extensions and Customizations

### Adding New Features

To add new Google Calendar features:

1. Add necessary helper functions to `google_calendar_helper.py`
2. Create new API endpoints in `gcalendar.py`
3. Update frontend code in `script.js` to use the new endpoints

### Modifying Event Properties

To customize event creation:

1. Modify the `event_data` object in the `add_events_to_calendar()` function
2. Update the `event_params` in the `generate_google_calendar_link()` function

### Supporting Additional OAuth Scopes

To request additional Google API permissions:

1. Update the `SCOPES` list in `google_calendar_helper.py`
2. Configure these scopes in the Google Cloud Console
3. Modify code to use the new permissions

## Common Challenges

- **Token Storage**: Currently, tokens are not persistently stored. For production, implement secure token storage.
- **Error Handling**: Complex OAuth errors should be mapped to user-friendly messages.
- **Timezone Handling**: Be mindful of timezone differences between user, server, and calendar settings.
- **Rate Limiting**: Google Calendar API has usage limits that should be monitored.

## Google Calendar API Resources

- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Google API Explorer](https://developers.google.com/apis-explorer/#p/calendar/v3/) 