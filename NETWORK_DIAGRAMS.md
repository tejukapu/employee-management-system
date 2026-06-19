# NETWORK ARCHITECTURE - VISUAL DIAGRAMS

## SCENARIO 1: Local Development (Docker Compose)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                          YOUR LAPTOP / DEV MACHINE                      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     DOCKER BRIDGE NETWORK                         │ │
│  │                  172.18.0.0/16 (Docker Internal)                 │ │
│  │                                                                  │ │
│  │  Docker Gateway: 172.18.0.1                                     │ │
│  │  Docker DNS: 127.0.0.11:53                                      │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────┐                               │ │
│  │  │ PostgreSQL Container         │                               │ │
│  │  │                              │                               │ │
│  │  │ ID: 7a3b2c9d8f5e6a           │                               │ │
│  │  │ Name: employee-postgres      │                               │ │
│  │  │ Hostname: postgres           │                               │ │
│  │  │ Bridge IP: 172.18.0.2        │                               │ │
│  │  │ Container Port: 5432         │                               │ │
│  │  │ Host Port: 5433              │                               │ │
│  │  │                              │                               │ │
│  │  │ ┌────────────────────────┐   │                               │ │
│  │  │ │ Process: postgres      │   │                               │ │
│  │  │ │ Listening: 0.0.0.0:5432│   │                               │ │
│  │  │ │ Database: hrdb         │   │                               │ │
│  │  │ │ User: hradmin          │   │                               │ │
│  │  │ └────────────────────────┘   │                               │ │
│  │  │                              │                               │ │
│  │  │ Volume: postgres_data        │                               │ │
│  │  │ Mounted at: /var/lib/        │                               │ │
│  │  │ postgresql/data              │                               │ │
│  │  └──────────────────────────────┘                               │ │
│  │                ↑                                                 │ │
│  │                │  (Docker Network Bridge)                       │ │
│  │                │  Connected Containers                          │ │
│  │                ↓                                                 │ │
│  │  ┌──────────────────────────────┐                               │ │
│  │  │ FastAPI Container            │                               │ │
│  │  │                              │                               │ │
│  │  │ ID: 9f8e7d6c5b4a3f           │                               │ │
│  │  │ Name: employee-app           │                               │ │
│  │  │ Hostname: employee-app       │                               │ │
│  │  │ Bridge IP: 172.18.0.3        │                               │ │
│  │  │ Container Port: 8000         │                               │ │
│  │  │ Host Port: 8000              │                               │ │
│  │  │                              │                               │ │
│  │  │ ┌────────────────────────┐   │                               │ │
│  │  │ │ Process: uvicorn       │   │                               │ │
│  │  │ │ Listening: 0.0.0.0:8000│   │                               │ │
│  │  │ │ Language: Python       │   │                               │ │
│  │  │ │ Framework: FastAPI     │   │                               │ │
│  │  │ │ PID: 1                 │   │                               │ │
│  │  │ └────────────────────────┘   │                               │ │
│  │  │                              │                               │ │
│  │  │ Environment (from .env):     │                               │ │
│  │  │ DB_HOST=postgres ────────┐   │                               │ │
│  │  │ DB_PORT=5432             │   │                               │ │
│  │  │ DB_NAME=hrdb             │   │                               │ │
│  │  │ DB_USER=hradmin          │   │                               │ │
│  │  │ DB_PASSWORD=hrpassword   │   │                               │ │
│  │  │                          │   │                               │ │
│  │  │ depends_on: postgres ────┼───┼────────┐                      │ │
│  │  │ (Waits for postgres before starting) │                      │ │
│  │  │                          ↓   │       │                       │ │
│  │  │ Connection Flow:         │   │       │                       │ │
│  │  │ 1. DNS lookup: "postgres"│   │       │                       │ │
│  │  │ 2. Resolves to: 172.18.0.2   │       │                       │ │
│  │  │ 3. Connects to postgres:5432 │       │                       │ │
│  │  │ 4. Executes queries     │   │       │                       │ │
│  │  │                              │                               │ │
│  │  └──────────────────────────────┘                               │ │
│  │                                                                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     HOST MACHINE PORT MAPPING                     │ │
│  │                  (How you access from localhost)                  │ │
│  │                                                                  │ │
│  │  localhost:8000  ────PORT MAP────> employee-app:8000            │ │
│  │  (Your browser)     (iptables)     (172.18.0.3)                 │ │
│  │                                                                  │ │
│  │  localhost:5433  ────PORT MAP────> postgres:5432                │ │
│  │  (psql client)       (iptables)     (172.18.0.2)                │ │
│  │                                                                  │ │
│  │  Note: Only container ports exposed here, not internal comms    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Docker Host IP: 127.0.0.1 (localhost) or 192.168.x.x               │
│  Docker Version: 4.x (Docker Desktop)                               │
│  Network Driver: bridge (default for docker-compose)                │
│                                                                        │
└──────────────────────────────────────────────────────────────────────────┘

