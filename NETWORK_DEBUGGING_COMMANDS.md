# QUICK REFERENCE: Network Debugging & Commands

## 1. VERIFY YOUR SETUP IS RUNNING

### Check Docker Compose (Local Dev)
```bash
# Start services
docker-compose -f C:\devops-project\employee-service\docker-compose-app.yml up -d

# Check running containers
docker ps

# Output should show:
# CONTAINER ID   IMAGE                              PORTS
# 7a3b2c9d...   postgres:15                        0.0.0.0:5433->5432/tcp
# 9f8e7d6c...   employee-service-employee-app      0.0.0.0:8000->8000/tcp

# Test connectivity
curl http://localhost:8000/health
curl -H "host=localhost" http://localhost:8000/

# View logs
docker logs 7a3b2c9d...  # postgres container
docker logs 9f8e7d6c...  # app container

# Stop everything
docker-compose -f C:\devops-project\employee-service\docker-compose-app.yml down
```

### Check Kubernetes (Production)
```bash
# Connect to cluster
aws eks update-kubeconfig --name your-cluster-name --region us-east-1
kubectl config current-context

# Verify connectivity
kubectl cluster-info
kubectl get nodes

# Output shows:
# NAME                               STATUS   ROLES    AGE
# ip-10-0-1-50.ec2.internal         Ready    <none>   5d
# ip-10-0-2-50.ec2.internal         Ready    <none>   5d
```

---

## 2. UNDERSTANDING WHAT'S RUNNING

### Docker Compose Network Check

```bash
# See all networks
docker network ls

# See which containers on which network
docker network inspect employee-service_default

# Output shows:
# "Name": "employee-service_default"
# "Driver": "bridge"
# "Containers": {
#   "7a3b2c9d...": {
#     "Name": "employee-postgres",
#     "IPv4Address": "172.18.0.2/16"
#   },
#   "9f8e7d6c...": {
#     "Name": "employee-app",
#     "IPv4Address": "172.18.0.3/16"
#   }
# }

# Test DNS within container
docker exec employee-app nslookup postgres
# Returns: Address: 172.18.0.2 ✓

# Test database connection from app
docker exec employee-app \
  python -c "import psycopg2; psycopg2.connect(host='postgres', user='hradmin', password='hrpassword')"
# No error = success ✓
```

### Kubernetes Resource Check

```bash
# 1. Check all resources in dev namespace
kubectl get all -n dev

# Output:
# NAME                                    READY   STATUS    RESTARTS   AGE
# pod/employee-app-5f4d8c9b2-xyz1a       1/1     Running   0          2d
# pod/employee-app-5f4d8c9b2-xyz2b       1/1     Running   0          2d
# pod/postgres-deployment-abc1234-xyz3c  1/1     Running   0          5d
#
# NAME                     TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)
# service/employee-service ClusterIP   10.96.0.50       <none>        8000/TCP
# service/postgres-service ClusterIP   10.96.0.200      <none>        5432/TCP
#
# NAME                               DESIRED   CURRENT   READY   AGE
# deployment.apps/employee-app       2         2         2       2d
# deployment.apps/postgres           1         1         1       5d

# 2. Check Ingress
kubectl get ingress -n dev
# Output:
# NAME               CLASS   HOSTS                        ADDRESS         PORTS
# employee-ingress   nginx   dev.shivalayammtp.club      10.0.1.101      80, 443

# 3. Check Service Endpoints
kubectl get endpoints -n dev
# Output:
# NAME                 ENDPOINTS
# employee-service    10.0.1.100:8000,10.0.2.100:8000
# postgres-service    10.0.100.100:5432
# (Shows which Pods each Service routes to)

# 4. Check Config & Secrets
kubectl get configmap -n dev
kubectl get secrets -n dev
```

---

## 3. TRACING A REQUEST (Docker Compose)

### What Happens When You Access: http://localhost:8000/employees

