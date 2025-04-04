#!/bin/bash

# Set your Docker registry (Docker Hub username or private registry)
DOCKER_REGISTRY="miriamcs"

# Build backend image
echo "Building backend image..."
docker build -t ${DOCKER_REGISTRY}/agentic-rag-backend:latest -f docker/backend/Dockerfile .
# Load image into Minikube
minikube image load ${DOCKER_REGISTRY}/agentic-rag-backend:latest

# Build frontend image
echo "Building frontend image..."
docker build -t ${DOCKER_REGISTRY}/agentic-rag-frontend:latest -f docker/frontend/Dockerfile .
# Load image into Minikube
minikube image load ${DOCKER_REGISTRY}/agentic-rag-frontend:latest

# Build supervisor image
echo "Building supervisor image..."
docker build -t ${DOCKER_REGISTRY}/agentic-rag-supervisor:latest -f docker/supervisor/Dockerfile .
# Load image into Minikube
minikube image load ${DOCKER_REGISTRY}/agentic-rag-supervisor:latest

# Build departments image
echo "Building departments image..."
docker build -t ${DOCKER_REGISTRY}/agentic-rag-departments:latest -f docker/departments/Dockerfile .
# Load image into Minikube
minikube image load ${DOCKER_REGISTRY}/agentic-rag-departments:latest

# Build whatsapp image
echo "Building whatsapp image..."
docker build -t ${DOCKER_REGISTRY}/agentic-rag-whatsapp:latest -f docker/whatsapp/Dockerfile .
# Load image into Minikube
minikube image load ${DOCKER_REGISTRY}/agentic-rag-whatsapp:latest

# Build scraper image
echo "Building scraper image..."
docker build -t ${DOCKER_REGISTRY}/agentic-rag-scraper:latest -f docker/scraper/Dockerfile .
# Load image into Minikube
minikube image load ${DOCKER_REGISTRY}/agentic-rag-scraper:latest

echo "All images built and loaded into Minikube successfully!"
echo "You can now run k8s/deploy.sh to deploy your application" 