CONNECTION SEQUENCE IN DOCKER COMPOSE:
═══════════════════════════════════════════════════════════════════════════

1. USER ACTION
   You type: http://localhost:8000/employees

2. BROWSER REQUEST
   Browser: Sends TCP SYN to 127.0.0.1:8000
   Docker Host: Sees request on port 8000

3. DOCKER PORT MAPPING (iptables)
   Port 8000 on host → Port 8000 in employee-app container
   Redirects traffic to 172.18.0.3:8000

4. FASTAPI RECEIVES REQUEST
   Uvicorn server listening on 0.0.0.0:8000 gets request
   Routes to: @app.get("/employees")

5. APP NEEDS DATABASE DATA
   Code: cursor.execute("SELECT * FROM employees")

6. APP CONNECTS TO DATABASE
   Connection string: postgresql://hradmin:hrpassword@postgres:5432/hrdb

7. DOCKER DNS RESOLUTION (127.0.0.11:53)
   Service name: "postgres" → Container IP: 172.18.0.2
   (Docker embedded DNS resolves container names)

8. TCP CONNECT TO POSTGRES
   From: 172.18.0.3 (app)
   To:   172.18.0.2:5432 (postgres)
   Connection status: Established ✓

9. DATABASE QUERY EXECUTION
   PostgreSQL receives: SELECT * FROM employees
   Executes query in database
   Returns result rows

10. APP FORMATS RESPONSE
    FastAPI: Converts rows to JSON
    { "employees": [{"id": 1, "name": "John", ...}] }

11. SEND RESPONSE TO BROWSER
    HTTP/1.1 200 OK
    Content-Type: application/json
    [{"id": 1, "name": "John"}, ...]

12. BROWSER RENDERS
    Displays employee list on webpage