```bash
# Step 1: Browser sends request
curl -v http://localhost:8000/employees

# Expected output:
# > GET /employees HTTP/1.1
# > Host: localhost:8000
# < HTTP/1.1 200 OK
# < Content-Type: application/json
# [{"id": 1, "name": "John", ...}, ...]

# Step 2: View app container logs
docker logs employee-app --follow

# Expected logs:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     GET /employees
# INFO:     200 OK

# Step 3: Check app can reach database
docker exec employee-app \
  psql -h postgres -U hradmin -d hrdb -c "SELECT * FROM employees;"

# Expected: List of employees

# Step 4: Test database directly
docker exec employee-postgres \
  psql -U hradmin -d hrdb -c "SELECT * FROM employees;"

# Expected: Same employee list
```

### What Happens Inside the Request

```
┌─ Request arrives at localhost:8000
│
├─ Docker maps port 8000:8000
│  Your port 8000 → Container port 8000
│
├─ Request enters app container (172.18.0.3)
│  FastAPI receives /employees
│
├─ FastAPI needs data, calls database
│  Query: "SELECT * FROM employees"
│
├─ App connects to postgres service
│  Host: "postgres" (docker-compose service name)
│  Docker embedded DNS: 127.0.0.11:53
│  Resolves: postgres → 172.18.0.2
│
├─ Connection to PostgreSQL container
│  User: hradmin
│  Password: hrpassword
│  Database: hrdb
│
├─ PostgreSQL executes query
│  Returns: employee rows
│
├─ FastAPI formats response as JSON
│  {"employees": [...]}
│
└─ Response sent back to you
   http://localhost:8000/employees → [{"id": 1, ...}]
```

---

## 4. TRACING A REQUEST (Kubernetes)

### What Happens When User Visits: dev.shivalayammtp.club

```bash
# Step 1: Trace from external
ping dev.shivalayammtp.club
# Should return: 52.XX.XX.XX (ALB IP)

nslookup dev.shivalayammtp.club
# Should show: 52.XX.XX.XX

# Step 2: Check Route 53 configuration
aws route53 list-resource-record-sets --hosted-zone-id Z1234567890ABC
# Look for:
# Type: A
# Name: dev.shivalayammtp.club
# Value: 52.XX.XX.XX

# Step 3: Check ALB is routing correctly
aws elbv2 describe-load-balancers --load-balancer-arns arn:aws:elasticloadbalancing:...
# Verify: ALB exists, has target group pointing to Ingress nodes

# Step 4: Check Ingress Controller
kubectl get pods -n kube-system | grep ingress
# Output:
# aws-alb-ingress-controller-xyz     Running
# nginx-ingress-controller-abc       Running

# Step 5: Check Ingress rules
kubectl describe ingress employee-ingress -n dev
# Output should show:
# Host: dev.shivalayammtp.club
# Backend: employee-service:8000

# Step 6: Check Service endpoints
kubectl get endpoints employee-service -n dev
# Output:
# NAME                 ENDPOINTS
# employee-service    10.0.1.100:8000,10.0.2.100:8000
# (Should show multiple Pod IPs)

# Step 7: Direct Pod access (debugging)
kubectl port-forward svc/employee-service 8000:8000 -n dev
# Then on your laptop:
curl http://localhost:8000/employees
# Should work! Shows app is functioning

# Step 8: Check Pod logs
kubectl logs employee-app-5f4d8c9b2-xyz1a -n dev
# Look for:
# - GET /employees
# - Database query execution
# - Response sent

# Step 9: Verify app reached database
kubectl logs employee-app-5f4d8c9b2-xyz1a -n dev | grep postgres
# Should show successful connection

# Step 10: Check database service
kubectl describe svc postgres-service -n dev
# Endpoints: 10.0.100.100:5432
```

### Kubernetes Request Path

