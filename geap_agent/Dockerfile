# Google Enterprise Agent Platform (GEAP) Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY geap_agent/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY pepsico_sc_agent/ pepsico_sc_agent/
COPY geap_agent/ geap_agent/

# Set Python path
ENV PYTHONPATH=/app
ENV PORT=8080

EXPOSE 8080

# Run FastAPI service
CMD ["python", "-m", "uvicorn", "geap_agent.agent_service:app", "--host", "0.0.0.0", "--port", "8080"]