TIMING:
- DNS resolution: ~1ms (internal to Docker, very fast)
- Database query: ~20-100ms (depends on query complexity)
- App processing: ~10-50ms (FastAPI routing, JSON serialization)
- Network within containers: < 1ms (172.18.0.0/16 is local bridge)
- Total round trip: 30-150ms (typical)
```

---

## SCENARIO 2: Production Kubernetes (AWS EKS)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                 INTERNET / USERS                                   │
│                        (Geographic: Can be anywhere in world)                      │
└────────────────────────────────┬──────────────────────────────────────────────────────┘
                                 │
                                 ↓
                    ┌────────────────────────────┐
                    │   AWS Route 53 (DNS)       │
                    │   Hosted Zone:             │
                    │   shivalayammtp.club       │
                    │                            │
                    │   Record:                  │
                    │   dev.shivalayammtp.club   │
                    │   A record → 52.12.34.56   │
                    │   (ALB Public IP)          │
                    └────────────────────────────┘
                                 │
                                 ↓ (Route to ALB)
                ┌────────────────────────────────────────┐
                │  AWS Application Load Balancer (ALB)   │
                │                                        │
                │  Public IP: 52.12.34.56               │
                │  Region: us-east-1 (N. Virginia)      │
                │                                        │
                │  Listeners:                            │
                │  ├─ Port 443 (HTTPS)                  │
                │  │  Certificate: *.shivalayammtp.club  │
                │  │  From: AWS Certificate Manager     │
                │  │  Issued by: Amazon                 │
                │  │                                    │
                │  └─ Port 80 (HTTP)                    │
                │     Redirect: 301 to HTTPS            │
                │                                        │
                │  Target Group:                         │
                │  Type: IP                             │
                │  Protocol: HTTP                       │
                │  Targets: Ingress Controller Pods     │
                │                                        │
                │  Health Check:                         │
                │  Path: /health                        │
                │  Interval: 30s                        │
                │  Threshold: 2 healthy checks          │
                │                                        │
                │  Jobs:                                │
                │  1. Terminate SSL/TLS                 │
                │  2. Decrypt HTTPS                     │
                │  3. Add headers:                       │
                │     X-Forwarded-For: user's IP        │
                │     X-Forwarded-Proto: https          │
                │     X-Forwarded-Port: 443             │
                │  4. Forward as HTTP to Ingress        │
                │                                        │
                └────────────────────────────────────────┘
                                 │
                                 ↓ (Enter VPC)
        ┌────────────────────────────────────────────────────────────────┐
        │         AWS VPC (Virtual Private Cloud)                        │
        │         CIDR Block: 10.0.0.0/16 (65,536 IPs)                 │
        │         Region: us-east-1                                    │
        │                                                              │
        │  ┌──────────────────────────────────────────────────────┐   │
        │  │  Availability Zone: us-east-1a                       │   │
        │  │  Public Subnet CIDR: 10.0.1.0/24 (256 IPs)          │   │
        │  │  Route Table: Direct route to IGW                   │   │
        │  │                                                      │   │
        │  │  ┌────────────────────────────────────────────────┐ │   │
        │  │  │  EC2 Worker Node 1 (EKS Node)                │ │   │
        │  │  │                                              │ │   │
        │  │  │  Instance ID: i-0a1b2c3d4e5f                │ │   │
        │  │  │  Instance Type: t3.large                    │ │   │
        │  │  │  Private IP: 10.0.1.50                      │ │   │
        │  │  │  Public IP: 203.45.67.89 (optional)        │ │   │
        │  │  │  Security Group: eks-worker-sg              │ │   │
        │  │  │  Subnet: 10.0.1.0/24                        │ │   │
        │  │  │                                              │ │   │
        │  │  │  ┌──────────────────────────────────────┐   │ │   │
        │  │  │  │ Kubernetes Pod 1                     │   │ │   │
        │  │  │  │ (Ingress Controller - Nginx)         │   │ │   │
        │  │  │  │                                      │   │ │   │
        │  │  │  │ Pod Name: nginx-ingress-xxx          │   │ │   │
        │  │  │  │ Namespace: kube-system               │   │ │   │
        │  │  │  │ Pod IP: 10.0.1.101                   │   │ │   │
        │  │  │  │ Node Port: 443, 80 (on node)         │   │ │   │
        │  │  │  │                                      │   │ │   │
        │  │  │  │ Container: nginx                     │   │ │   │
        │  │  │  │ Image: nginx:latest                  │   │ │   │
        │  │  │  │ Port: 8443 (internal)                │   │ │   │
        │  │  │  │ CPU: 100m, Memory: 90Mi              │   │ │   │
        │  │  │  │                                      │   │ │   │
        │  │  │  │ Job: Route HTTP/HTTPS traffic        │   │ │   │
        │  │  │  │ to backend Services                  │   │ │   │
        │  │  │  └──────────────────────────────────────┘   │ │   │
        │  │  │                                              │ │   │
        │  │  │  ┌──────────────────────────────────────┐   │ │   │
        │  │  │  │ Kubernetes Pod 2                     │   │ │   │
        │  │  │  │ (Employee App)                       │   │ │   │
        │  │  │  │                                      │   │ │   │
        │  │  │  │ Pod Name: employee-app-5f4d8c9b2-1   │   │ │   │
        │  │  │  │ Pod IP: 10.0.1.100                   │   │ │   │
        │  │  │  │                                      │   │ │   │
        │  │  │  │ Container: employee-app              │   │ │   │
        │  │  │  │ Image: raviteja21k/employee-service  │   │ │   │
        │  │  │  │ Port: 8000                           │   │ │   │
        │  │  │  │ CPU: 100m→250m                       │   │ │   │
        │  │  │  │ Memory: 128Mi→256Mi                  │   │ │   │
        │  │  │  │                                      │   │ │   │
        │  │  │  │ Env Variables:                       │   │ │   │
        │  │  │  │ DB_HOST: postgres-service (DNS name)│   │ │   │
        │  │  │  │ DB_PORT: 5432                       │   │ │   │
        │  │  │  │ DB_NAME: hrdb (from ConfigMap)      │   │ │   │
        │  │  │  │ DB_USER: hradmin (from Secret)      │   │ │   │
        │  │  │  │ DB_PASS: xxxxxx (encrypted secret)  │   │ │   │
        │  │  │  │                                      │   │ │   │
        │  │  │  │ Health Checks:                       │   │ │   │
        │  │  │  │ - Liveness:  /health (20s delay)    │   │ │   │
        │  │  │  │ - Readiness: /health (10s delay)    │   │ │   │
        │  │  │  │                                      │   │ │   │
        │  │  │  │ Status: Running (1/1 Ready)          │   │ │   │
        │  │  │  └──────────────────────────────────────┘   │ │   │
        │  │  │                                              │ │   │
        │  │  └────────────────────────────────────────────────┘ │   │
        │  └──────────────────────────────────────────────────────┘   │
        │                                                              │
        │  ┌──────────────────────────────────────────────────────┐   │
        │  │  Availability Zone: us-east-1b                       │   │
        │  │  Public Subnet CIDR: 10.0.2.0/24 (256 IPs)          │   │
        │  │                                                      │   │
        │  │  ┌────────────────────────────────────────────────┐ │   │
        │  │  │  EC2 Worker Node 2 (EKS Node)                │ │   │
        │  │  │  Private IP: 10.0.2.50                       │ │   │
        │  │  │                                              │ │   │
        │  │  │  Kubernetes Pod 3 (Employee App Replica 2)  │ │   │
        │  │  │  Pod IP: 10.0.2.100                         │ │   │
        │  │  │  Status: Running (1/1 Ready)                │ │   │
        │  │  │                                              │ │   │
        │  │  │  [Similar to Pod 2 above]                   │ │   │
        │  │  └────────────────────────────────────────────────┘ │   │
        │  └──────────────────────────────────────────────────────┘   │
        │                                                              │
        │  ┌──────────────────────────────────────────────────────┐   │
        │  │  KUBERNETES SERVICES (Virtual Load Balancers)        │   │
        │  │                                                      │   │
        │  │  ┌────────────────────────────────────────────────┐ │   │
        │  │  │ Service: employee-service                     │ │   │
        │  │  │ Type: ClusterIP                               │ │   │
        │  │  │ Namespace: dev                                │ │   │
        │  │  │                                               │ │   │
        │  │  │ Cluster IP: 10.96.0.50 (Virtual IP)          │ │   │
        │  │  │ Port: 8000                                    │ │   │
        │  │  │ Target Port: 8000                             │ │   │
        │  │  │                                               │ │   │
        │  │  │ Selector: app=employee-app                    │ │   │
        │  │  │ Matches Pods with label: app=employee-app    │ │   │
        │  │  │                                               │ │   │
        │  │  │ Endpoints:                                    │ │   │
        │  │  │ ├─ 10.0.1.100:8000 (Pod 1 on Node 1)         │ │   │
        │  │  │ └─ 10.0.2.100:8000 (Pod 2 on Node 2)         │ │   │
        │  │  │                                               │ │   │
        │  │  │ Load Balancing: Round-robin across endpoints │ │   │
        │  │  │ Internal only: 10.96.0.50 not reachable from │ │   │
        │  │  │ outside cluster                              │ │   │
        │  │  └────────────────────────────────────────────────┘ │   │
        │  │                                                      │   │
        │  │  ┌────────────────────────────────────────────────┐ │   │
        │  │  │ Service: postgres-service                     │ │   │
        │  │  │ Type: ClusterIP                               │ │   │
        │  │  │ Cluster IP: 10.96.0.200                       │ │   │
        │  │  │ Port: 5432                                    │ │   │
        │  │  │ Endpoints: 10.0.100.100:5432 (DB Pod)        │ │   │
        │  │  │ (Routes to RDS database)                      │ │   │
        │  │  └────────────────────────────────────────────────┘ │   │
        │  │                                                      │   │
        │  └──────────────────────────────────────────────────────┘   │
        │                                                              │
        │  ┌──────────────────────────────────────────────────────┐   │
        │  │  KUBERNETES DNS (CoreDNS)                            │   │
        │  │  Service FQDN: employee-service.dev.svc.cluster.local│  │
        │  │  Resolves to: 10.96.0.50 (Service Cluster IP)       │   │
        │  │                                                      │   │
        │  │  Service FQDN: postgres-service.dev.svc.cluster.local│  │
        │  │  Resolves to: 10.96.0.200                           │   │
        │  │                                                      │   │
        │  │  How it works:                                       │   │
        │  │  Pod queries 10.96.0.10:53 (kube-dns)               │   │
        │  │  "employee-service.dev.svc.cluster.local?"          │   │
        │  │  Response: 10.96.0.50 ✓                             │   │
        │  └──────────────────────────────────────────────────────┘   │
        │                                                              │
        │  ┌──────────────────────────────────────────────────────┐   │
        │  │  PRIVATE SUBNETS (RDS)                              │   │
        │  │                                                      │   │
        │  │  Private Subnet 1 CIDR: 10.0.100.0/24              │   │
        │  │  Route Table: No IGW, only VPC local               │   │
        │  │                                                      │   │
        │  │  ┌────────────────────────────────────────────────┐ │   │
        │  │  │ RDS PostgreSQL - Primary (Multi-AZ)           │ │   │
        │  │  │                                                │ │   │
        │  │  │ Instance: db-prod.c9akciq32.us-east-1.rds... │ │   │
        │  │  │ Private IP: 10.0.100.50                       │ │   │
        │  │  │ Engine: PostgreSQL 15.2                       │ │   │
        │  │  │ Instance Class: db.t3.micro                   │ │   │
        │  │  │ Storage: 20 GB (gp3)                          │ │   │
        │  │  │ Port: 5432                                    │ │   │
        │  │  │                                                │ │   │
        │  │  │ Database: hrdb                                │ │   │
        │  │  │ Admin User: hradmin                           │ │   │
        │  │  │ Master Password: (encrypted in Secrets)       │ │   │
        │  │  │                                                │ │   │
        │  │  │ Security Group: rds-sg                        │ │   │
        │  │  │ Inbound: Port 5432 from eks-worker-sg ONLY    │ │   │
        │  │  │ Outbound: Deny all (DB doesn't initiate)     │ │   │
        │  │  │                                                │ │   │
        │  │  │ Backups:                                       │ │   │
        │  │  │ - Automated daily snapshots (7 days retention)│ │   │
        │  │  │ - Multi-AZ Standby replication                │ │   │
        │  │  │                                                │ │   │
        │  │  │ Monitoring:                                    │ │   │
        │  │  │ - CloudWatch metrics                          │ │   │
        │  │  │ - Enhanced monitoring                         │ │   │
        │  │  │ - CPU, Memory, Disk I/O tracked              │ │   │
        │  │  └────────────────────────────────────────────────┘ │   │
        │  │                                                      │   │
        │  │  Private Subnet 2 CIDR: 10.0.101.0/24             │   │
        │  │                                                      │   │
        │  │  ┌────────────────────────────────────────────────┐ │   │
        │  │  │ RDS PostgreSQL - Standby (Multi-AZ Replica)   │ │   │
        │  │  │                                                │ │   │
        │  │  │ Private IP: 10.0.101.50                       │ │   │
        │  │  │ Region: us-east-1 (different AZ)              │ │   │
        │  │  │ Purpose: High Availability                    │ │   │
        │  │  │ Replication: Synchronous from Primary         │ │   │
        │  │  │                                                │ │   │
        │  │  │ Automatic Failover:                           │ │   │
        │  │  │ If Primary fails:                             │ │   │
        │  │  │ - Standby promoted to Primary                │ │   │
        │  │  │ - RDS endpoint updated                        │ │   │
        │  │  │ - Applications reconnect (automatic)          │ │   │
        │  │  │ - RTO: < 2 minutes                            │ │   │
        │  │  │ - RPO: 0 seconds (no data loss)               │ │   │
        │  │  └────────────────────────────────────────────────┘ │   │
        │  └──────────────────────────────────────────────────────┘   │
        │                                                              │
        │  ┌──────────────────────────────────────────────────────┐   │
        │  │  KUBERNETES CONFIGMAPS & SECRETS                     │   │
        │  │  (Mounted to Pods as env variables)                │   │
        │  │                                                      │   │
        │  │  ConfigMap: employee-config                         │   │
        │  │  ├─ DB_HOST: postgres-service                       │   │
        │  │  ├─ DB_PORT: "5432"                                │   │
        │  │  └─ DB_NAME: hrdb                                   │   │
        │  │     (All plain text, not sensitive)                 │   │
        │  │                                                      │   │
        │  │  Secret: employee-secret (base64 encoded, etcd enc)│   │
        │  │  ├─ DB_USER: hradmin                               │   │
        │  │  └─ DB_PASSWORD: hrpassword                        │   │
        │  │     (Encrypted at rest in etcd)                    │   │
        │  │                                                      │   │
        │  │  Stored in: Kubernetes etcd database (control plane)│   │
        │  │  Mounted in: Pod /var/run/secrets/k8s              │   │
        │  └──────────────────────────────────────────────────────┘   │
        │                                                              │
        └──────────────────────────────────────────────────────────────┘

TRAFFIC FLOW IN KUBERNETES:
═══════════════════════════════════════════════════════════════════════════

REQUEST FROM BROWSER:
https://dev.shivalayammtp.club/employees
  ↓
Route 53: Resolves to ALB IP: 52.12.34.56
  ↓
ALB (52.12.34.56:443)
  - Accepts HTTPS connection
  - Verifies SSL certificate
  - Decrypts TLS
  - Adds headers (X-Forwarded-For, X-Forwarded-Proto)
  - Forwards HTTP to target
  ↓
Ingress Controller Pod (10.0.1.101:8443)
  - Nginx receives unencrypted HTTP request
  - Reads Ingress rule:
    Host: dev.shivalayammtp.club
    Path: /
    Backend: employee-service:8000
  - Looks up: employee-service.dev.svc.cluster.local
  ↓
CoreDNS Resolves:
  employee-service.dev.svc.cluster.local → 10.96.0.50
  ↓
Service Routes (Round Robin):
  10.96.0.50:8000 → [10.0.1.100, 10.0.2.100]
  (Let's say: 10.0.1.100)
  ↓
Pod Processes (10.0.1.100:8000)
  FastAPI receives /employees
  Routes to handler
  Handler needs data: SELECT * FROM employees
  ↓
Pod Connects to Database:
  Lookup: postgres-service.dev.svc.cluster.local
  ↓
CoreDNS Resolves:
  postgres-service → 10.96.0.200
  ↓
Service Routes:
  10.96.0.200:5432 → 10.0.100.100:5432 (RDS Primary)
  ↓
PostgreSQL Executes Query:
  SELECT * FROM employees
  Returns: rows
  ↓
Pod Formats Response:
  {"employees": [{"id": 1, "name": "John"}, ...]}
  ↓
Response Returns Through Same Path:
  Pod → Service → Ingress → ALB → User
  ↓
ALB Encrypts Response (HTTPS)
  ↓
User Receives & Renders
  ✓ Web page displays employee list

RESPONSE TIME BREAKDOWN:
- DNS lookup: 50-100ms (depends on geographic location)
- TLS handshake: 100-200ms
- ALB processing: 5-10ms
- Ingress routing: 2-5ms
- Service discovery: 1-2ms
- Pod processing: 50-200ms (app logic)
- Database query: 20-100ms
- Network latency (within VPC): < 1ms
- Network transmission (back): 50-100ms
  ════════════════════════════
  Total: 280-800ms (typical)
```

