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

# Copy Kubernetes config and check if it exists
if [ -f "$USER_HOME/.kube/config" ]; then
  echo "Copying Kubernetes config from $USER_HOME/.kube/config"
  cp $USER_HOME/.kube/config $SHARED_CONFIG_DIR/
else
  echo "ERROR: Kubernetes config not found at $USER_HOME/.kube/config"
  echo "Please ensure Minikube is properly configured."
  exit 1
fi

# Copy Minikube certificates and check if they exist
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

echo ""
echo "✅ Kubernetes configuration for Jenkins is ready!"
echo "The shared configuration is available at: $SHARED_CONFIG_DIR"
echo ""
echo "If your Jenkins server is running, you can now execute your pipeline."
echo "If you need to check the current configuration, run: ls -la $SHARED_CONFIG_DIR"