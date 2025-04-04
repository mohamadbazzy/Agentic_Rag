# Kubernetes Deployment for Agentic RAG

This directory contains the Kubernetes configuration files for deploying the Agentic RAG application.

## Prerequisites

- kubectl installed and configured
- Docker installed
- Access to a Kubernetes cluster or Minikube for local development
- A Docker registry account (Docker Hub or private registry)

## Setup Steps

1. **Update Docker Registry Information**

   Edit the `build-and-push.sh` script and update the `DOCKER_REGISTRY` variable with your Docker registry name.

2. **Build and Push Docker Images**

   ```bash
   ./k8s/build-and-push.sh
   ```

3. **Update Kubernetes Configuration Files**

   Replace `${YOUR_DOCKER_REGISTRY}` in all Kubernetes YAML files with your actual Docker registry name.

   ```bash
   find k8s -name "*.yaml" -exec sed -i '' 's/${YOUR_DOCKER_REGISTRY}/your-registry/g' {} \;
   ```

4. **Deploy to Kubernetes**

   ```bash
   ./k8s/deploy.sh
   ```

5. **Verify Deployment**

   ```bash
   kubectl get pods -n agentic-rag
   ```

## Accessing the Application

- If using Minikube, you can access the application using:

  ```bash
  minikube service frontend-service -n agentic-rag
  ```

- If deployed to a production cluster with the Ingress controller, access the application using the domain configured in the Ingress resource.

## Architecture

The Kubernetes deployment consists of the following components:

- **Backend**: FastAPI application handling the core RAG functionality
- **Frontend**: Web UI for user interaction
- **Supervisor**: Agent for managing and routing user queries
- **Departments**: Department-specific agents for specialized responses
- **WhatsApp Integration**: Service for WhatsApp message handling
- **Scraper**: Job for scraping and updating knowledge base

## Configuration

Environment variables are managed through Kubernetes ConfigMaps and Secrets:

- **ConfigMap**: Non-sensitive configuration
- **Secrets**: Sensitive data like API keys

## Data Persistence

Persistent data is stored using Persistent Volume Claims:

- **data-pvc**: For application data
- **scraper-output-pvc**: For scraped content

## Troubleshooting

- To check logs for a specific pod:
  ```bash
  kubectl logs -n agentic-rag pod-name
  ```

- To restart a deployment:
  ```bash
  kubectl rollout restart deployment -n agentic-rag deployment-name
  ```