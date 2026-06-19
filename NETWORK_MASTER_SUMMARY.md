# NETWORK ARCHITECTURE - MASTER SUMMARY & QUICK START

## 📚 FILES IN THIS GUIDE

You now have 4 comprehensive guides:

1. **NETWORK_ARCHITECTURE_GUIDE.md** (63 KB)
   - Complete explanation from users to database
   - Real AWS data flow
   - Field-by-field YAML breakdown
   - Detailed output explanations
   - AWS integration details
   - Network troubleshooting guide

2. **NETWORK_DEBUGGING_COMMANDS.md** (15 KB)
   - Practical commands for Docker Compose
   - Practical commands for Kubernetes
   - Step-by-step request tracing
   - Common errors & fixes
   - Performance monitoring
   - Security checks

3. **NETWORK_DIAGRAMS.md** (42 KB)
   - ASCII diagrams for each scenario
   - Local development setup
   - Production Kubernetes setup
   - Multi-AZ failover scenario
   - Complete traffic flow diagrams

4. **PORT_ENDPOINT_REFERENCE.md** (17 KB)
   - Port mapping reference table
   - How to access each service
   - Reading Kubernetes output
   - Endpoint examples
   - Error tracing example
   - Quick command reference

---

## 🎯 QUICK START: The 30-Second Understanding

### Local Development (Docker Compose)

```
┌─────────────────────────────────────┐
│ Your Browser                        │
│ http://localhost:8000               │
└──────────────┬──────────────────────┘
               │
        ┌──────▼──────┐
        │ Docker Port │ (5433→5432, 8000→8000)
        │ Mapping     │
        └──────┬──────┘
               │
        ┌──────▼──────────────────┐
        │ Docker Bridge Network   │
        │ 172.18.0.0/16          │
        │                        │
        ├─ employee-app: 172.18.0.3
        │  (FastAPI on 8000)
        │      ↓ connects to
        │ postgres: 172.18.0.2
        │  (PostgreSQL on 5432)
        │
        └─ (All in 1 machine)
```

**Key Point:** Container names resolve via Docker DNS (127.0.0.11:53)

### Production (Kubernetes on AWS)

```
┌──────────────────────────────┐
│ Internet Users               │
│ dev.shivalayammtp.club       │
└──────────────┬───────────────┘
               │
        ┌──────▼──────────────────────────┐
        │ AWS Route 53 (DNS)              │
        │ Resolves to ALB IP: 52.12.34.56 │
        └──────┬──────────────────────────┘
               │
        ┌──────▼──────────────────────────┐
        │ AWS ALB (Load Balancer)         │
        │ Decrypts HTTPS                  │
        │ Port: 443 (HTTPS)               │
        └──────┬──────────────────────────┘
               │
        ┌──────▼──────────────────────────┐
        │ VPC (AWS Private Network)       │
        │ 10.0.0.0/16                     │
        │                                 │
        ├─ Ingress Controller (Nginx)
        │  Ingress: dev.shivalayammtp.club → employee-service:8000
        │
        ├─ employee-service (ClusterIP 10.96.0.50)
        │  Endpoints:
        │  ├─ Pod 1: 10.0.1.100:8000
        │  └─ Pod 2: 10.0.2.100:8000
        │
        ├─ postgres-service (ClusterIP 10.96.0.200)
        │  Endpoints:
        │  └─ RDS DB: 10.0.100.100:5432
        │
        └─ Database: PostgreSQL (Multi-AZ)
           Primary: 10.0.100.50 (us-east-1a)
           Standby: 10.0.101.50 (us-east-1b)
```

**Key Point:** Service DNS (postgres-service) abstracts backend Pod IPs

---

## 🔑 KEY CONCEPTS

### 1. What is a Port?

A port is a communication endpoint. Think of it like a mail slot:

- **Container Port:** Where app listens inside container (always 8000)
- **Host Port:** Where you access it from outside (can be different)
- **Service Port:** Virtual port inside Kubernetes cluster
- **Target Port:** Actual container port Service routes to

**Example:**
```
You: curl http://localhost:8000/employees
     ↓ (Docker maps)
Container Port 8000 ← App listening here
```

### 2. What is a Service?

A virtual load balancer inside Kubernetes:

```
Service (10.96.0.50:8000)
    ├─ Selector: app=employee-app
    └─ Finds Pods with this label
       ├─ 10.0.1.100:8000 ← send traffic here
       ├─ 10.0.2.100:8000 ← or here
       └─ Load balances between all matching Pods
```

**Why?** Pod IPs change when Pod restarts. Service IP stays same.

### 3. What is an Ingress?

HTTP(S) router for external traffic:

```
Ingress Rule:
- Host: dev.shivalayammtp.club
- Path: /
- Backend: employee-service:8000

When user visits dev.shivalayammtp.club:
1. DNS → ALB IP
2. ALB → Ingress Controller (Nginx)
3. Nginx reads rule above
4. Routes to employee-service
5. Service routes to Pod
```

### 4. What is DNS Resolution?

Converting names to IP addresses:

