# Google Calendar Integration Testing Guide

This document provides instructions on how to test the Google Calendar integration for the MSFEA Agent.

## Prerequisites

- Completed setup steps from [Google Calendar Setup Guide](google_calendar_setup.md)
- Application running locally or on a server
- A Google account with calendar access

## Test 1: Basic Authentication Flow

1. Start your application server:
   ```
   uvicorn app.main:app --reload
   ```

2. Open the application in your browser

3. Chat with the agent and ask it to create a class schedule:
   ```
   "Can you create a schedule for me with EECE 230, MATH 201, and CMPS 200?"
   ```

4. When the agent generates a schedule, you should see a "Add to Google Calendar" button below the response

5. Click the button to test the authentication flow:
   - You should be redirected to Google's consent screen
   - Grant permission to access your calendar
   - After authorization, you should be redirected back to your application

6. Expected result: Successful authentication with redirect back to your application

## Test 2: Adding Events to Calendar

1. Follow Test 1 steps to get a schedule and authenticate

2. After successful authentication, the application should:
   - Show a loading indicator
   - Create recurring events in your Google Calendar for each class
   - Display a success message when complete

3. Check your Google Calendar to verify:
   - Events were created with the correct course information
   - Events are scheduled at the correct times
   - Events repeat weekly for the semester

4. Expected result: All class events properly added to your Google Calendar

## Test 3: Conflict Detection

1. Create an event in your Google Calendar that overlaps with your class schedule
   - For example, add an event from 9:00 AM to 10:30 AM on Monday

2. Follow Test 1 steps to generate a schedule that would conflict with this event
   - Make sure one of the courses meets during your manually created event time

3. Click "Add to Google Calendar" and authenticate

4. Expected result: The system should detect the conflict and:
   - Display a message showing the conflicting events
   - Ask if you want to proceed anyway
   - Allow you to choose whether to add the events despite conflicts

## Test 4: OAuth Error Handling

1. Intentionally create an error scenario:
   - Temporarily change the `GOOGLE_REDIRECT_URI` in your .env file to an incorrect value
   - Restart your application

2. Follow Test 1 steps to generate a schedule and click "Add to Google Calendar"

3. Expected result: The system should handle the authentication error gracefully and display an appropriate error message

4. Reset your `GOOGLE_REDIRECT_URI` to the correct value when done

## Test 5: Fallback URL Generation

1. In your application, there should be a fallback mechanism for users who prefer not to grant calendar access

2. Generate a schedule and look for an option to "Get Calendar Links" instead of direct integration

3. Click this option to test the fallback mechanism

4. Expected result: 
   - The system generates direct Google Calendar URLs for each class
   - Clicking these links opens Google Calendar with pre-filled event details
   - You can add events individually without granting API access

## Troubleshooting Common Issues

- **Authentication Errors**: Check that your Google Cloud Console credentials match your .env file
- **Calendar Events Not Appearing**: Verify the timezone settings in your Google Calendar
- **Recurring Events Issues**: Check that the recurrence rule is properly formatted
- **Wrong Class Times**: Verify that time parsing is handling AM/PM correctly

## Logging and Debugging

For more detailed debugging, enable debug logging in your .env file:
```
DEBUG=True
LOG_LEVEL=DEBUG
```

This will provide more detailed logs about the Google Calendar API requests and responses. 