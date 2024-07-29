# Dockerfile for dummy FastAPI service
FROM python:3.11.5


# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Copy your FastAPI code into the container
COPY  . .


# Expose the port
EXPOSE 8086

# Run the FastAPI application
CMD ["uvicorn", "ansible:mock_epem", "--host", "0.0.0.0", "--port", "8086"]
