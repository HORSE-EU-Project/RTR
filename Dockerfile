# Use an official Python runtime as a parent image
FROM python:3.11.5

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Expose the port that the FastAPI application will run on
EXPOSE 8000

# Command to run the FastAPI application
CMD ["uvicorn", "IBI-RTR_api:rtr_api", "--host", "0.0.0.0", "--port", "8000"]