```
DOCKER: "postgres" → 172.18.0.2 (Docker DNS 127.0.0.11:53)
KUBERNETES: "postgres-service.dev.svc.cluster.local" → 10.96.0.200 (CoreDNS 10.96.0.10:53)
AWS ROUTE53: "dev.shivalayammtp.club" → 52.12.34.56 (ALB IP)
```

### 5. What is Multi-AZ (Availability Zones)?

Running same app in multiple data centers:

```
AZ us-east-1a: Pod 1, DB Primary
AZ us-east-1b: Pod 2, DB Standby

If AZ-a fails:
- Pod 1 lost → Recreated in AZ-b
- DB Primary fails → Standby auto-promoted
- Single Pod left, still running ✓
```

---

## 📊 COMPARISON TABLE: Docker vs Kubernetes

| Feature | Docker Compose | Kubernetes |
|---------|---|---|
| **Purpose** | Local development | Production orchestration |
| **Network** | Bridge (172.18.0.0/16) | CNI plugin (10.x.x.x) |
| **Service Discovery** | Docker DNS (127.0.0.11:53) | CoreDNS (10.96.0.10:53) |
| **Ports** | Host port mapping | ClusterIP, NodePort, LoadBalancer |
| **Load Balancing** | Docker internal | kube-proxy + iptables |
| **High Availability** | No restart | Auto-restart + replication |
| **Auto-scaling** | No | Yes (Horizontal Pod Autoscaling) |
| **Multi-AZ** | No | Yes |
| **External Access** | Localhost | ALB/Ingress |
| **Database** | Container | RDS (Managed) |
| **Updates** | Manual | Rolling/Blue-Green |

---

## 🚀 STEP-BY-STEP: How a User Request Works

### LOCAL DEVELOPMENT

```
1. USER
   curl http://localhost:8000/employees

2. HOST PORT MAPPING
   Docker: localhost:8000 → Container port 8000

3. APP CONTAINER RECEIVES REQUEST
   FastAPI on 172.18.0.3 port 8000
   Routes to /employees handler

4. APP NEEDS DATA
   Handler: SELECT * FROM employees

5. DATABASE LOOKUP
   App asks: "Where is postgres?"
   Docker DNS: postgres → 172.18.0.2

6. DATABASE CONNECTION
   TCP connect: 172.18.0.3 → 172.18.0.2:5432
   PostgreSQL receives query

7. RESPONSE
   PostgreSQL → App → Browser
   User sees JSON list ✓

TOTAL TIME: 30-150ms
```

### PRODUCTION (KUBERNETES)

```
1. USER (Mumbai)
   curl https://dev.shivalayammtp.club/employees

2. DNS RESOLUTION (Route 53)
   dev.shivalayammtp.club → 52.12.34.56 (ALB IP)
   Latency: 50-100ms

3. ALB RECEIVES HTTPS REQUEST (Virginia)
   Port 443
   Decrypts TLS
   Adds headers
   Forwards to Ingress

4. INGRESS CONTROLLER ROUTES
   Reads: dev.shivalayammtp.club → employee-service:8000
   Looks up: employee-service.dev.svc.cluster.local

5. KUBERNETES DNS RESOLUTION
   CoreDNS: resolves → 10.96.0.50 (Service IP)
   Latency: 1-2ms (internal, very fast)

6. SERVICE LOAD BALANCES
   10.96.0.50:8000 → [10.0.1.100, 10.0.2.100]
   (picks one, typically round-robin)

7. POD PROCESSES REQUEST
   FastAPI on 10.0.1.100:8000
   Handler: SELECT * FROM employees

8. POD CONNECTS TO DATABASE
   App lookup: postgres-service.dev.svc.cluster.local
   CoreDNS: → 10.96.0.200 (postgres Service)
   Service routes to: 10.0.100.100:5432 (RDS)

9. DATABASE EXECUTES QUERY
   PostgreSQL returns rows
   Replication syncs to Standby

10. RESPONSE RETURNS
    PostgreSQL → Service → Pod → Ingress → ALB → Internet → User Browser
    User sees JSON list ✓

TOTAL TIME: 280-800ms
Breakdown:
- Geographic latency: 150ms
- TLS handshake: 150ms
- Ingress routing: 5ms
- Service routing: 2ms
- App logic: 100ms
- DB query: 50ms
- Network return: 100ms
```

---

## ❌ COMMON MISTAKES & HOW TO AVOID

### Mistake 1: Using Pod IP Instead of Service

```bash
# ❌ WRONG
env:
  - name: DB_HOST
    value: "10.0.100.100"  # Direct Pod IP

# Problem: If Pod restarts, gets new IP, app breaks

# ✅ CORRECT
env:
  - name: DB_HOST
    value: "postgres-service"  # Service name

# Benefit: Service finds Pod, Pod IP doesn't matter
```

### Mistake 2: Exposing RDS to Internet

```
❌ WRONG:
RDS Security Group: Allow 5432 from 0.0.0.0/0
└─ Anyone on internet can connect to your database!

✅ CORRECT:
RDS Security Group: Allow 5432 from eks-worker-sg only
└─ Only EKS Pods can connect, database protected
```

