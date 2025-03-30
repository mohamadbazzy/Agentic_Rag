FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the necessary department files
COPY app/services/departments/ app/services/departments/
# Remove MSFEA advisor as it's in the supervisor image
RUN rm app/services/departments/msfea_advisor.py
# Copy tracks
COPY app/services/tracks/ app/services/tracks/
COPY app/services/agent_index_wrapper.py app/services/agent_index_wrapper.py
COPY app/services/namespace_config.py app/services/namespace_config.py
COPY app/core/ app/core/
COPY app/models/ app/models/
COPY app/db/ app/db/

# Create a non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Command to run the department services
CMD ["python", "-m", "app.services.departments"] 