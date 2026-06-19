# 🌐 COMPLETE NETWORK ARCHITECTURE GUIDE
## From AWS Users to Your Database - Everything Explained

---

## TABLE OF CONTENTS
1. [Real-World Data Flow](#real-world-data-flow)
2. [Network Architecture Overview](#network-architecture-overview)
3. [Docker Compose Network (Local Development)](#docker-compose-network-local-development)
4. [Kubernetes Network (Production)](#kubernetes-network-production)
5. [Port Mappings & Endpoints](#port-mappings--endpoints)
6. [YAML Explanations](#yaml-explanations)
7. [How to Read Output & Debug](#how-to-read-output--debug)
8. [AWS Integration](#aws-integration)

---

# 1️⃣ REAL-WORLD DATA FLOW

## Journey of a User Request: From AWS to Your Database

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        USER REQUEST JOURNEY                                 │
└─────────────────────────────────────────────────────────────────────────────┘

STEP 1: USER MAKES REQUEST (AWS Region)
═══════════════════════════════════════════════════════════════════════════════
User in Mumbai/Bangalore opens browser:
  ↓
  Types: https://dev.shivalayammtp.club/employees
  
  ↓
  Browser sends HTTP request to AWS Route 53 (DNS)


STEP 2: AWS ROUTE 53 - DNS RESOLUTION
═══════════════════════════════════════════════════════════════════════════════
Route 53 receives: "Resolve dev.shivalayammtp.club"
  ↓
  Looks up DNS records in Route 53 console
  ↓
  Returns: IP Address of AWS Load Balancer (e.g., 52.XX.XX.XX)


STEP 3: AWS APPLICATION LOAD BALANCER (ALB)
═══════════════════════════════════════════════════════════════════════════════
Request hits ALB on port 443 (HTTPS):
  ┌────────────────────────────────────────┐
  │ ALB: 52.XX.XX.XX:443                   │
  │ (Internet-facing, public IP)           │
  │                                        │
  │ - Accepts incoming traffic             │
  │ - Terminates SSL/TLS encryption        │
  │ - Routes to target group               │
  └────────────────────────────────────────┘
  
  ↓
  ALB adds headers (X-Forwarded-For, X-Forwarded-Proto)
  ↓
  Forwards to: EKS Cluster Ingress (inside VPC)


STEP 4: AWS VPC NETWORK
═══════════════════════════════════════════════════════════════════════════════
Request enters VPC (Private network, 10.0.0.0/16):
  
  ┌─────────────────────────────────────────────────────────┐
  │            AWS VPC (Virtual Private Cloud)              │
  │         CIDR Block: 10.0.0.0/16 (65,536 IPs)            │
  │                                                         │
  │  ┌──────────────────────────────────────────────────┐   │
  │  │        EKS Cluster (Kubernetes Control Plane)    │   │
  │  │                                                  │   │
  │  │  - 3 Control Plane nodes (managed by AWS)        │   │
  │  │  - Auto Scaling Group for worker nodes           │   │
  │  └──────────────────────────────────────────────────┘   │
  │                                                         │
  │  ┌──────────────────────────────────────────────────┐   │
  │  │      Availability Zone 1 (us-east-1a)           │   │
  │  │  CIDR: 10.0.1.0/24 (subnet with 256 IPs)        │   │
  │  │                                                  │   │
  │  │  ┌─────────────────────────────────────────┐    │   │
  │  │  │ EC2 Worker Node 1 (EKS Node)            │    │   │
  │  │  │ IP: 10.0.1.50                           │    │   │
  │  │  │                                         │    │   │
  │  │  │ ┌────────────────────────────────────┐  │    │   │
  │  │  │ │ Kubernetes Pod                     │  │    │   │
  │  │  │ │ (Employee App Container)           │  │    │   │
  │  │  │ │ IP: 10.0.1.100 (Pod IP)            │  │    │   │
  │  │  │ │ Port: 8000 (internal)              │  │    │   │
  │  │  │ │                                    │  │    │   │
  │  │  │ │ Listening for requests...          │  │    │   │
  │  │  │ └────────────────────────────────────┘  │    │   │
  │  │  └─────────────────────────────────────────┘    │   │
  │  └──────────────────────────────────────────────────┘   │
  │                                                         │
  │  ┌──────────────────────────────────────────────────┐   │
  │  │      Availability Zone 2 (us-east-1b)           │   │
  │  │  CIDR: 10.0.2.0/24 (subnet with 256 IPs)        │   │
  │  │                                                  │   │
  │  │  [Similar worker nodes and pods...]             │   │
  │  └──────────────────────────────────────────────────┘   │
  │                                                         │
  │  ┌──────────────────────────────────────────────────┐   │
  │  │   RDS Database Subnet (Private)                  │   │
  │  │  CIDR: 10.0.100.0/24                            │   │
  │  │                                                  │   │
  │  │  ┌──────────────────────────────────────────┐   │   │
  │  │  │ PostgreSQL RDS Instance                 │   │   │
  │  │  │ IP: 10.0.100.50                         │   │   │
  │  │  │ Port: 5432                              │   │   │
  │  │  │ (Only accessible from within VPC)       │   │   │
  │  │  └──────────────────────────────────────────┘   │   │
  │  └──────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────┘


STEP 5: KUBERNETES INGRESS CONTROLLER
═══════════════════════════════════════════════════════════════════════════════
Request hits Nginx Ingress Controller (running as Pod):
  
  ┌─────────────────────────────────────┐
  │  Ingress Controller Pod             │
  │  (Nginx - runs in kube-system ns)   │
  │  IP: 10.0.1.101                     │
  │  Port: 443 (HTTPS) / 80 (HTTP)      │
  │                                     │
  │  Job: Route external traffic to     │
  │  internal services                  │
  └─────────────────────────────────────┘
  
  Ingress Controller reads rules from:
  Name: employee-ingress
  Host: dev.shivalayammtp.club
  Path: /
  Service: employee-service:8000
  
  ↓
  Controller routes request to Service IP


STEP 6: KUBERNETES SERVICE (LOAD BALANCER)
═══════════════════════════════════════════════════════════════════════════════
Request hits Service (Virtual IP - ClusterIP):
  
  ┌──────────────────────────────────────────────┐
  │  Service: employee-service                   │
  │  Type: ClusterIP                             │
  │  Cluster IP: 10.96.0.50 (Virtual/DNS name)  │
  │  Port: 8000                                  │
  │  Protocol: TCP                               │
  │                                              │
  │  Selector: app=employee-app                  │
  │  (Routes to Pods with this label)            │
  │                                              │
  │  Load Balance Algorithm: Round Robin         │
  └──────────────────────────────────────────────┘
  
  Service finds Endpoints (Pod IPs):
  - 10.0.1.100:8000
  - 10.0.2.100:8000
  - 10.0.1.101:8000
  
  ↓
  Distributes traffic to Pods in round-robin


STEP 7: KUBERNETES POD (CONTAINER)
═══════════════════════════════════════════════════════════════════════════════
Request arrives at Pod:
  
  ┌────────────────────────────────────────────┐
  │  Pod: employee-app-5f4d8c9b2-xyz1a         │
  │  IP: 10.0.1.100                            │
  │  Port: 8000                                │
  │                                            │
  │  ┌──────────────────────────────────────┐  │
  │  │  Docker Container                    │  │
  │  │  (FastAPI App - Python/Uvicorn)      │  │
  │  │                                      │  │
  │  │  Listening on 0.0.0.0:8000           │  │
  │  │                                      │  │
  │  │  Reads request URL: /employees       │  │
  │  │  Matches to route in FastAPI         │  │
  │  │                                      │  │
  │  │  Example route:                      │  │
  │  │  @app.get("/employees")              │  │
  │  │  def get_employees():                │  │
  │  │      ...                             │  │
  │  │                                      │  │
  │  │  Now needs to query database         │  │
  │  └──────────────────────────────────────┘  │
  └────────────────────────────────────────────┘
  
  ↓
  Pod retrieves DB_HOST from ConfigMap:
  DB_HOST: postgres-service (Kubernetes DNS)


STEP 8: INTERNAL KUBERNETES DNS RESOLUTION
═══════════════════════════════════════════════════════════════════════════════
Pod queries CoreDNS (Kubernetes internal DNS):
  
  Query: "postgres-service.dev.svc.cluster.local"
  ↓
  CoreDNS returns Cluster IP of postgres-service
  ↓
  IP: 10.96.0.200 (Virtual IP of postgres service)


STEP 9: DATABASE SERVICE (POSTGRES SERVICE)
═══════════════════════════════════════════════════════════════════════════════
Request hits postgres-service:
  
  ┌──────────────────────────────────────────────┐
  │  Service: postgres-service                   │
  │  Type: ClusterIP                             │
  │  Cluster IP: 10.96.0.200                     │
  │  Port: 5432                                  │
  │  Protocol: TCP                               │
  │                                              │
  │  Routes to Pod with label: app=postgres      │
  └──────────────────────────────────────────────┘
  
  ↓
  Routes to PostgreSQL Pod


STEP 10: DATABASE POD
═══════════════════════════════════════════════════════════════════════════════
Request reaches PostgreSQL Container:
  
  ┌────────────────────────────────────────────┐
  │  Pod: postgres-deployment-xyz2b             │
  │  IP: 10.0.100.100                           │
  │  Port: 5432                                 │
  │                                            │
  │  ┌──────────────────────────────────────┐  │
  │  │  PostgreSQL Database                 │  │
  │  │  Listening on 0.0.0.0:5432           │  │
  │  │                                      │  │
  │  │  Database: hrdb                      │  │
  │  │  User: hradmin                       │  │
  │  │  Password: encrypted from Secret     │  │
  │  │                                      │  │
  │  │  Executes query from app             │  │
  │  │  Returns employee data               │  │
  │  └──────────────────────────────────────┘  │
  └────────────────────────────────────────────┘


STEP 11: RETURN PATH (Response)
═══════════════════════════════════════════════════════════════════════════════
Database → Pod → Service → Ingress → ALB → Route 53 → User

Response travels back through same path:
1. PostgreSQL returns result set
2. FastAPI Pod formats as JSON
3. employee-service routes response
4. Ingress Controller passes through
5. ALB routes to user's IP
6. User receives HTML/JSON in browser
7. Browser renders page


COMPLETE REQUEST-RESPONSE TIME:
═══════════════════════════════════════════════════════════════════════════════
User Request Initiated (t=0ms)
  ├─ DNS Resolution: 10-50ms
  ├─ ALB Processing: 5-10ms
  ├─ Ingress Controller: 2-5ms
  ├─ Service Discovery: 1-2ms
  ├─ Pod Processing (App Logic): 50-200ms
  ├─ Database Query: 20-100ms
  ├─ Response Serialization: 10-50ms
  ├─ Ingress Response: 2-5ms
  ├─ ALB Response: 5-10ms
  └─ Network Transmission: 50-100ms
      ══════════════════════════════════
      Total Time: 155-532ms (typical)

```

---

# 2️⃣ NETWORK ARCHITECTURE OVERVIEW

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             INTERNET 
/ USERS                                │
│                        (Public, Outside AWS)                               │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ↓
                    ┌──────────────────────┐
                    │  AWS Route 53 (DNS)  │
                    │ Resolves domain to   │
                    │ ALB IP Address       │
                    └──────────────────────┘
                               │
                               ↓
            ┌──────────────────────────────────────┐
            │  Internet Gateway (IGW)              │
            │  Connects VPC to Internet            │
            └──────────────────────────────────────┘
                               │
                               ↓
            ┌──────────────────────────────────────┐
            │  AWS Application Load Balancer (ALB) │
            │  Public IP: 52.XX.XX.XX              │
            │  Port 443 (HTTPS) & 80 (HTTP)        │
            │  Terminates SSL/TLS                  │
            │  Routes to Ingress Controller        │
            └──────────────────────────────────────┘
                               │
                               ↓
        ┌─────────────────────────────────────────────────┐
        │          AWS VPC (Private Network)              │
        │    CIDR Block: 10.0.0.0/16                      │
        │    (Contains all private resources)             │
        │                                                 │
        │  ┌────────────────────────────────────────────┐ │
        │  │    EKS Cluster (Kubernetes)                │ │
        │  │                                            │ │
        │  │  ┌─────────────────────────────────────┐   │ │
        │  │  │ Availability Zone 1 (us-east-1a)    │   │ │
        │  │  │ Subnet: 10.0.1.0/24                 │   │ │
        │  │  │                                     │   │ │
        │  │  │  ┌───────────────────────────────┐  │   │ │
        │  │  │  │ EC2 Worker Node 1             │  │   │ │
        │  │  │  │ IP: 10.0.1.50                 │  │   │ │
        │  │  │  │                               │  │   │ │
        │  │  │  │ ┌─────────────────────────┐   │  │   │ │
        │  │  │  │ │ App Pod (Replica 1)     │   │  │   │ │
        │  │  │  │ │ IP: 10.0.1.100          │   │  │   │ │
        │  │  │  │ │ Port: 8000              │   │  │   │ │
        │  │  │  │ └─────────────────────────┘   │  │   │ │
        │  │  │  │                               │  │   │ │
        │  │  │  │ ┌─────────────────────────┐   │  │   │ │
        │  │  │  │ │ Ingress Controller      │   │  │   │ │
        │  │  │  │ │ (Nginx)                 │   │  │   │ │
        │  │  │  │ │ IP: 10.0.1.101          │   │  │   │ │
        │  │  │  │ │ Port: 443/80            │   │  │   │ │
        │  │  │  │ └─────────────────────────┘   │  │   │ │
        │  │  │  └───────────────────────────────┘  │   │ │
        │  │  └─────────────────────────────────────┘   │ │
        │  │                                            │ │
        │  │  ┌─────────────────────────────────────┐   │ │
        │  │  │ Availability Zone 2 (us-east-1b)    │   │ │
        │  │  │ Subnet: 10.0.2.0/24                 │   │ │
        │  │  │                                     │   │ │
        │  │  │  ┌───────────────────────────────┐  │   │ │
        │  │  │  │ EC2 Worker Node 2             │  │   │ │
        │  │  │  │ IP: 10.0.2.50                 │  │   │ │
        │  │  │  │                               │  │   │ │
        │  │  │  │ ┌─────────────────────────┐   │  │   │ │
        │  │  │  │ │ App Pod (Replica 2)     │   │  │   │ │
        │  │  │  │ │ IP: 10.0.2.100          │   │  │   │ │
        │  │  │  │ │ Port: 8000              │   │  │   │ │
        │  │  │  │ └─────────────────────────┘   │  │   │ │
        │  │  │  └───────────────────────────────┘  │   │ │
        │  │  └─────────────────────────────────────┘   │ │
        │  │                                            │ │
        │  │  ┌─────────────────────────────────────┐   │ │
        │  │  │ Kubernetes Services (Virtual IPs)   │   │ │
        │  │  │                                     │   │ │
        │  │  │ Service: employee-service          │   │ │
        │  │  │ Type: ClusterIP                     │   │ │
        │  │  │ Cluster IP: 10.96.0.50              │   │ │
        │  │  │ Port: 8000                          │   │ │
        │  │  │ Endpoints: [10.0.1.100, 10.0.2.100]│   │ │
        │  │  │                                     │   │ │
        │  │  │ Service: postgres-service          │   │ │
        │  │  │ Type: ClusterIP                     │   │ │
        │  │  │ Cluster IP: 10.96.0.200             │   │ │
        │  │  │ Port: 5432                          │   │ │
        │  │  │ Endpoints: [10.0.100.100]           │   │ │
        │  │  └─────────────────────────────────────┘   │ │
        │  └────────────────────────────────────────────┘ │
        │                                                 │
        │  ┌────────────────────────────────────────────┐ │
        │  │  RDS - PostgreSQL Database                │ │
        │  │  (Managed by AWS)                         │ │
        │  │                                            │ │
        │  │  Private Subnet: 10.0.100.0/24            │ │
        │  │  Primary Node IP: 10.0.100.50             │ │
        │  │  Standby Node IP: 10.0.101.50 (DR)        │ │
        │  │  Port: 5432                               │ │
        │  │  Database: hrdb                           │ │
        │  │  Security Group: Only allow from EKS      │ │
        │  │                                            │ │
        │  │  Multi-AZ: Yes (HA + Backup)             │ │
        │  │  Automated Backups: 7 days                │ │
        │  └────────────────────────────────────────────┘ │
        │                                                 │
        └─────────────────────────────────────────────────┘

```

---

# 3️⃣ DOCKER COMPOSE NETWORK (LOCAL DEVELOPMENT)

## Purpose
Local development environment that mirrors production on your laptop/dev machine.

## What Docker Compose Does

When you run: `docker-compose -f docker-compose-app.yml up`

```
┌────────────────────────────────────────────────────────┐
│    Docker Host Machine (Your Laptop)                   │
│    IP: localhost (127.0.0.1)                           │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Docker Bridge Network: employee-service_default│  │
│  │  CIDR: 172.18.0.0/16 (Docker internal)          │  │
│  │                                                  │  │
│  │  ┌──────────────────────────────┐               │  │
│  │  │ Container: employee-postgres │               │  │
│  │  │ Container ID: 7a3b2c9d...    │               │  │
│  │  │ Internal IP: 172.18.0.2      │               │  │
│  │  │ Port: 5432                   │               │  │
│  │  │ Hostname: postgres           │               │  │
│  │  │ Exposed Port: 5433 on host   │               │  │
│  │  │                              │               │  │
│  │  │ Environment:                 │               │  │
│  │  │ - POSTGRES_DB: hrdb          │               │  │
│  │  │ - POSTGRES_USER: hradmin     │               │  │
│  │  │ - POSTGRES_PASSWORD: hrpass  │               │  │
│  │  │                              │               │  │
│  │  │ Volume Mount:                │               │  │
│  │  │ /var/lib/postgresql/data →   │               │  │
│  │  │ ~/docker_volumes/postgres/   │               │  │
│  │  └──────────────────────────────┘               │  │
│  │                ↑                                 │  │
│  │                │ (Docker Network)               │  │
│  │                ↓                                 │  │
│  │  ┌──────────────────────────────┐               │  │
│  │  │ Container: employee-app      │               │  │
│  │  │ Container ID: 9f8e7d6c...    │               │  │
│  │  │ Internal IP: 172.18.0.3      │               │  │
│  │  │ Port: 8000                   │               │  │
│  │  │ Hostname: employee-app       │               │  │
│  │  │ Exposed Port: 8000 on host   │               │  │
│  │  │                              │               │  │
│  │  │ Environment Variables:       │               │  │
│  │  │ (from .env file)             │               │  │
│  │  │ - DB_HOST: postgres          │               │  │
│  │  │   (Docker resolves to        │               │  │
│  │  │    172.18.0.2)               │               │  │
│  │  │ - DB_PORT: 5432             │               │  │
│  │  │ - DB_NAME: hrdb              │               │  │
│  │  │ - DB_USER: hradmin           │               │  │
│  │  │ - DB_PASSWORD: hrpassword    │               │  │
│  │  │                              │               │  │
│  │  │ Depends On: postgres         │               │  │
│  │  │ (Starts after postgres)      │               │  │
│  │  └──────────────────────────────┘               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  Port Mappings (Host Access):                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ localhost:5433 → Container:5432 (PostgreSQL)    │  │
│  │ localhost:8000 → Container:8000 (FastAPI App)   │  │
│  │                                                  │  │
│  │ You access: http://localhost:8000/employees    │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

## Docker Network Communication

### How Services Talk to Each Other

**Container-to-Container Communication:**
```
1. employee-app container needs to connect to PostgreSQL
2. Looks up: DB_HOST=postgres (from .env)
3. Docker embedded DNS (127.0.0.11:53) resolves "postgres"
4. Returns: 172.18.0.2 (postgres container IP)
5. employee-app connects to 172.18.0.2:5432
6. PostgreSQL responds
```

### Docker Network Driver

```
Type: bridge (Default for docker-compose)
Name: employee-service_default
Subnet: 172.18.0.0/16 (65,536 possible IPs)
Gateway: 172.18.0.1 (Docker-managed)

```

---

# 4️⃣ KUBERNETES NETWORK (PRODUCTION)

## What Each YAML File Does

### A. DEPLOYMENT.YAML - Creates Pods

```yaml
apiVersion: apps/v1
kind: Deployment                    # Type: Creates and manages Pods

metadata:
  name: employee-app               # Name: How you reference this deployment
  namespace: dev                   # Namespace: Logical isolation (like folder)
                                  # - Separates dev/staging/prod
                                  # - Each has own policies

spec:
  replicas: 1                      # Number of copies: 1 Pod running
                                  # In production: replicas: 3-5 for HA
                                  # Kubernetes auto-restarts if Pod dies

  selector:
    matchLabels:
      app: employee-app            # Pod Selector: Routes traffic to Pods
                                  # with label "app: employee-app"
                                  # Service uses this to find Pods

  template:
    metadata:
      labels:
        app: employee-app          # Labels: Used for selection and grouping
                                  # Can have multiple labels
                                  # Example: 
                                  # env: dev
                                  # version: v2
                                  # tier: backend

    spec:
      containers:
      - name: employee-app         # Container name in Pod
        
        image: raviteja21k/employee-service:16
                                  # Docker image to run
                                  # raviteja21k = Docker Hub username
                                  # employee-service = image name
                                  # 16 = image tag/version
                                  # Full path: docker.io/raviteja21k/...

        ports:
        - containerPort: 8000      # Port INSIDE container
                                  # FastAPI app listens on 8000
                                  # Must match CMD in Dockerfile:
                                  # uvicorn app.main:app --port 8000

        env:                       # Environment variables for app
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: employee-config  # ConfigMap name
              key: DB_HOST          # Key in ConfigMap
                                    # Value: postgres-service
                                    # This is Kubernetes DNS name

        - name: DB_PORT
          valueFrom:
            configMapKeyRef:
              name: employee-config
              key: DB_PORT          # Value: "5432"

        - name: DB_NAME
          valueFrom:
            configMapKeyRef:
              name: employee-config
              key: DB_NAME          # Value: hrdb

        - name: DB_USER
          valueFrom:
            secretKeyRef:           # Secrets = Encrypted ConfigMap
              name: employee-secret # Secret object name
              key: DB_USER          # Key in Secret
                                    # Value: hradmin (base64 encoded in etcd)

        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: employee-secret
              key: DB_PASSWORD      # Value: hrpassword (encrypted)

        livenessProbe:              # Is app still running?
          httpGet:                  # Check via HTTP
            path: /health           # Endpoint to check
            port: 8000              # On which port
          initialDelaySeconds: 20   # Wait 20s after Pod start
                                    # (app needs time to initialize)
                                    # (don't check too early)
          
          # Default:
          # periodSeconds: 10       # Check every 10 seconds
          # failureThreshold: 3     # Fail after 3 failed checks
          # If fails: Kubernetes KILLS and RESTARTS Pod

        readinessProbe:             # Is app ready to accept traffic?
          httpGet:
            path: /health           # Same /health endpoint
            port: 8000
          initialDelaySeconds: 10   # Wait 10s before first check
          
          # If check fails:
          # - Pod stays running
          # - Removed from Service endpoints
          # - No traffic routed to it
          # - Useful during deployment/startup

        resources:                  # CPU & Memory limits
          requests:                 # Guaranteed minimum
            cpu: "100m"             # 100 millicores (0.1 CPU)
                                    # 1 CPU = 1000m
                                    # 100m = 10% of 1 CPU
            memory: "128Mi"         # 128 Megabytes
          
          limits:                   # Maximum allowed
            cpu: "250m"             # Can use up to 250m
            memory: "256Mi"         # Can use up to 256Mi
          
          # If app exceeds limits:
          # - CPU: Throttled (slowed down)
          # - Memory: OOMKilled (killed and restarted)
```

### B. SERVICE.YAML - Internal Load Balancer

```yaml
apiVersion: v1
kind: Service                        # Type: Virtual Load Balancer

metadata:
  name: employee-service             # Service name
  namespace: dev                      # Same namespace as Pods

spec:
  selector:
    app: employee-app                # Find Pods with this label
                                     # Routes traffic to matching Pods
                                     # If 3 Pods match: Load balance across all 3

  ports:
    - port: 8000                     # Service port (external to Pod)
                                     # What clients call: service:8000
      targetPort: 8000               # Pod port (container's listening port)
                                     # Maps to container port in Deployment
                                     # Traffic: service:8000 → Pod:8000

  type: ClusterIP                    # Type of Service
                                     # ClusterIP = Internal only
                                     # Only reachable within cluster
                                     # Gets virtual IP: 10.96.0.50
                                     # No external access
```

**What ClusterIP Does:**
```
┌─────────────────────────────────────────────┐
│  Service: employee-service                  │
│  ClusterIP: 10.96.0.50 (Virtual IP)         │
│  Port: 8000                                 │
│                                             │
│  When any Pod/Container inside cluster      │
│  tries to connect to: employee-service:8000 │
│                                             │
│  1. Kubernetes DNS resolves:                │
│     employee-service.dev.svc.cluster.local  │
│     → 10.96.0.50                            │
│                                             │
│  2. Connection goes to Service              │
│                                             │
│  3. Service kube-proxy intercepts           │
│     (iptables rules)                        │
│                                             │
│  4. Load balances to Pod IPs:               │
│     - 10.0.1.100:8000 (Pod 1)               │
│     - 10.0.2.100:8000 (Pod 2)               │
│     - Round robin distribution              │
│                                             │
│  5. Pod processes request                   │
│  6. Response returns through same path      │
└─────────────────────────────────────────────┘
```

### C. INGRESS.YAML - External Access

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress                         # Type: HTTP/HTTPS routing

metadata:
  name: employee-ingress              # Ingress name
  namespace: dev

spec:
  ingressClassName: nginx             # Use Nginx controller
                                      # (Must be installed in cluster)
                                      # Other options: traefik, aws-alb, etc.

  rules:                              # Routing rules
  - host: dev.shivalayammtp.club      # Domain name
                                      # DNS must point to Ingress Controller IP
                                      # When request comes for this domain:

    http:
      paths:
      - path: /                       # URL path
                                      # / = all paths
                                      # Can also be:
                                      # /api/v1 = only /api/v1/*
                                      # /employees = only /employees*
        
        pathType: Prefix              # Match type
                                      # Prefix = starts with /
                                      # Exact = exact match
                                      # ImplementationSpecific = controller decides

        backend:                      # Where to send traffic
          service:
            name: employee-service    # Send to employee-service
            
            port:
              number: 8000            # Port: 8000

# What Happens When User Visits: dev.shivalayammtp.club
# 1. Browser sends HTTP request
# 2. DNS resolves to Ingress Controller IP (10.0.1.101)
# 3. Request hits Ingress Controller (Nginx Pod)
# 4. Controller reads this Ingress rule
# 5. Matches: host=dev.shivalayammtp.club, path=/
# 6. Routes to: employee-service:8000
# 7. Service load balances to Pods
# 8. Pod processes request
```

### D. CONFIGMAP.YAML - Configuration Storage

```yaml
apiVersion: v1
kind: ConfigMap                       # Type: Key-value config storage
                                      # Plain text (NOT encrypted)

metadata:
  name: employee-config               # ConfigMap name
  namespace: dev

data:                                 # Key-value pairs
  DB_HOST: postgres-service           # Key: DB_HOST
                                      # Value: postgres-service
                                      # (Kubernetes DNS name of postgres Service)

  DB_PORT: "5432"                     # Key: DB_PORT
                                      # Value: "5432" (as string)
                                      # Note: quotes = string type

  DB_NAME: hrdb                       # Database name

# How to Use ConfigMap:
# In Deployment, reference like:
# env:
#   - name: DB_HOST
#     valueFrom:
#       configMapKeyRef:
#         name: employee-config
#         key: DB_HOST
# 
# Result: Pod gets env var DB_HOST=postgres-service

# Advantages:
# - Change value in ConfigMap
# - Redeploy Pod
# - New value applied
# - No need to rebuild Docker image
```

---

# 5️⃣ PORT MAPPINGS & ENDPOINTS

## Complete Port Reference

### Development (Docker Compose)

| Service | Container Port | Host Port | Purpose | Access |
|---------|-----------------|-----------|---------|--------|
| FastAPI App | 8000 | 8000 | API Application | `http://localhost:8000` |
| PostgreSQL | 5432 | 5433 | Database | `localhost:5433` (psql client) |
| Jenkins | 8080 | 8080 | CI/CD Pipeline | `http://localhost:8080` |
| SonarQube | 9000 | 9000 | Code Quality | `http://localhost:9000` |

### Production (Kubernetes)

| Component | Port | Type | Internal? | External? | How to Access |
|-----------|------|------|-----------|-----------|-----------------|
| ALB | 443/80 | Ingress | No | Yes | `https://dev.shivalayammtp.club` |
| Ingress Controller | 443/80 | Service | Internal | Via ALB | Through ALB |
| employee-service | 8000 | ClusterIP | Yes | No | `employee-service.dev.svc.cluster.local:8000` |
| postgres-service | 5432 | ClusterIP | Yes | No | `postgres-service.dev.svc.cluster.local:5432` |
| App Pod | 8000 | Pod IP | Yes | No | `10.0.1.100:8000` (internal only) |
| DB Pod | 5432 | Pod IP | Yes | No | `10.0.100.100:5432` (internal only) |

## Service Discovery Examples

### From App Pod to Database

**Old Way (Manual IP):**
```
App hardcodes: DB_HOST=10.0.100.100
Problem: If DB Pod restarts, gets new IP, app breaks
```

**Kubernetes Way (DNS):**
```
App uses: DB_HOST=postgres-service
Kubernetes DNS resolves to: 10.96.0.200 (Service Virtual IP)
Service routes to: 10.0.100.100 (Current DB Pod IP)
If DB restarts: New IP assigned, but Service still returns same VIP
Problem solved! ✓
```

---

# 6️⃣ YAML EXPLANATIONS

## What Each Field Does & Why It Exists

### DEPLOYMENT FIELDS

| Field | Value | Meaning | Why |
|-------|-------|---------|-----|
| `apiVersion` | `apps/v1` | Kubernetes API version | Compatibility with cluster |
| `kind` | `Deployment` | Resource type | Tells K8s this is a Deployment (not Pod/Service) |
| `metadata.name` | `employee-app` | Identifier | Reference name in logs/commands |
| `metadata.namespace` | `dev` | Logical isolation | Separates dev/staging/prod resources |
| `spec.replicas` | `1` | Number of Pods | 3+ recommended for production |
| `selector.matchLabels` | `app: employee-app` | Pod filter | Service uses this to find Pods |
| `template.labels` | `app: employee-app` | Pod identifier | Must match selector |
| `spec.containers[0].image` | `raviteja21k/employee-service:16` | Docker image | Which container to run |
| `containerPort` | `8000` | Listen port | Where app listens inside Pod |
| `env[].name` | `DB_HOST` | Variable name | How app accesses value |
| `configMapKeyRef.name` | `employee-config` | ConfigMap source | Where to get value |
| `configMapKeyRef.key` | `DB_HOST` | ConfigMap key | Which value to get |
| `livenessProbe.path` | `/health` | Health check endpoint | Kubernetes calls this every 10s |
| `initialDelaySeconds` | `20` | Startup grace period | Time before first health check |
| `requests.cpu` | `100m` | Minimum CPU | Scheduler: Pod needs this to run |
| `limits.cpu` | `250m` | Maximum CPU | Throttle if exceeded |

---

# 7️⃣ HOW TO READ OUTPUT & DEBUG

## Reading Kubernetes Output

### kubectl get pods

```bash
$ kubectl get pods -n dev

NAME                                 READY   STATUS    RESTARTS   AGE
employee-app-5f4d8c9b2-xyz1a        1/1     Running   0          2d
employee-app-5f4d8c9b2-xyz2b        1/1     Running   0          2d
postgres-deployment-abc1234-xyz3c   1/1     Running   0          5d
```

**Field Explanations:**

| Column | Value | Meaning |
|--------|-------|---------|
| `NAME` | `employee-app-5f4d8c9b2-xyz1a` | Pod name (auto-generated by Deployment) |
| `READY` | `1/1` | Containers ready / Total containers. `1/1` = healthy. `0/1` = starting/crashed |
| `STATUS` | `Running` | Pod state: `Pending` (waiting), `Running` (active), `Failed` (error) |
| `RESTARTS` | `0` | How many times Kubernetes restarted it. High number = app crashing |
| `AGE` | `2d` | How long Pod has been running. `2d` = 2 days |

### kubectl get services

```bash
$ kubectl get svc -n dev

NAME                 TYPE       CLUSTER-IP    EXTERNAL-IP   PORT(S)
employee-service    ClusterIP  10.96.0.50    <none>        8000/TCP
postgres-service    ClusterIP  10.96.0.200   <none>        5432/TCP
kubernetes          ClusterIP  10.96.0.1     <none>        443/TCP
```

**Field Explanations:**

| Column | Value | Meaning |
|--------|-------|---------|
| `NAME` | `employee-service` | Service name |
| `TYPE` | `ClusterIP` | Internal only (not exposed externally) |
| `CLUSTER-IP` | `10.96.0.50` | Virtual IP inside cluster |
| `EXTERNAL-IP` | `<none>` | No external IP (ClusterIP has none) |
| `PORT(S)` | `8000/TCP` | Listening on port 8000 |

### kubectl get ingress

```bash
$ kubectl get ingress -n dev

NAME               CLASS   HOSTS                        ADDRESS         PORTS
employee-ingress   nginx   dev.shivalayammtp.club      10.0.1.101      80, 443
```

**Field Explanations:**

| Column | Value | Meaning |
|--------|-------|---------|
| `NAME` | `employee-ingress` | Ingress name |
| `CLASS` | `nginx` | Using Nginx controller |
| `HOSTS` | `dev.shivalayammtp.club` | Domain this handles |
| `ADDRESS` | `10.0.1.101` | Ingress Controller Pod IP |
| `PORTS` | `80, 443` | Listening on HTTP and HTTPS |

### kubectl describe pod

```bash
$ kubectl describe pod employee-app-5f4d8c9b2-xyz1a -n dev

Name:             employee-app-5f4d8c9b2-xyz1a
Namespace:        dev
Priority:         0
Node:             ip-10-0-1-50.ec2.internal
Status:           Running

IP:               10.0.1.100          # Pod IP inside cluster
IPs:              [10.0.1.100]

Containers:
  employee-app:
    Container ID:   docker://7f3e...
    Image:          raviteja21k/employee-service:16
    Port:           8000/TCP
    State:          Running
    Started:        2024-06-18T10:30:00Z
    
    Mounts:
      /var/run/secrets/...   (volume mount for credentials)

Conditions:
  Type              Status
  ----              ------
  Initialized       True
  Ready             True      # Pod is healthy and ready for traffic
  ContainersReady   True

Events:
  Type     Reason                    Age    Message
  ----     ------                    ----   -------
  Normal   Scheduled                 2d     Pod assigned to node
  Normal   Pulled                    2d     Container image pulled
  Normal   Created                   2d     Container created
  Normal   Started                   2d     Container started
```

### kubectl logs

```bash
$ kubectl logs employee-app-5f4d8c9b2-xyz1a -n dev

INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
2024-06-18 10:30:00 - FastAPI app started
```

**Reading logs:**
- `INFO` = Normal operation
- `ERROR` = Problem (check why)
- `WARNING` = Something needs attention
- If no recent logs = app might be stuck/crashing

### kubectl exec - Run command inside Pod

```bash
# Check if app can reach database
$ kubectl exec employee-app-5f4d8c9b2-xyz1a -n dev -- \
  python -c "import psycopg2; conn = psycopg2.connect('host=postgres-service user=hradmin')"

# Check environment variables
$ kubectl exec employee-app-5f4d8c9b2-xyz1a -n dev -- env | grep DB_

DB_HOST=postgres-service
DB_PORT=5432
DB_NAME=hrdb
DB_USER=hradmin
DB_PASSWORD=hrpassword
```

### kubectl port-forward - Local access

```bash
# Access Pod directly from laptop for debugging
$ kubectl port-forward pod/employee-app-5f4d8c9b2-xyz1a 8000:8000 -n dev

Forwarding from 127.0.0.1:8000 -> 8000
Forwarding from [::1]:8000 -> 8000

# Now: curl localhost:8000/health works on your laptop
# Bypasses Service and Ingress (direct Pod access)
```

---

# 8️⃣ AWS INTEGRATION

## Full AWS Architecture Explained

### 1. Route 53 (DNS Management)

```
What: DNS service
Why: Translates domain names to IP addresses
Setup: Create hosted zone for shivalayammtp.club

Record:
Type: A (Address)
Name: dev.shivalayammtp.club
Value: 52.XX.XX.XX (ALB IP)
TTL: 300 (cache 5 minutes)

When user types: dev.shivalayammtp.club
Route 53 returns: 52.XX.XX.XX (ALB IP)
Browser connects to ALB
```

### 2. Internet Gateway (IGW)

```
What: Connects VPC to Internet
Why: Without it, VPC is completely isolated
Setup: Attached to VPC

Traffic flow:
Internet → IGW → VPC → ALB → EKS
Response:
EKS → ALB → IGW → Internet
```

### 3. Application Load Balancer (ALB)

```
What: Distributes incoming traffic
Why: Single point of entry, handles SSL/TLS

Setup:
- Listener: Port 443 (HTTPS)
- SSL Certificate: From AWS Certificate Manager
- Target: Ingress Controller Pods

When request comes:
1. ALB receives HTTPS request
2. Terminates SSL/TLS (decrypts)
3. Adds headers: X-Forwarded-Proto: https
4. Forwards as HTTP to Ingress Controller
5. Ingress Controller routes to Service
6. Service routes to Pod
7. Pod processes
8. ALB encrypts response
9. Returns to user

Advantages:
- Handles SSL/TLS (not your app)
- Offloads encryption work
- Single HTTPS point
- SSL certificate managed by AWS
```

### 4. VPC (Virtual Private Cloud)

```
What: Your private network inside AWS
Why: Isolate resources, control access

CIDR Block: 10.0.0.0/16
Available IPs: 65,536

Subnets (subdivisions):
├─ Public Subnets (internet-facing):
│  ├─ 10.0.1.0/24 (256 IPs) - AZ us-east-1a
│  └─ 10.0.2.0/24 (256 IPs) - AZ us-east-1b
│  └─ Route Table: Direct route to IGW
│
└─ Private Subnets (internal only):
   ├─ 10.0.100.0/24 (256 IPs) - RDS Primary
   └─ 10.0.101.0/24 (256 IPs) - RDS Standby
   └─ Route Table: No direct internet access
       (can reach internet via NAT Gateway)

Why multiple AZs?
- High Availability
- If us-east-1a goes down, us-east-1b keeps running
- Automatic failover
```

### 5. EKS (Elastic Kubernetes Service)

```
What: Managed Kubernetes
Why: AWS manages control plane (Master nodes)
You manage: Worker nodes

Architecture:
┌─ EKS Cluster (Control Plane) - Managed by AWS
│  ├─ API Server
│  ├─ etcd (database)
│  ├─ Scheduler
│  └─ Controller Manager
│
└─ Worker Nodes (EC2 instances) - You manage
   ├─ Worker Node 1 (us-east-1a) - 10.0.1.50
   │  └─ Pods running here
   └─ Worker Node 2 (us-east-1b) - 10.0.2.50
      └─ Pods running here

Auto Scaling Group:
- Min: 2 nodes (minimum)
- Max: 5 nodes (maximum)
- Desired: 2 nodes (current)

If CPU usage high:
- Kubernetes adds Pod
- Needs more resources
- ASG launches new EC2 instance
- Pod scheduled on new node

If Pod dies:
- Deployment controller notices
- Restarts Pod on available node
- Service still routes to it
```

### 6. RDS (Relational Database Service)

```
What: Managed PostgreSQL
Why: AWS handles backups, patches, updates

Configuration:
Database Engine: PostgreSQL 15
Instance Class: db.t3.micro (small, cheap)
Storage: 20 GB, auto-scaling enabled

Multi-AZ Setup (High Availability):
Primary Node:
  - IP: 10.0.100.50
  - Subnet: Private (no internet access)
  - Handles all reads/writes

Standby Node (Synchronous Replication):
  - IP: 10.0.101.50
  - Subnet: Private (different AZ)
  - Exact copy of primary
  - Ready to takeover if primary fails

Endpoint: db-prod.c9akciq32.us-east-1.rds.amazonaws.com
(AWS manages DNS)

Automatic Backups:
- Daily snapshots kept 7 days
- Point-in-time recovery possible

Replication:
Primary writes data
↓
Synchronous replication to Standby
↓
Standby acknowledges
↓
Write considered complete

If Primary fails:
- Route 53 DNS updated
- Points to Standby IP
- Application reconnects automatically
- Zero downtime (RTO < 2 minutes)
```

### 7. Security Groups

```
What: Virtual firewall rules
Why: Control which traffic is allowed

SG: ALB (Load Balancer)
┌─ Inbound Rules:
│  ├─ Port 443 from 0.0.0.0/0 (HTTPS from anyone)
│  └─ Port 80 from 0.0.0.0/0 (HTTP from anyone)
└─ Outbound Rules:
   └─ All traffic to all destinations

SG: EKS Nodes
┌─ Inbound Rules:
│  ├─ Port 8000 from ALB SG (traffic from ALB)
│  └─ Port 443 from 0.0.0.0/0 (kubectl access)
└─ Outbound Rules:
   └─ All traffic (to reach external services)

SG: RDS (PostgreSQL)
┌─ Inbound Rules:
│  └─ Port 5432 from EKS Nodes SG ONLY
│     (Only Kubernetes Pods can connect)
└─ Outbound Rules:
   └─ No outbound (database doesn't initiate)
```

### 8. Complete AWS Request Flow

```
┌──────────────────────────────────────────────────────────────┐
│ STEP-BY-STEP: User in Mumbai Accessing Your App             │
└──────────────────────────────────────────────────────────────┘

STEP 1: User Action
User: Opens browser, types https://dev.shivalayammtp.club

STEP 2: DNS Resolution (Route 53)
┌─────────────────────────────────────────────────────────────┐
│ Route 53 (Mumbai ISP DNS cache)                             │
│ Question: What's the IP for dev.shivalayammtp.club?         │
│                                                             │
│ Route 53 Response: 52.XX.XX.XX (ALB IP in us-east-1)       │
│ TTL: 300 (cache for 5 minutes)                              │
└─────────────────────────────────────────────────────────────┘

STEP 3: TCP Connection (Mumbai to us-east-1)
Browser → Internet → AWS Network Edge (Virginia)
Response time: ~150-200ms (geographic latency)

STEP 4: TLS Handshake
Browser ↔ ALB (52.XX.XX.XX:443)
- Exchange certificates
- Establish encryption
- Time: ~100-150ms

STEP 5: ALB Processing (Terminates SSL)
Encrypted HTTPS request
↓
ALB decrypts using certificate
↓
Extracts HTTP request
↓
Adds headers:
  X-Forwarded-For: 123.45.67.89 (user's IP)
  X-Forwarded-Proto: https
  X-Forwarded-Port: 443
↓
Forwards to Ingress Controller

STEP 6: VPC Routing
ALB (10.0.1.1) → Ingress Controller (10.0.1.101)
Within AWS, internal network, instant

STEP 7: Ingress Controller (Nginx)
Nginx Pod (10.0.1.101:443)
Reads Ingress rule:
  Host: dev.shivalayammtp.club
  Path: /
  Backend: employee-service:8000
↓
Looks up: employee-service.dev.svc.cluster.local
↓
Gets: 10.96.0.50 (Service Virtual IP)
↓
Connects to Service

STEP 8: Service Load Balancing
Service (10.96.0.50:8000)
Endpoints:
  - 10.0.1.100:8000 (Pod 1)
  - 10.0.2.100:8000 (Pod 2)
Round robin: Send to Pod 1
↓
Routes via kube-proxy (iptables)

STEP 9: Pod Processing
Pod (10.0.1.100:8000)
FastAPI receives request
Routes to handler: @app.get("/employees")
Handler logic:
  from app.models import Employee
  from db_connection import get_session
  
  Query: SELECT * FROM employees

STEP 10: Internal Kubernetes DNS
Pod queries: postgres-service.dev.svc.cluster.local
CoreDNS response: 10.96.0.200 (postgres Service IP)

STEP 11: Service to Database Pod
Service (10.96.0.200:5432)
Routes to: postgres-pod (10.0.100.100:5432)

STEP 12: Database Query
PostgreSQL receives:
  SELECT * FROM employees WHERE active = true
↓
Executes query
↓
Returns result set to Pod

STEP 13: Response Cascade
PostgreSQL → Pod
↓
Pod formats as JSON
↓
Pod → Service (10.96.0.50)
↓
Service → Ingress Controller (10.0.1.101)
↓
Ingress → ALB (52.XX.XX.XX)
↓
ALB encrypts with HTTPS
↓
ALB → Internet Edge
↓
Internet → Mumbai User

STEP 14: Browser Rendering
User sees: List of employees on webpage

Total time: ~200-500ms (typical)
Breakdown:
- DNS: 10ms
- Network latency (Mumbai→Virginia): 150ms
- TLS handshake: 100ms
- ALB processing: 5ms
- Ingress routing: 2ms
- Service routing: 1ms
- App logic + DB query: 100-200ms
- Network return: 50ms
- Browser rendering: 50ms
```

---

# 9️⃣ NETWORK TROUBLESHOOTING

## Common Issues & How to Debug

### Issue 1: Pod Can't Reach Database

```bash
# Step 1: Check Pod logs
kubectl logs <pod-name> -n dev
Look for: "Connection refused" or timeout errors

# Step 2: Verify DNS resolution inside Pod
kubectl exec <pod-name> -n dev -- nslookup postgres-service.dev.svc.cluster.local
Expected output: 10.96.0.200

# Step 3: Check Service exists
kubectl get svc postgres-service -n dev
Expected: ClusterIP 10.96.0.200, Port 5432

# Step 4: Check Security Group rules
aws ec2 describe-security-groups --group-ids sg-xxxx
Verify: Inbound rule allows port 5432 from EKS nodes

# Step 5: Test connectivity
kubectl exec <pod-name> -n dev -- \
  psql -h postgres-service -U hradmin -d hrdb -c "SELECT 1"
Expected: psql (13.0) ... hrdb=> (1)
```

### Issue 2: External Users Can't Reach App

```bash
# Step 1: Check Ingress
kubectl get ingress -n dev
Expected: HOSTS: dev.shivalayammtp.club, ADDRESS: 10.0.1.101

# Step 2: Check DNS
nslookup dev.shivalayammtp.club
Expected: dev.shivalayammtp.club points to 52.XX.XX.XX (ALB IP)

# Step 3: Test ALB directly
curl -k https://52.XX.XX.XX -H "Host: dev.shivalayammtp.club"
Should return: 200 OK or website

# Step 4: Check Security Groups
ALB SG: Must allow 443 from 0.0.0.0/0
EKS SG: Must allow 8000 from ALB SG

# Step 5: Check Ingress Controller running
kubectl get pods -n kube-system | grep ingress
Expected: nginx-ingress-controller running

# Step 6: Check Ingress rules
kubectl describe ingress employee-ingress -n dev
Expected: Rules show correct host and backend service
```

### Issue 3: High Latency

```
Possible causes:
1. Geographic: User far from AWS region
   Solution: Use CloudFront CDN, or replicate to closer region

2. Unbalanced Pods: All traffic to one Pod
   Solution: Verify Service endpoints: kubectl get endpoints
   
3. Database connection pool exhausted
   Solution: Check connection count, increase pool size

4. Pod on wrong node: Affinity rules misconfigured
   Solution: Check node, reschedule Pod

Debug:
kubectl top nodes        # Node CPU/memory usage
kubectl top pods -n dev  # Pod CPU/memory usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime
```

---

# 🔟 NETWORK COMMANDS REFERENCE

## Essential Commands

```bash
# Check cluster connectivity
kubectl cluster-info

# List all resources
kubectl get all -n dev

# Deep dive into specific resource
kubectl describe pod <name> -n dev
kubectl describe svc <name> -n dev
kubectl describe ingress <name> -n dev

# Check network policies
kubectl get networkpolicy -n dev

# DNS testing from Pod
kubectl exec <pod> -n dev -- nslookup kubernetes.default

# Port forwarding for debugging
kubectl port-forward svc/employee-service 8000:8000 -n dev

# View container logs
kubectl logs <pod> -n dev -c <container> --tail=100 --follow

# Get Pod details including IP
kubectl get pods -o wide -n dev

# Check Service endpoints
kubectl get endpoints -n dev

# Watch Pod events
kubectl get events -n dev --sort-by='.lastTimestamp'
```

---

## SUMMARY

Your network architecture is:
- **External**: Route 53 DNS → ALB (HTTPS/SSL)
- **VPC**: Spans 2 AZs for high availability
- **Ingress**: Nginx controller routes domains to services
- **Internal**: Kubernetes ClusterIP Services for pod-to-pod communication
- **Database**: RDS Multi-AZ for data persistence
- **Security**: Isolated via Security Groups, network policies

All traffic is encrypted (HTTPS to ALB, encrypted within VPC), and failures are automatically handled (pod restart, multi-AZ failover).

