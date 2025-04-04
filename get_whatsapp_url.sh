#!/bin/bash
echo "Fetching WhatsApp webhook URL from container..."
docker-compose logs whatsapp | grep "SUCCESS! WhatsApp webhook URL:" -A 1 | tail -n 1
echo ""
echo "Copy this URL to the Twilio WhatsApp Sandbox settings:"
echo "https://www.twilio.com/console/sms/whatsapp/sandbox"
