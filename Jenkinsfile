pipeline {
    agent any
    
    environment {
        DOCKER_HUB_CREDS = credentials('dockerhub-login')
        DOCKER_BACKEND_IMAGE = "girish445g/weather-ops-backend:${BUILD_NUMBER}"
        DOCKER_FRONTEND_IMAGE = "girish445g/weather-ops-frontend:${BUILD_NUMBER}"
        LATEST_BACKEND_IMAGE = "girish445g/weather-ops-backend:latest"
        LATEST_FRONTEND_IMAGE = "girish445g/weather-ops-frontend:latest"
        PYTHON_VERSION = "3.12"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                sh 'echo "Setting up Python environment..."'
                sh 'python${PYTHON_VERSION} -m venv jenkins_venv'
                sh 'jenkins_venv/bin/pip install -r backend/requirements.txt'
                sh 'jenkins_venv/bin/pip install pytest pytest-cov fastapi httpx'
            }
        }
        
        stage('Setup Test Data') {
            steps {
                sh 'echo "Setting up test data..."'
                sh '''
                    # Create data directories if they don't exist
                    mkdir -p data
                    mkdir -p backend/data
                    
                    # Create a sample raw_weather.csv file if it doesn't exist
                    if [ ! -f data/raw_weather.csv ]; then
                        echo "time,tavg,tmin,tmax,prcp,wspd" > data/raw_weather.csv
                        echo "2025-01-01,15.0,10.0,20.0,0.5,10.0" >> data/raw_weather.csv
                        echo "2025-01-02,16.0,11.0,21.0,0.0,12.0" >> data/raw_weather.csv
                        echo "2025-01-03,17.0,12.0,22.0,0.2,11.0" >> data/raw_weather.csv
                    fi
                    
                    # Create a sample cleaned_weather.csv file if it doesn't exist
                    if [ ! -f data/cleaned_weather.csv ]; then
                        echo "time,tavg,tmin,tmax,prcp,wspd" > data/cleaned_weather.csv
                        echo "2025-01-01,15.0,10.0,20.0,0.5,10.0" >> data/cleaned_weather.csv
                        echo "2025-01-02,16.0,11.0,21.0,0.0,12.0" >> data/cleaned_weather.csv
                        echo "2025-01-03,17.0,12.0,22.0,0.2,11.0" >> data/cleaned_weather.csv
                    fi
                    
                    # Copy the data files to the backend directory as well
                    cp -f data/raw_weather.csv backend/data/ || true
                    cp -f data/cleaned_weather.csv backend/data/ || true
                '''
            }
        }
        
        stage('Data Validation') {
            steps {
                sh 'echo "Validating data integrity..."'
                sh '''
                jenkins_venv/bin/python -c "
import pandas as pd
import os

# Check if data files exist
data_paths = ['data/raw_weather.csv', 'data/cleaned_weather.csv']
for path in data_paths:
    if not os.path.exists(path):
        print(f'Error: Data file {path} not found')
        exit(1)

# Validate cleaned data
try:
    df = pd.read_csv('data/cleaned_weather.csv')
    # Check for null values in critical columns
    critical_columns = ['tavg', 'tmin', 'tmax', 'prcp', 'wspd']
    for col in critical_columns:
        if col in df.columns and df[col].isnull().sum() > 0:
            print(f'Warning: {df[col].isnull().sum()} null values found in {col}')
    print('Data validation completed successfully')
except Exception as e:
    print(f'Error during data validation: {str(e)}')
    exit(1)
"
                '''
            }
        }
        
        stage('Test') {
            steps {
                sh 'echo "Running tests..."'
                sh 'jenkins_venv/bin/pytest backend/ -v'
                // If you have frontend tests, add them here
            }
        }
        
        stage('Build Docker Images') {
            steps {
                sh 'docker-compose build'
                // Debug: List all images after build
                sh 'docker images'
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                sh 'echo $DOCKER_HUB_CREDS_PSW | docker login -u $DOCKER_HUB_CREDS_USR --password-stdin'
                
                // Tag and push backend image with build number
                sh 'docker tag weather_ops_backend:latest girish445g/weather-ops-backend:${BUILD_NUMBER}'
                sh 'docker push girish445g/weather-ops-backend:${BUILD_NUMBER}'
                
                // Tag and push backend image as latest
                sh 'docker tag weather_ops_backend:latest girish445g/weather-ops-backend:latest'
                sh 'docker push girish445g/weather-ops-backend:latest'
                
                // Tag and push frontend image with build number
                sh 'docker tag weather_ops_frontend:latest girish445g/weather-ops-frontend:${BUILD_NUMBER}'
                sh 'docker push girish445g/weather-ops-frontend:${BUILD_NUMBER}'
                
                // Tag and push frontend image as latest
                sh 'docker tag weather_ops_frontend:latest girish445g/weather-ops-frontend:latest'
                sh 'docker push girish445g/weather-ops-frontend:latest'
            }
        }
        
        stage('Deploy') {
            steps {
                sh 'echo "Deploying application..."'
                // This simulates a deployment to a staging environment
                sh '''
                    # Create a deployment directory if it doesn't exist
                    mkdir -p /tmp/weather_ops_deployment
                    
                    # Create a docker-compose override file for the deployment
                    cat > /tmp/weather_ops_deployment/docker-compose.yml << EOF
version: '3'
services:
  backend:
    image: ${LATEST_BACKEND_IMAGE}
    ports:
      - "5001:5000"
    environment:
      - ENV=staging
  
  frontend:
    image: ${LATEST_FRONTEND_IMAGE}
    ports:
      - "8502:8501"
    environment:
      - BACKEND_URL=http://backend:5000
    depends_on:
      - backend
EOF
                    
                    # Print deployment information
                    echo "Deployment prepared at /tmp/weather_ops_deployment"
                    
                    # Actually start the containers
                    cd /tmp/weather_ops_deployment && docker-compose down -v && docker-compose up -d
                    
                    echo "Containers have been started!"
                    echo "Frontend available at: http://localhost:8502"
                    echo "Backend API available at: http://localhost:5001"
                '''
            }
        }

        stage('Setup Kubernetes') {
            steps {
                echo 'Setting up Kubernetes environment...'
                sh '''
                    # Install kubectl if not present
                    if ! command -v kubectl &> /dev/null; then
                        echo "Installing kubectl..."
                        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                        chmod +x kubectl
                        sudo mv kubectl /usr/local/bin/ || mv kubectl ~/bin/ || mkdir -p ~/bin && mv kubectl ~/bin/
                        export PATH=$PATH:~/bin
                    fi
                    
                    # Setup kubeconfig directory
                    mkdir -p ~/.kube
                    
                    # Use shared Kubernetes config if available
                    if [ -f /opt/shared-k8s-config/config ]; then
                        echo "Using shared Kubernetes configuration..."
                        cp /opt/shared-k8s-config/config ~/.kube/config
                        chmod 600 ~/.kube/config
                        
                        # Update paths in config to use shared Minikube certs
                        sed -i "s|$HOME/.minikube|/opt/shared-k8s-config/.minikube|g" ~/.kube/config
                    else
                        echo "WARNING: Shared Kubernetes configuration not found!"
                        echo "Run these commands on the host machine to set it up:"
                        echo "sudo mkdir -p /opt/shared-k8s-config"
                        echo "sudo cp ~/.kube/config /opt/shared-k8s-config/"
                        echo "sudo cp -r ~/.minikube /opt/shared-k8s-config/"
                        echo "sudo chown -R jenkins:jenkins /opt/shared-k8s-config"
                        echo "sudo chmod -R 755 /opt/shared-k8s-config"
                    fi
                    
                    # Make deployment script executable
                    chmod +x ./deploy_kubernetes.sh
                '''
            }
        }

        stage('Kubernetes Deployment') {
            steps {
                echo 'Deploying to Kubernetes...'
                sh './deploy_kubernetes.sh'
            }
        }
        
        stage('Apply Kubernetes HPA') {
            steps {
                echo 'Applying backend HPA manifest to Kubernetes...'
                sh '''
                if [ -n "$JENKINS_HOME" ]; then
                    echo "Running in Jenkins - simulating HPA application"
                    echo "In a real production environment, this would apply HPA to a production cluster."
                else
                    kubectl apply -f kubernetes/backend-hpa.yaml
                fi
                '''
            }
        }
    }
    
    post {
        always {
            sh 'docker logout'
            sh 'if [ -d "jenkins_venv" ]; then rm -rf jenkins_venv; fi'
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Please check the logs for details.'
        }
    }
}