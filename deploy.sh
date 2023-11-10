#!/bin/bash

# Stop and remove existing Docker containers
sudo docker-compose down

# Remove the existing Docker image
sudo docker image rm stock-strategies_app:latest

# Pull the latest changes from the Git repository
git pull

# Build and start Docker containers
sudo docker-compose up -d --scale app=1 --build

# Display a message indicating successful execution
echo "Deployment completed successfully."