### Mistake 3: Not Using Multi-AZ

```
❌ WRONG:
RDS: Single-AZ
└─ Data center fails → app down until backup

✅ CORRECT:
RDS: Multi-AZ enabled
└─ Primary fails → Standby auto-promoted (< 2 min)
```

### Mistake 4: Hardcoding Passwords

```bash
❌ WRONG
ENV DB_PASSWORD=hrpassword  # In Dockerfile!
└─ Password visible to everyone who pulls image

✅ CORRECT
Kubernetes Secret: Contains encrypted password
Pod mounts as env var: ${DB_PASSWORD}
└─ Password encrypted at rest
```

---

## 🔍 DEBUGGING FLOW CHART

```
User Reports: "Website not working"
│
├─→ Is ALB receiving traffic?
│   ├─ YES → Continue
│   └─ NO → Check Route 53, DNS resolution
│
├─→ Is Ingress Controller running?
│   ├─ YES → Continue
│   └─ NO → kubectl get pods -n kube-system | grep ingress
│
├─→ Are employee-service Pods ready?
│   ├─ YES (1/1) → Continue
│   └─ NO (0/1) → kubectl logs <pod>
│
├─→ Can Pods reach database?
│   ├─ YES → Continue
│   └─ NO → Check postgres-service endpoints, RDS security group
│
├─→ Is RDS database running?
│   ├─ YES → Continue
│   └─ NO → Restart RDS instance, check backups
│
└─→ SUCCESS! Website should work now ✓
   If not, check app logs: kubectl logs <pod>
```

---

## 📝 YAML QUICK REFERENCE

```yaml
# DEPLOYMENT: Creates and manages Pods
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 2  # 2 copies of Pod
  selector:
    matchLabels:
      app: my-app  # Find Pods with this label
  template:
    metadata:
      labels:
        app: my-app  # Pod gets this label
    spec:
      containers:
      - name: my-app
        image: my-image:latest
        ports:
        - containerPort: 8000
        env:
        - name: DB_HOST
          value: "db-service"

---

# SERVICE: Virtual load balancer
apiVersion: v1
kind: Service
metadata:
  name: my-app-svc
spec:
  selector:
    app: my-app  # Route to Pods with this label
  ports:
  - port: 8000  # Service port
    targetPort: 8000  # Pod port
  type: ClusterIP  # Internal only

---

# INGRESS: HTTP(S) router
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app-svc
            port:
              number: 8000

---

# CONFIGMAP: Non-secret config
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-config
data:
  DB_HOST: db-service
  DB_PORT: "5432"

---

# SECRET: Encrypted config
apiVersion: v1
kind: Secret
metadata:
  name: my-secret
type: Opaque
stringData:
  DB_USER: admin
  DB_PASS: secret123
```

---

## 🎓 LEARNING PATH

If you want to understand deeper:

1. **Networking Basics**
   - What is TCP/IP, DNS, HTTP
   - How ports work
   - Read: "Computer Networking" basics

2. **Docker Networking**
   - Docker bridge networks
   - Container DNS
   - Port mapping
   - Practice: docker-compose locally

3. **Kubernetes Networking**
   - Services, Endpoints, DNS
   - Ingress controllers
   - Network policies
   - Practice: kubectl on minikube or EKS

4. **AWS**
   - Route 53, VPC, Subnets
   - ALB, Security Groups
   - RDS, Multi-AZ
   - Practice: Deploy on EKS

5. **Production**
   - Monitoring, logging
   - Security, compliance
   - Disaster recovery
   - Load testing

---

## 📞 QUICK HELP

**"Pods can't talk to each other"**
→ Check: kubectl get networkpolicy, Service endpoints

**"External users can't reach app"**
→ Check: Route 53, ALB, Security Groups, Ingress rules

**"Database connection fails"**
→ Check: RDS security group, kubernetes endpoints, logs

**"Performance is slow"**
→ Check: kubectl top nodes/pods, CloudWatch metrics, app logs

**"Pod keeps crashing"**
→ Check: kubectl logs --previous, liveness probe settings

**"Deployment stuck on 'Pending'"**
→ Check: kubectl describe pod, node resources, node labels

---

## 🎯 FINAL CHECKLIST: Is My Network Working?

```bash
✓ DNS resolves: nslookup dev.shivalayammtp.club
✓ ALB responds: curl -k https://52.12.34.56
✓ Ingress exists: kubectl get ingress -n dev
✓ Pods running: kubectl get pods -n dev
✓ Services exist: kubectl get svc -n dev
✓ Endpoints show: kubectl get endpoints -n dev
✓ App healthy: kubectl exec pod -- curl localhost:8000/health
✓ DB connected: kubectl exec pod -- psql -h postgres-service
✓ Performance acceptable: kubectl top pods, CloudWatch metrics
✓ Backups working: AWS RDS console shows recent snapshots

If ALL ✓ then your network is healthy! 🎉
```

---

**Master Summary Created!**
Use this document as your reference for everything network-related.
Start with the diagrams, drill into details with the main guide.