```
User in Mumbai
    ↓
    │ DNS: dev.shivalayammtp.club?
    ↓
Route 53 → 52.XX.XX.XX (ALB IP)
    ↓
    │ HTTPS request to 52.XX.XX.XX:443
    ↓
ALB (us-east-1)
    │ Decrypt HTTPS
    │ Add headers: X-Forwarded-For, X-Forwarded-Proto
    ├─ Check target group health
    └─ Forward to Ingress Controller
        ↓
        │ Ingress Controller (10.0.1.101:443)
        │ Read rule: dev.shivalayammtp.club → employee-service
        ├─ DNS: employee-service.dev.svc.cluster.local?
        └─ Gets: 10.96.0.50 (Service ClusterIP)
            ↓
        Service (10.96.0.50:8000)
            │ Load balance to endpoints
            ├─ 10.0.1.100:8000 (Pod 1) ← send to this one
            └─ 10.0.2.100:8000 (Pod 2)
                ↓
            Pod (10.0.1.100:8000)
                │ FastAPI processes /employees
                ├─ Need data: postgres-service.dev.svc.cluster.local?
                ├─ Gets: 10.96.0.200 (postgres Service)
                ├─ Connects to 10.0.100.100:5432 (DB Pod)
                ├─ Query: SELECT * FROM employees
                └─ Response: [{"id": 1, "name": "John"}, ...]
                    ↓
            Response bubbles back through same path
                    ↓
            Ingress Controller
                    ↓
            ALB (encrypt to HTTPS)
                    ↓
            User gets JSON in browser ✓
```

---

## 5. CHECKING CONNECTIVITY

### Docker Compose: Check Container-to-Container

```bash
# From app container, can it reach postgres?
docker exec employee-app ping postgres
# Expected: Reachable (if you have ping installed)

# Better: Try psql
docker exec employee-app \
  psql -h postgres -U hradmin -d hrdb -c "SELECT 1"
# Expected: 1 (or connection refused = problem)

# Check environment variables inside app
docker exec employee-app env | grep DB_
# Expected:
# DB_HOST=postgres
# DB_PORT=5432
# DB_NAME=hrdb
# DB_USER=hradmin
# DB_PASSWORD=hrpassword
```

### Kubernetes: Check Pod-to-Pod

```bash
# From app Pod, can it reach postgres Service?
kubectl exec employee-app-xyz1a -n dev -- \
  nslookup postgres-service.dev.svc.cluster.local
# Expected:
# Address: 10.96.0.200

# Can it connect to postgres?
kubectl exec employee-app-xyz1a -n dev -- \
  psql -h postgres-service -U hradmin -d hrdb -c "SELECT 1"
# Expected: 1

# Check environment variables inside Pod
kubectl exec employee-app-xyz1a -n dev -- env | grep DB_
# Expected:
# DB_HOST=postgres-service
# DB_PORT=5432
# DB_NAME=hrdb
# DB_USER=hradmin
# DB_PASSWORD=hrpassword
```

### Kubernetes: Check External Connectivity

```bash
# Can external users reach ALB?
curl -k -v https://dev.shivalayammtp.club/health
# Expected:
# HTTP/1.1 200 OK
# {"status": "healthy"}

# Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...
# Expected:
# TargetHealth: {
#   State: "healthy"
#   Reason: "Target.ResponseCodeMatcher"
# }

# Check Security Groups
aws ec2 describe-security-groups --group-ids sg-12345678
# Verify:
# Inbound: 443 from 0.0.0.0/0 (ALB)
# Inbound: 8000 from ALB-SG (EKS)
# Outbound: All or specific ports to RDS-SG
```

---

## 6. COMMON ERRORS & FIXES

### "Connection refused"
```bash
# Docker Compose
docker logs employee-app
# Check: Is postgres container running?
docker ps | grep postgres

# Kubernetes
kubectl logs employee-app-xyz1a
# Check: Is postgres Pod running?
kubectl get pods -n dev | grep postgres

# Fix: Restart containers/Pods
docker-compose down && docker-compose up -d
kubectl delete pod postgres-deployment-xyz -n dev
# (Deployment will recreate it)
```

### "No route to host" / "Network unreachable"
```bash
# Docker Compose: Check network
docker network ls
docker network inspect employee-service_default

# Kubernetes: Check network policies
kubectl get networkpolicy -n dev
# If too restrictive, update or remove
```

### "DNS resolution failed"
```bash
# Docker Compose
docker exec employee-app nslookup postgres
# If fails: Docker DNS issue

# Kubernetes
kubectl exec employee-app-xyz1a -- nslookup postgres-service.dev.svc.cluster.local
# Check CoreDNS:
kubectl get pods -n kube-system | grep coredns

# Restart CoreDNS if needed:
kubectl rollout restart deployment coredns -n kube-system
```

