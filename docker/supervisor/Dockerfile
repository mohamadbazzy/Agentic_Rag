FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the necessary files for this image
COPY app/services/supervisor.py app/services/supervisor.py
COPY app/services/departments/msfea_advisor.py app/services/departments/msfea_advisor.py
COPY app/services/schedule_helper.py app/services/schedule_helper.py
# COPY app/services/petition_system.py app/services/petition_system.py  # Comment this line until the file exists
COPY app/services/agent_index_wrapper.py app/services/agent_index_wrapper.py
COPY app/services/namespace_config.py app/services/namespace_config.py
COPY app/core/ app/core/
COPY app/models/ app/models/
COPY app/db/ app/db/

# Create a non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Command to run the supervisor service
CMD ["python", "-m", "app.services.supervisor"] 