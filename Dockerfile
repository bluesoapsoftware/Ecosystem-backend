# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
# We copy only the requirements file first to leverage Docker's cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire src directory into the container at /app/src
COPY src/ src/
COPY .env .env
COPY aws_config.json aws_config.json
COPY config.py config.py # Copy root config files that might be referenced

# Expose the port the app runs on (our canonical FastAPI port)
EXPOSE 8080

# Run the uvicorn server
# The server.py file initializes the FastAPI app as 'app'
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8080"]
