#!/bin/bash

# Create namespace if it doesn't exist
kubectl create namespace agentic-rag --dry-run=client -o yaml | kubectl apply -f -

# Apply ConfigMap and Secret
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Apply persistent volumes
kubectl apply -f k8s/persistent-volumes.yaml

# Apply backend deployment and service
kubectl apply -f k8s/backend-deployment.yaml

# Apply microservices deployments
kubectl apply -f k8s/microservices-deployment.yaml

# Apply frontend deployment and service
kubectl apply -f k8s/frontend-deployment.yaml

# Apply ingress for external access
kubectl apply -f k8s/ingress.yaml

# Create scraper job
kubectl apply -f k8s/scraper-job.yaml

echo "Deployment completed!"
echo "You can check the status of the pods with: kubectl get pods -n agentic-rag" 