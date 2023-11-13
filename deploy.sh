#!/bin/bash

# Stop and remove existing Docker containers
echo "Stopping and removing existing Docker containers..."
sudo docker-compose down

# Remove the existing Docker image
echo "Removing existing Docker image..."
sudo docker image rm stock-strategies_app:latest

# Pull the latest changes from the Git repository
echo "Pulling the latest changes from the Git repository..."
git pull orgin main

# Build frontend assets
echo "Building frontend assets..."
cd frontend
yarn install
yarn build
cd ..

# Build and start Docker containers
echo "Building and starting Docker containers..."
sudo docker-compose up -d --scale app=1 --build

# Display a message indicating successful execution
echo "Deployment completed successfully."

