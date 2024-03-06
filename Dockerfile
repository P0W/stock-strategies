## Stage 1: Build the frontend - Uncomment for Higher CPU VMs
## FROM node:21-slim AS frontEndBuild
## WORKDIR /app
#COPY frontend/package*.json .
## RUN yarn ci
## RUN mkdir node_modules
## COPY frontend/ /app
## RUN yarn install
## RUN yarn run build

## Stage 2: Build the backend
FROM python:3.9-slim
WORKDIR /app
# Copy all .py files
COPY backend/*.py /app/backend/
# Copy requirements.txt
COPY backend/requirements.txt /app/backend/

# Install any needed packages specified in requirements.txt
RUN pip install -r backend/requirements.txt

## copy from frontend/build to /app/frontend/build
COPY frontend/build /app/frontend/build
## COPY --from=frontEndBuild /app/build /app/frontend/build -- Uncomment for Higher CPU VMs
# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
CMD ["python", "backend/app.py"]
