# Google Calendar Integration Setup Guide

This document provides instructions on how to set up the Google Calendar integration for the MSFEA Agent.

## Prerequisites

- A Google account
- Access to [Google Cloud Console](https://console.cloud.google.com/)
- Your application running locally or on a server

## Step 1: Set Up a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Take note of your project ID

## Step 2: Enable the Google Calendar API

1. In the Google Cloud Console sidebar, navigate to "APIs & Services" > "Library"
2. Search for "Google Calendar API"
3. Click on the Google Calendar API card
4. Click "Enable" to enable the API for your project

## Step 3: Configure OAuth Consent Screen

1. In the Google Cloud Console, go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type (or "Internal" if you have a Google Workspace organization)
3. Fill in the required application information:
   - App name: "MSFEA Agent Calendar" (or your preferred name)
   - User support email: Your email address
   - Developer contact information: Your email address
4. Click "Save and Continue"
5. Add the following scopes:
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/calendar.events`
6. Click "Save and Continue"
7. Add test users (your email and any other testers)
8. Click "Save and Continue"
9. Review your app information and click "Back to Dashboard"

## Step 4: Create OAuth Credentials

1. In the Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Set Application type to "Web application"
4. Add a name like "MSFEA Agent Web Client"
5. Add authorized redirect URIs:
   - For local development: `http://localhost:8000/api/gcalendar/callback`
   - For production: `https://your-domain.com/api/gcalendar/callback`
6. Click "Create"
7. A dialog will display your Client ID and Client Secret - save these securely

## Step 5: Configure Your Application

1. Add the following environment variables to your `.env` file:

```
GOOGLE_CLIENT_ID="your-client-id"
GOOGLE_CLIENT_SECRET="your-client-secret"
GOOGLE_REDIRECT_URI="http://localhost:8000/api/gcalendar/callback"
```

For production, use your domain for the redirect URI: `https://your-domain.com/api/gcalendar/callback`

## Step 6: Integration Flow

The Google Calendar integration follows this flow:

1. When a student asks to add their schedule to Google Calendar, the agent will direct them to click the "Add to Google Calendar" button
2. The application will redirect them to the Google authorization page
3. After they grant permission, Google will redirect back to your application with an authorization code
4. Your application exchanges this code for access tokens
5. The application then uses these tokens to add the student's schedule to their Google Calendar
6. The application checks for conflicts with existing events and allows the student to confirm before adding events

## Troubleshooting

- **Error: redirect_uri_mismatch**: Ensure that the redirect URI in your `.env` file exactly matches what you configured in the Google Cloud Console
- **Error: invalid_client**: Double-check that your client ID and client secret are correct
- **Error: access_denied**: The user declined to grant permission to their calendar

## Security Considerations

- Keep your client secret secure and never commit it to public repositories
- Use HTTPS for production redirect URIs
- Consider implementing token refresh mechanisms for long-lived applications
- Monitor your API usage in the Google Cloud Console 