#!/bin/bash

# setup_jenkins_k8s_simple.sh - A simpler script to configure Kubernetes for Jenkins
# Created: May 17, 2025

set -e  # Exit on error

echo "Setting up simplified Kubernetes configuration for Jenkins..."

# Define paths
JENKINS_USER="jenkins"
JENKINS_GROUP="jenkins" 
SHARED_CONFIG_DIR="/opt/shared-k8s-config"
USER_HOME="/home/girish"  # Hardcoded for simplicity

# First, get the Minikube IP as the regular user
MINIKUBE_IP=$(su - girish -c "minikube ip")
echo "Detected Minikube IP: $MINIKUBE_IP"

# Create shared directory
echo "Creating shared Kubernetes config directory at $SHARED_CONFIG_DIR"
sudo mkdir -p $SHARED_CONFIG_DIR

# Create a simplified kubeconfig
echo "Creating simplified kubeconfig for Jenkins..."
cat > $SHARED_CONFIG_DIR/config << EOF
apiVersion: v1
clusters:
- cluster:
    insecure-skip-tls-verify: true
    server: https://${MINIKUBE_IP}:8443
  name: minikube
contexts:
- context:
    cluster: minikube
    namespace: default
    user: minikube
  name: minikube
current-context: minikube
kind: Config
preferences: {}
users:
- name: minikube
  user:
    client-certificate: ${SHARED_CONFIG_DIR}/client.crt
    client-key: ${SHARED_CONFIG_DIR}/client.key
EOF

# Copy the necessary certificate files directly
echo "Copying Minikube certificates..."
cp $USER_HOME/.minikube/profiles/minikube/client.crt $SHARED_CONFIG_DIR/
cp $USER_HOME/.minikube/profiles/minikube/client.key $SHARED_CONFIG_DIR/
cp $USER_HOME/.minikube/ca.crt $SHARED_CONFIG_DIR/

# Set proper ownership
echo "Setting permissions for Jenkins user..."
sudo chown -R $JENKINS_USER:$JENKINS_GROUP $SHARED_CONFIG_DIR
sudo chmod -R 755 $SHARED_CONFIG_DIR
sudo chmod 600 $SHARED_CONFIG_DIR/client.key

echo ""
echo "✅ Simple Kubernetes configuration for Jenkins is ready!"
echo "The shared configuration is available at: $SHARED_CONFIG_DIR"
echo ""
echo "Now you can run your Jenkins pipeline with FORCE_K8S_DEPLOY=1"