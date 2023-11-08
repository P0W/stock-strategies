## Stage 1: Build the frontend
FROM node:21-slim AS frontEndBuild
WORKDIR /app
COPY frontend/package*.json .
RUN npm ci
## copy from frontend/*.* to /app
COPY frontend/ /app
RUN npm install
RUN npm run build

## Stage 2: Build the backend
FROM python:3.9-slim
WORKDIR /app
# Copy all .py files
COPY backend/*.py /app/
# Copy requirements.txt
COPY backend/requirements.txt /app/
# Copy local.settings.json
COPY local.settings.json /app/

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

## copy from frontend/build to /app/frontend/build
COPY --from=frontEndBuild /app/build /app/frontend/build
# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
CMD ["python", "app.py"]
