# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy all .py files
COPY *.py /app/
# Copy requirements.txt
COPY requirements.txt /app/
# Copy local.settings.json
COPY local.settings.json /app/

# Debugging inside container (curl, ps, etc.)
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get install -y procps

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
CMD ["python", "app.py"]
