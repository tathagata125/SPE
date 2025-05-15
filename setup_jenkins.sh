#!/bin/bash

# setup_jenkins.sh - Script to set up Jenkins for Weather_ops project
# Created: May 15, 2025

set -e  # Exit on error

echo "Setting up Jenkins for Weather_ops project..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker installed. You may need to log out and log back in to use Docker without sudo."
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installed."
fi

# Create a directory for Jenkins data
JENKINS_HOME="$HOME/jenkins_home"
mkdir -p $JENKINS_HOME

# Create Docker Compose file for Jenkins
cat > $JENKINS_HOME/docker-compose.yml << EOF
version: '3'
services:
  jenkins:
    image: jenkins/jenkins:lts
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - ./jenkins_data:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=true
    restart: unless-stopped
EOF

# Create directory for Jenkins data
mkdir -p $JENKINS_HOME/jenkins_data

# Set permissions for the Docker socket
sudo chmod 666 /var/run/docker.sock

echo "Starting Jenkins container..."
cd $JENKINS_HOME && docker-compose up -d

# Wait for Jenkins to start up
echo "Waiting for Jenkins to start up (this may take a few minutes)..."
until $(curl --output /dev/null --silent --head --fail http://localhost:8080); do
    printf '.'
    sleep 5
done

echo ""
echo "Jenkins is now running at http://localhost:8080"
echo "To complete setup, you need the initial admin password:"
echo "Run: docker exec jenkins_jenkins_1 cat /var/jenkins_home/secrets/initialAdminPassword"
echo ""
echo "After logging in:"
echo "1. Install suggested plugins"
echo "2. Create an admin user"
echo "3. Set up Docker Hub credentials with ID 'docker-hub-credentials'"
echo "4. Create a new Pipeline job pointing to your Weather_ops repository"
echo ""
echo "To stop Jenkins: cd $JENKINS_HOME && docker-compose down"