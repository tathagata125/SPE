#!/bin/bash

# setup_jenkins_k8s.sh - Script to configure shared Kubernetes configuration for Jenkins
# Created: May 17, 2025

set -e  # Exit on error

echo "Setting up Kubernetes configuration for Jenkins..."

# Define Jenkins user (adjust if your Jenkins runs as a different user)
JENKINS_USER="jenkins"
JENKINS_GROUP="jenkins"
SHARED_CONFIG_DIR="/opt/shared-k8s-config"

# Get the actual user's home directory (not root's home when using sudo)
if [ -n "$SUDO_USER" ]; then
  USER_HOME=$(eval echo ~$SUDO_USER)
else
  USER_HOME=$HOME
fi

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script with sudo."
  exit 1
fi

# Create shared directory
echo "Creating shared Kubernetes config directory at $SHARED_CONFIG_DIR"
mkdir -p $SHARED_CONFIG_DIR

# Get Minikube IP address
MINIKUBE_IP=$(minikube ip)
echo "Detected Minikube IP: $MINIKUBE_IP"

# Create a simplified kubeconfig that uses direct IP communication
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
    user: minikube
  name: minikube
current-context: minikube
kind: Config
preferences: {}
users:
- name: minikube
  user:
    client-certificate: ${SHARED_CONFIG_DIR}/.minikube/profiles/minikube/client.crt
    client-key: ${SHARED_CONFIG_DIR}/.minikube/profiles/minikube/client.key
EOF

# Copy Minikube certificates
if [ -d "$USER_HOME/.minikube" ]; then
  echo "Copying Minikube certificates from $USER_HOME/.minikube"
  cp -r $USER_HOME/.minikube $SHARED_CONFIG_DIR/
else
  echo "ERROR: Minikube directory not found at $USER_HOME/.minikube"
  echo "Please ensure Minikube is properly installed and configured."
  exit 1
fi

# Set proper ownership for Jenkins
echo "Setting permissions for Jenkins user..."
if getent passwd $JENKINS_USER > /dev/null 2>&1; then
  chown -R $JENKINS_USER:$JENKINS_GROUP $SHARED_CONFIG_DIR
  chmod -R 755 $SHARED_CONFIG_DIR
  echo "✅ Permissions set for user $JENKINS_USER"
else
  echo "⚠️ WARNING: User $JENKINS_USER not found."
  echo "Please run the following commands manually after Jenkins is installed:"
  echo "  sudo chown -R jenkins:jenkins $SHARED_CONFIG_DIR"
  echo "  sudo chmod -R 755 $SHARED_CONFIG_DIR"
fi

# Test the configuration
echo "Testing Kubernetes configuration..."
KUBECONFIG=$SHARED_CONFIG_DIR/config kubectl get nodes || {
  echo "❌ Failed to connect to Minikube with the generated configuration"
  echo "This might be because Minikube is not accessible from within Jenkins"
  echo "You might need to start Minikube with more permissive networking:"
  echo "  minikube stop"
  echo "  minikube start --listen-address=0.0.0.0"
  exit 1
}

echo ""
echo "✅ Kubernetes configuration for Jenkins is ready!"
echo "The shared configuration is available at: $SHARED_CONFIG_DIR"
echo ""
echo "If your Jenkins server is running, you can now execute your pipeline with FORCE_K8S_DEPLOY=1."
echo "If you need to check the current configuration, run: KUBECONFIG=$SHARED_CONFIG_DIR/config kubectl get nodes"