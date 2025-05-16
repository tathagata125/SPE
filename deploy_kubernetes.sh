#!/bin/bash

# deploy_kubernetes.sh - Script to deploy Weather_ops to Kubernetes
# Created: May 15, 2025

set -e  # Exit on error

echo "Deploying Weather_ops to Kubernetes..."

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if minikube is installed (for local development)
if command -v minikube &> /dev/null; then
    MINIKUBE_STATUS=$(minikube status --format={{.Host}} 2>/dev/null || echo "Not Running")
    if [ "$MINIKUBE_STATUS" != "Running" ]; then
        echo "Starting Minikube..."
        minikube start
    else
        echo "Minikube is already running."
    fi
    
    # Enable ingress addon if not already enabled
    if ! minikube addons list | grep -q "ingress: enabled"; then
        echo "Enabling Ingress addon in Minikube..."
        minikube addons enable ingress
    fi
fi

# Create namespace if it doesn't exist
echo "Creating namespace..."
kubectl apply -f kubernetes/namespace.yaml

# Deploy backend
echo "Deploying backend..."
kubectl apply -f kubernetes/backend.yaml

# Deploy frontend
echo "Deploying frontend..."
kubectl apply -f kubernetes/frontend.yaml

# Deploy ingress
echo "Deploying ingress..."
kubectl apply -f kubernetes/ingress.yaml

echo "Waiting for pods to be ready..."
kubectl wait --namespace weather-ops --for=condition=ready pod --selector=app=weather-ops --timeout=120s

echo "Deployment completed successfully!"

# If using Minikube, show access URLs
if command -v minikube &> /dev/null; then
    MINIKUBE_IP=$(minikube ip)
    echo ""
    echo "To access the application on Minikube:"
    echo "1. Add this entry to your /etc/hosts file:"
    echo "   $MINIKUBE_IP weather-ops.local"
    echo ""
    echo "2. Then access the application at:"
    echo "   Frontend: http://weather-ops.local"
    echo "   Backend API: http://weather-ops.local/api"
    echo ""
    echo "3. Alternatively, use port-forwarding to access the services directly:"
    echo "   kubectl port-forward -n weather-ops svc/frontend 8502:8501"
    echo "   kubectl port-forward -n weather-ops svc/backend 5001:5000"
fi