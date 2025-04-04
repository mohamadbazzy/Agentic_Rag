FROM python:3.9-slim

WORKDIR /app

# Install dependencies and procps (for ps command)
COPY requirements.txt .
RUN apt-get update && apt-get install -y curl unzip procps
RUN pip install --no-cache-dir -r requirements.txt

# Install ngrok
RUN curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list && \
    apt-get update && apt-get install -y ngrok

# Copy backend code
COPY app/ app/
COPY scripts/ scripts/

# Copy startup script
COPY docker/whatsapp/start.sh .
RUN chmod +x start.sh

# Create a non-root user
RUN adduser --disabled-password --gecos "" appuser

# Now switch to non-root user
USER appuser

# Expose the port
EXPOSE 8000

# Command to run the whatsapp service
CMD ["./start.sh"]