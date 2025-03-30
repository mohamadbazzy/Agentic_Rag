FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY app/ app/

# Create a non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Expose the port
EXPOSE 8000

# Command to run the backend service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 