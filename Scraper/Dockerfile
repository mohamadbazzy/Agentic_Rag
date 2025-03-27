FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy scraper code
COPY scraper.py .

# Create necessary directories
RUN mkdir -p /app/logs /app/output

# Create volume mount points
VOLUME /app/output
VOLUME /app/logs

# Set the entrypoint
ENTRYPOINT ["python", "scraper.py"] 