---

## SCENARIO 3: Multi-AZ Failover

```
NORMAL STATE (Both AZs Up):
═════════════════════════════

Route 53 DNS Points to: 52.12.34.56 (ALB)

EKS Cluster:
├─ AZ us-east-1a: Worker Node 1 (10.0.1.50) - RUNNING
│  ├─ App Pod 1 (10.0.1.100) - RUNNING
│  ├─ App Pod 3 (10.0.1.102) - RUNNING
│  └─ Ingress Pod (10.0.1.101) - RUNNING
│
└─ AZ us-east-1b: Worker Node 2 (10.0.2.50) - RUNNING
   ├─ App Pod 2 (10.0.2.100) - RUNNING
   └─ App Pod 4 (10.0.2.101) - RUNNING

RDS Database:
├─ Primary (10.0.100.50) in us-east-1a - RUNNING
└─ Standby (10.0.101.50) in us-east-1b - RUNNING (replicating)

Traffic Distribution:
User → ALB (52.12.34.56) → Ingress (balanced between 10.0.1.101, ...)
                        → Service (balanced between Pods)
                        → Database (Primary 10.0.100.50)


SCENARIO: us-east-1a ENTIRE AVAILABILITY ZONE FAILS!
════════════════════════════════════════════════════════

Time: T+0
Disaster: Network failure in us-east-1a
└─ All instances in AZ offline
   ├─ Worker Node 1 (10.0.1.50) - FAILED
   ├─ Primary RDS (10.0.100.50) - FAILED
   └─ All Pods on Node 1 - LOST

Time: T+30
EKS Control Plane Detects Failure:
├─ Health check to Worker Node 1 fails
├─ Node marked as "NotReady"
├─ Pods on this node get "Terminating" status
├─ Deployment controller detects: Only 2 of 4 replicas healthy
└─ Initiates Pod recreation on healthy nodes

Time: T+60
Kubernetes Auto-Healing:
├─ Recreates lost Pods on Worker Node 2
│  ├─ New App Pod A (10.0.2.102) - STARTING
│  └─ New App Pod B (10.0.2.103) - STARTING
│
└─ Ingress Pod recreated on:
   └─ New Ingress Pod (10.0.2.104) - STARTING

Time: T+120
RDS Database Failover:
├─ Primary (10.0.100.50) no response for 60 seconds
├─ RDS Manager initiates automatic failover
├─ Standby (10.0.101.50) promoted to Primary
├─ RDS endpoint (db-prod.c9akciq32.rds.amazonaws.com) updated
│  └─ Now points to: 10.0.101.50
│
└─ Postgres replication direction reversed:
   Old Primary ← New Primary
   (One-way, no sync on old primary)

Time: T+150
Application Reconnection:
├─ Pod with in-flight database connection
│  ├─ Connection times out after ~60s
│  └─ Connection pool refreshes
│
├─ Next query uses fresh connection:
│  ├─ Looks up: postgres-service
│  ├─ Gets: 10.96.0.200 (still same Service VIP)
│  └─ Service routes to: 10.0.101.50 (NEW Primary)
│
└─ Query succeeds ✓

Time: T+180
User Experience:
├─ t=0-120: Request may timeout (if it hit failed AZ)
├─ t=120-180: Request waits during DB failover
├─ t=180+: Requests succeed to new healthy state ✓
│
└─ Total Downtime: ~3 minutes (unplanned access blocked)
   Note: With proper health checks and ALB, could be <2 minutes

FULL STATE AFTER FAILOVER:
═════════════════════════════

Route 53 DNS: Still points to 52.12.34.56 (ALB unchanged)

EKS Cluster (All resources in us-east-1b now):
├─ AZ us-east-1a: COMPLETELY OFFLINE (no resources)
│
└─ AZ us-east-1b: ALL ACTIVE
   └─ Worker Node 2 (10.0.2.50) - RUNNING
      ├─ App Pod 2 (10.0.2.100) - RUNNING (original)
      ├─ App Pod 4 (10.0.2.101) - RUNNING (original)
      ├─ App Pod A (10.0.2.102) - RUNNING (recreated from Pod 1)
      ├─ App Pod B (10.0.2.103) - RUNNING (recreated from Pod 3)
      └─ Ingress Pod (10.0.2.104) - RUNNING (recreated)
      
         All Pod replicas: 4 (desired 4) ✓

RDS Database (Primary moved to us-east-1b):
├─ Primary (10.0.101.50) in us-east-1b - RUNNING & ACCEPTING WRITES
│  └─ Accepting all queries now
│
├─ Standby (10.0.100.50) in us-east-1a - OFFLINE
│  └─ (Will be replaced when AZ recovers)
│
└─ Failover Status: Complete, New Primary operational

Traffic Now Flows:
User → ALB (52.12.34.56)
     → Ingress Pod (10.0.2.104)
     → Service (load balances between 10.0.2.100, 10.0.2.101, 10.0.2.102, 10.0.2.103)
     → Database Service (10.96.0.200)
     → RDS Primary (10.0.101.50 in us-east-1b)


WHEN us-east-1a RECOVERS:
════════════════════════════

Time: T+3600 (1 hour later)
Network restored in us-east-1a

Kubernetes Actions:
├─ Detects Worker Node 1 rejoining cluster
├─ Rebalances Pods across both AZs:
│  ├─ Move Pod A back to us-east-1a
│  └─ Move Pod B back to us-east-1a
│
└─ New state:
   ├─ us-east-1a: 2 Pods (Pod 1 recreated as Pod A, Pod 3 recreated as Pod B)
   └─ us-east-1b: 2 Pods (Pod 2, Pod 4 stay)

RDS Actions:
├─ Provision new Standby in us-east-1a (10.0.100.50)
├─ Start replication from Primary (us-east-1b) to Standby (us-east-1a)
├─ Primary-Standby relationship re-established:
│  ├─ Primary: 10.0.101.50 (us-east-1b) - accepts writes
│  └─ Standby: 10.0.100.50 (us-east-1a) - replicates
│
└─ Ready for next failover

System Back to Fully Redundant State ✓
```

