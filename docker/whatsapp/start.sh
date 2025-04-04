#!/bin/bash
set -e

echo "Starting WhatsApp webhook service..."

# Check if NGROK_AUTH_TOKEN exists
if [ -z "$NGROK_AUTH_TOKEN" ]; then
  echo "ERROR: NGROK_AUTH_TOKEN is not set!"
  exit 1
fi

echo "Starting ngrok with auth token..."
ngrok http --authtoken $NGROK_AUTH_TOKEN 8000 &

echo "Waiting for ngrok to start..."
sleep 10

# Get the URL
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'https://[^"]*' | head -n 1)

if [ -z "$PUBLIC_URL" ]; then
  echo "ERROR: Failed to get ngrok URL!"
else
  echo "SUCCESS! WhatsApp webhook URL:"
  echo "$PUBLIC_URL/api/whatsapp/webhook"
  echo ""
  echo "You must manually update this URL in the Twilio console:"
  echo "1. Go to https://www.twilio.com/console/sms/whatsapp/sandbox"
  echo "2. Set 'WHEN A MESSAGE COMES IN' to the URL above"
fi

echo "Starting FastAPI application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
