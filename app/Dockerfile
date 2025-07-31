# Use an official Python runtime as a parent image
FROM python:3.11.5

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY ../requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the working directory
COPY . ./app/
COPY ../config/ ./config/
COPY ../ansible_playbooks/ ./ansible_playbooks/
COPY ../llm_server/models/ ./llm_server/models/
COPY ../.env ./

# Create necessary directories
RUN mkdir -p /app/llm_server/models

# Expose the port that the FastAPI application will run on
EXPOSE 8000

# Command to run the FastAPI application using the new structure
CMD ["uvicorn", "app.rtr_service.main:app", "--host", "0.0.0.0", "--port", "8000"]