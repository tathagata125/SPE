pipeline {
    agent any
    
    parameters {
        booleanParam(name: 'FORCE_K8S_DEPLOY', defaultValue: false, description: 'Force actual deployment to Kubernetes (not simulation)')
    }
    
    environment {
        DOCKER_HUB_CREDS = credentials('dockerhub-login')
        DOCKER_BACKEND_IMAGE = "girish445g/weather-ops-backend:${BUILD_NUMBER}"
        DOCKER_FRONTEND_IMAGE = "girish445g/weather-ops-frontend:${BUILD_NUMBER}"
        LATEST_BACKEND_IMAGE = "girish445g/weather-ops-backend:latest"
        LATEST_FRONTEND_IMAGE = "girish445g/weather-ops-frontend:latest"
        PYTHON_VERSION = "3.12"
        // Set FORCE_K8S_DEPLOY based on parameter
        FORCE_K8S_DEPLOY = "${params.FORCE_K8S_DEPLOY == true ? '1' : '0'}"
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
                        # Create a bin directory in Jenkins home
                        mkdir -p $HOME/bin
                        
                        # Try apt installation if we have sudo without password
                        if command -v apt-get &> /dev/null && sudo -n true 2>/dev/null; then
                            sudo apt-get update && sudo apt-get install -y apt-transport-https gnupg
                            curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
                            echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee -a /etc/apt/sources.list.d/kubernetes.list
                            sudo apt-get update && sudo apt-get install -y kubectl
                        else
                            # Fall back to direct download if apt is not available or sudo needs password
                            KUBECTL_VERSION=$(curl -L -s https://dl.k8s.io/release/stable.txt)
                            echo "Downloading kubectl version ${KUBECTL_VERSION}..."
                            curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl"
                            chmod +x kubectl
                            mv kubectl $HOME/bin/
                            export PATH=$HOME/bin:$PATH
                            echo "kubectl installed at $HOME/bin/kubectl"
                        fi
                    else
                        echo "kubectl is already installed at $(which kubectl)"
                        kubectl version --client
                    fi
                    
                    # Add $HOME/bin to PATH permanently for this job
                    echo "export PATH=$HOME/bin:$PATH" >> $HOME/.bashrc
                    
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
                sh '''
                if [ "$FORCE_K8S_DEPLOY" = "1" ]; then
                    echo "Forcing actual deployment to Kubernetes..."
                    ./deploy_kubernetes.sh
                else
                    echo "Simulating Kubernetes deployment..."
                    echo "This is a simulated Kubernetes deployment environment."
                    echo "In a real deployment, Weather_ops would be deployed to a Kubernetes cluster with:"
                    echo "- Backend deployment (machine learning API)"
                    echo "- Frontend deployment (Streamlit UI)"
                    echo "- Persistent storage for weather data and models"
                    echo "- ConfigMaps for configuration"
                    echo "- Services for networking"
                    echo "- Ingress for external access"
                fi
                '''
            }
        }
        
        stage('Apply Kubernetes HPA') {
            steps {
                echo 'Applying backend HPA manifest to Kubernetes...'
                sh '''
                if [ "$FORCE_K8S_DEPLOY" = "1" ]; then
                    kubectl apply -f kubernetes/backend-hpa.yaml
                else
                    echo "Simulating HPA application..."
                    echo "In a real environment, this would configure horizontal pod autoscaling"
                    echo "to automatically scale the backend based on CPU usage."
                fi
                '''
            }
        }
        
        stage('Deploy Prometheus Monitoring') {
            steps {
                echo 'Setting up Prometheus monitoring...'
                sh '''
                if [ "$FORCE_K8S_DEPLOY" = "1" ]; then
                    echo "Deploying Prometheus to Kubernetes..."
                    kubectl apply -f kubernetes/prometheus/prometheus-configmap.yaml
                    kubectl apply -f kubernetes/prometheus/prometheus-deployment.yaml
                    kubectl apply -f kubernetes/prometheus/prometheus-service.yaml
                    echo "Prometheus deployed successfully."
                    echo "You can access the Prometheus dashboard by port-forwarding:"
                    echo "kubectl port-forward -n weather-ops svc/prometheus-service 9090:9090"
                else
                    echo "Simulating Prometheus deployment..."
                    echo "In a real environment, this would deploy Prometheus for monitoring:"
                    echo "- Backend API metrics (request count, latency)"
                    echo "- Model training and prediction counts"
                    echo "- System metrics (CPU, memory usage)"
                    echo "- Kubernetes metrics"
                fi
                '''
            }
        }
        
        stage('Deploy Grafana Dashboard') {
            steps {
                echo 'Setting up Grafana dashboards...'
                sh '''
                if [ "$FORCE_K8S_DEPLOY" = "1" ]; then
                    echo "Deploying Grafana to Kubernetes..."
                    
                    # Check if Grafana manifests exist, if not create them
                    if [ ! -f kubernetes/grafana/grafana-configmap.yaml ]; then
                        mkdir -p kubernetes/grafana
                        
                        # Create ConfigMap for Grafana datasources
                        cat > kubernetes/grafana/grafana-configmap.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
  namespace: weather-ops
data:
  prometheus.yaml: |-
    apiVersion: 1
    datasources:
    - name: Prometheus
      type: prometheus
      url: http://prometheus-service:9090
      access: proxy
      isDefault: true
EOF
                        
                        # Create Grafana deployment manifest
                        cat > kubernetes/grafana/grafana-deployment.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: weather-ops
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
          name: grafana
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
          requests:
            cpu: 100m
            memory: 256Mi
        volumeMounts:
        - name: grafana-datasources
          mountPath: /etc/grafana/provisioning/datasources
      volumes:
      - name: grafana-datasources
        configMap:
          name: grafana-datasources
EOF

                        # Create Grafana service manifest
                        cat > kubernetes/grafana/grafana-service.yaml << EOF
apiVersion: v1
kind: Service
metadata:
  name: grafana-service
  namespace: weather-ops
spec:
  selector:
    app: grafana
  ports:
  - port: 3000
    targetPort: 3000
    protocol: TCP
  type: ClusterIP
EOF
                    fi
                    
                    # Apply Grafana manifests
                    kubectl apply -f kubernetes/grafana/grafana-configmap.yaml
                    kubectl apply -f kubernetes/grafana/grafana-deployment.yaml
                    kubectl apply -f kubernetes/grafana/grafana-service.yaml
                    
                    echo "Grafana deployed successfully."
                    echo "You can access the Grafana dashboard by port-forwarding:"
                    echo "kubectl port-forward -n weather-ops svc/grafana-service 3000:3000"
                    echo "Default credentials: admin/admin"
                    
                    # Wait for Grafana to be ready
                    echo "Waiting for Grafana pod to be ready..."
                    kubectl wait --namespace weather-ops --for=condition=ready pod --selector=app=grafana --timeout=120s || echo "Grafana pod not ready in time, may still be starting"
                    
                else
                    echo "Simulating Grafana deployment..."
                    echo "In a real environment, this would deploy Grafana with:"
                    echo "- Prometheus datasource pre-configured"
                    echo "- Dashboards for Weather_ops application metrics"
                    echo "- Custom dashboards for model performance monitoring"
                    echo "- Alerts for critical performance issues"
                fi
                '''
            }
        }
        
        stage('Create Weather_ops Dashboard') {
            steps {
                echo 'Creating custom dashboards for Weather_ops...'
                sh '''
                if [ "$FORCE_K8S_DEPLOY" = "1" ]; then
                    echo "Creating a Weather_ops dashboard in Grafana..."
                    
                    # Create a dashboard JSON file
                    mkdir -p kubernetes/grafana/dashboards
                    cat > kubernetes/grafana/dashboards/weather-ops-dashboard.json << 'EOF'
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": "-- Grafana --",
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "panels": [
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Prometheus",
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "hiddenSeries": false,
      "id": 2,
      "legend": {
        "alignAsTable": true,
        "avg": false,
        "current": true,
        "max": true,
        "min": false,
        "rightSide": true,
        "show": true,
        "total": false,
        "values": true
      },
      "lines": true,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "dataLinks": []
      },
      "percentage": false,
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "expr": "rate(http_requests_total[5m])",
          "legendFormat": "{{method}} {{endpoint}} ({{status}})",
          "refId": "A"
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Request Rate (per second)",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "short",
          "label": "Requests/s",
          "logBase": 1,
          "max": null,
          "min": "0",
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Prometheus",
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "hiddenSeries": false,
      "id": 4,
      "legend": {
        "alignAsTable": true,
        "avg": true,
        "current": true,
        "max": true,
        "min": false,
        "rightSide": true,
        "show": true,
        "total": false,
        "values": true
      },
      "lines": true,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "dataLinks": []
      },
      "percentage": false,
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))",
          "legendFormat": "{{endpoint}} (p95)",
          "refId": "A"
        },
        {
          "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))",
          "legendFormat": "{{endpoint}} (p50)",
          "refId": "B"
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Response Time",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "s",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": "0",
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "datasource": "Prometheus",
      "gridPos": {
        "h": 8,
        "w": 8,
        "x": 0,
        "y": 8
      },
      "id": 6,
      "options": {
        "colorMode": "value",
        "fieldOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "defaults": {
            "mappings": [],
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {
                  "color": "green",
                  "value": null
                }
              ]
            },
            "unit": "none"
          },
          "overrides": [],
          "values": false
        },
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto"
      },
      "pluginVersion": "6.7.3",
      "targets": [
        {
          "expr": "model_predictions_total",
          "refId": "A"
        }
      ],
      "timeFrom": null,
      "timeShift": null,
      "title": "Total Model Predictions",
      "type": "stat"
    },
    {
      "datasource": "Prometheus",
      "gridPos": {
        "h": 8,
        "w": 8,
        "x": 8,
        "y": 8
      },
      "id": 8,
      "options": {
        "colorMode": "value",
        "fieldOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "defaults": {
            "mappings": [],
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {
                  "color": "green",
                  "value": null
                }
              ]
            },
            "unit": "none"
          },
          "overrides": [],
          "values": false
        },
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto"
      },
      "pluginVersion": "6.7.3",
      "targets": [
        {
          "expr": "model_training_total",
          "refId": "A"
        }
      ],
      "timeFrom": null,
      "timeShift": null,
      "title": "Model Retraining Count",
      "type": "stat"
    },
    {
      "datasource": "Prometheus",
      "gridPos": {
        "h": 8,
        "w": 8,
        "x": 16,
        "y": 8
      },
      "id": 10,
      "options": {
        "colorMode": "value",
        "fieldOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "defaults": {
            "mappings": [],
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {
                  "color": "green",
                  "value": null
                }
              ]
            },
            "unit": "none"
          },
          "overrides": [],
          "values": false
        },
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto"
      },
      "pluginVersion": "6.7.3",
      "targets": [
        {
          "expr": "data_upload_total",
          "refId": "A"
        }
      ],
      "timeFrom": null,
      "timeShift": null,
      "title": "Data Upload Count",
      "type": "stat"
    },
    {
      "datasource": "Prometheus",
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 16
      },
      "id": 12,
      "options": {
        "colorMode": "value",
        "fieldOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "defaults": {
            "mappings": [],
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {
                  "color": "green",
                  "value": null
                },
                {
                  "color": "red",
                  "value": 0.1
                }
              ]
            },
            "unit": "%"
          },
          "overrides": [],
          "values": false
        },
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto"
      },
      "pluginVersion": "6.7.3",
      "targets": [
        {
          "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100",
          "refId": "A"
        }
      ],
      "timeFrom": null,
      "timeShift": null,
      "title": "Error Rate (5xx)",
      "type": "stat"
    },
    {
      "datasource": "Prometheus",
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 16
      },
      "id": 14,
      "options": {
        "colorMode": "value",
        "fieldOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "defaults": {
            "mappings": [],
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {
                  "color": "green",
                  "value": null
                }
              ]
            }
          },
          "overrides": [],
          "values": false
        },
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "horizontal"
      },
      "pluginVersion": "6.7.3",
      "targets": [
        {
          "expr": "sum(rate(http_requests_total[5m])) by (endpoint)",
          "legendFormat": "{{endpoint}}",
          "refId": "A"
        }
      ],
      "timeFrom": null,
      "timeShift": null,
      "title": "Endpoint Usage",
      "type": "stat"
    }
  ],
  "refresh": "10s",
  "schemaVersion": 22,
  "style": "dark",
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "timepicker": {
    "refresh_intervals": [
      "5s",
      "10s",
      "30s",
      "1m",
      "5m",
      "15m",
      "30m",
      "1h",
      "2h",
      "1d"
    ]
  },
  "timezone": "",
  "title": "Weather_ops Application Dashboard",
  "uid": "weather-ops",
  "version": 1
}
EOF
                    
                    # Create ConfigMap for dashboards
                    cat > kubernetes/grafana/grafana-dashboard-configmap.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: weather-ops
data:
  dashboard-provider.yaml: |-
    apiVersion: 1
    providers:
    - name: 'default'
      orgId: 1
      folder: ''
      type: file
      disableDeletion: false
      updateIntervalSeconds: 10
      options:
        path: /var/lib/grafana/dashboards
EOF

                    # Update the Grafana deployment to use these dashboards
                    cat > kubernetes/grafana/grafana-dashboard-deployment.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: weather-ops
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
          name: grafana
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
          requests:
            cpu: 100m
            memory: 256Mi
        volumeMounts:
        - name: grafana-datasources
          mountPath: /etc/grafana/provisioning/datasources
        - name: grafana-dashboards-provider
          mountPath: /etc/grafana/provisioning/dashboards
        - name: grafana-dashboards
          mountPath: /var/lib/grafana/dashboards
      volumes:
      - name: grafana-datasources
        configMap:
          name: grafana-datasources
      - name: grafana-dashboards-provider
        configMap:
          name: grafana-dashboards
      - name: grafana-dashboards
        configMap:
          name: grafana-dashboards-json
EOF

                    # Create a ConfigMap for the dashboard JSON
                    kubectl create configmap grafana-dashboards-json -n weather-ops --from-file=weather-ops-dashboard.json=kubernetes/grafana/dashboards/weather-ops-dashboard.json --dry-run=client -o yaml | kubectl apply -f -
                    
                    # Apply the updated dashboard configurations
                    kubectl apply -f kubernetes/grafana/grafana-dashboard-configmap.yaml
                    kubectl apply -f kubernetes/grafana/grafana-dashboard-deployment.yaml
                    
                    # Restart Grafana to pick up the changes
                    kubectl rollout restart deployment/grafana -n weather-ops
                    
                    echo "Weather_ops dashboards created successfully."
                    echo "Access the dashboard at: http://localhost:3000/d/weather-ops/weather-ops-application-dashboard"
                    echo "(after setting up port-forwarding)"
                    
                else
                    echo "Simulating dashboard creation..."
                    echo "In a real environment, this would:"
                    echo "- Create a preconfigured Weather_ops application dashboard"
                    echo "- Set up monitoring for HTTP requests, latency, and error rates"
                    echo "- Add visualizations for model predictions and training counts"
                    echo "- Configure automatic dashboard refresh"
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