### "Port already in use"
```bash
# Docker Compose
# Port 8000 already used on host?
netstat -an | grep 8000  # Windows: Get-NetTCPConnection -LocalPort 8000

# Kill existing process or change port in compose:
ports:
  - "8001:8000"  # Use 8001 instead
```

### "Certificate verification failed"
```bash
# HTTPS issues - Kubernetes
# Ingress cert not installed
kubectl get certificate -n dev
kubectl describe cert employee-ingress-cert -n dev

# Force renewal:
kubectl delete cert employee-ingress-cert -n dev
# Cert-manager will recreate
```

---

## 7. PERFORMANCE MONITORING

### Docker Compose

```bash
# See resource usage
docker stats

# Output:
# CONTAINER ID  NAME              CPU %   MEM USAGE
# 7a3b2c9d...  employee-postgres  0.5%    150MiB
# 9f8e7d6c...  employee-app       1.2%    75MiB

# Check response time
time curl http://localhost:8000/employees
# Shows: real 0.234s (total time)

# Load test
docker run --rm -it \
  -e TARGET_HOST=http://employee-app:8000 \
  grafana/k6:latest run - <<'EOF'
import http from 'k6/http';
import { check } from 'k6';
export let options = {
  vus: 10,
  duration: '30s',
};
export default function () {
  let res = http.get('http://employee-app:8000/employees');
  check(res, { 'status was 200': (r) => r.status == 200 });
}
EOF
```

### Kubernetes

```bash
# View resource usage
kubectl top nodes
# Output:
# NAME                             CPU(cores)   MEMORY(Mi)
# ip-10-0-1-50.ec2.internal       250m         600Mi
# ip-10-0-2-50.ec2.internal       180m         520Mi

kubectl top pods -n dev
# Output:
# NAME                              CPU(cores)   MEMORY(Mi)
# employee-app-5f4d8c9b2-xyz1a     50m          45Mi
# employee-app-5f4d8c9b2-xyz2b     45m          42Mi
# postgres-deployment-xyz3c        80m          150Mi

# Check Pod events/warnings
kubectl get events -n dev --sort-by='.lastTimestamp'

# Stream logs with timestamps
kubectl logs employee-app-xyz1a -n dev -f --timestamps=true

# Check Kubernetes resource quotas
kubectl describe quota -n dev
```

---

## 8. SECURITY CHECKS

### Network Policies

```bash
# Check if network policies exist
kubectl get networkpolicy -n dev

# Typical restrictive policy:
# Allow: Pod to Pod (same namespace)
# Allow: Pod to external (DNS, HTTPS)
# Deny: Everything else

# View a policy
kubectl describe networkpolicy deny-all -n dev

# Test connectivity through policy
kubectl exec employee-app-xyz1a -- \
  nslookup google.com
# Should fail if policy denies external DNS
```

### Security Groups (AWS)

```bash
# List all security groups
aws ec2 describe-security-groups

# Check specific rules
aws ec2 describe-security-groups \
  --group-ids sg-12345678 \
  --query 'SecurityGroups[0].IpPermissions'

# Output shows:
# [
#   {
#     "IpProtocol": "tcp",
#     "FromPort": 443,
#     "ToPort": 443,
#     "IpRanges": [{"CidrIp": "0.0.0.0/0"}]  # HTTPS from anywhere
#   },
#   {
#     "IpProtocol": "tcp",
#     "FromPort": 8000,
#     "ToPort": 8000,
#     "UserIdGroupPairs": [{"GroupId": "sg-alb-id"}]  # From ALB only
#   }
# ]
```

---

## QUICK SUMMARY

| Task | Docker Compose | Kubernetes |
|------|-----------------|-----------|
| Check running | `docker ps` | `kubectl get pods -n dev` |
| View logs | `docker logs container` | `kubectl logs pod -n dev` |
| Test connectivity | `docker exec container curl service:port` | `kubectl exec pod -- curl service` |
| Port forward | N/A (direct access) | `kubectl port-forward svc/service 8000:8000 -n dev` |
| Restart | `docker restart container` | `kubectl delete pod pod-name -n dev` |
| Check network | `docker network ls` | `kubectl get svc,endpoints -n dev` |
| View config | `docker inspect container` | `kubectl describe pod/svc/ingress -n dev` |
| Monitor | `docker stats` | `kubectl top nodes/pods` |

