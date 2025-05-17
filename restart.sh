#!/bin/bash
# restart.sh - Script to restart Weather_Ops project from scratch
# Created: May 17, 2025

# Stop on errors
set -e

echo "=== Weather_Ops Project Restart Script ==="

# Clean up existing Kubernetes resources
echo "Step 1: Cleaning up existing Kubernetes resources..."
kubectl delete namespace weather-ops || echo "Namespace not found or already deleted"

# Restart Minikube with proper network settings
echo "Step 2: Restarting Minikube with proper network configuration..."
minikube stop
minikube start --listen-address=0.0.0.0

# Set up Kubernetes configuration for Jenkins
echo "Step 3: Setting up Kubernetes configuration for Jenkins..."
sudo ./setup_jenkins_k8s_simple.sh

# Deployment options
echo ""
echo "=== Deployment Options ==="
echo "Your environment is now ready. You can deploy in one of these ways:"
echo ""
echo "Option 1: Deploy via Jenkins pipeline"
echo "  1. Go to your Jenkins dashboard"
echo "  2. Open the Weather_Ops pipeline"
echo "  3. Check the 'Force actual deployment to Kubernetes' option"
echo "  4. Click 'Build Now'"
echo ""
echo "Option 2: Deploy manually"
echo "  Run: ./deploy_kubernetes.sh"
echo ""

# Ask if user wants to deploy manually now
read -p "Would you like to deploy manually now? (y/n): " deploy_choice
if [ "$deploy_choice" = "y" ] || [ "$deploy_choice" = "Y" ]; then
    echo "Deploying Weather_Ops to Kubernetes..."
    ./deploy_kubernetes.sh
    
    echo ""
    echo "Deployment complete!"
    echo "To access the frontend: http://weather-ops.local (with proper hosts file entry)"
    echo "Or use port-forwarding: kubectl port-forward -n weather-ops svc/frontend 8502:8501"
fi

echo ""
echo "Restart process complete!"