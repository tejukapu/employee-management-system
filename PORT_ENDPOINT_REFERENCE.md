# PORT & ENDPOINT REFERENCE - Complete Cheat Sheet

## PART 1: PORT MAPPING REFERENCE

### Local Development (Docker Compose)

```
SERVICE          CONTAINER PORT    HOST PORT    URL/ACCESS                  PURPOSE
═════════════════════════════════════════════════════════════════════════════════════════
FastAPI App      8000              8000         http://localhost:8000       Web Application
PostgreSQL       5432              5433         localhost:5433 (psql)       Database
Jenkins          8080              8080         http://localhost:8080       CI/CD
SonarQube        9000              9000         http://localhost:9000       Code Quality
```

**Why different Host vs Container?**
- Container sees its own port (8000 inside container)
- Host maps external port (8000 on your machine)
- Database: Container 5432 → Host 5433 (avoid conflicts)

### Production (Kubernetes)

```
COMPONENT                TYPE       PORT    CLUSTER-IP      ACCESS              SCOPE
═════════════════════════════════════════════════════════════════════════════════════════════
ALB                      External   443     52.12.34.56     https://domain      Internet
ALB                       External   80      52.12.34.56     http://domain       Internet (redirect)
Ingress Controller       Internal   8443    10.0.1.101      kube-system only    Internal

employee-service        ClusterIP  8000    10.96.0.50      Cluster DNS         Internal Only
  └─ Pod Backend         -          8000    10.0.1.100      Pod IP              K8s Internal
  
postgres-service        ClusterIP  5432    10.96.0.200     Cluster DNS         Internal Only
  └─ Pod Backend         -          5432    10.0.100.100    Pod IP              K8s Internal

RDS Database            Private    5432    N/A             EKS only (no SG)     VPC Private
```

---

## PART 2: HOW TO ACCESS EACH SERVICE

### Docker Compose Access Methods

```bash
# 1. FROM BROWSER (Your laptop)
http://localhost:8000/health
http://localhost:8080/   (Jenkins)
http://localhost:9000/   (SonarQube)

# 2. FROM COMMAND LINE (Your laptop)
curl http://localhost:8000/employees
psql -h localhost -p 5433 -U hradmin -d hrdb
docker exec -it employee-app bash

# 3. FROM APP CONTAINER TO DB
docker exec employee-app \
  psql -h postgres -U hradmin -d hrdb -c "SELECT 1"
# Note: "postgres" = service name (Docker resolves)

# 4. CONTAINER INTERNAL IP
docker inspect employee-app --format='{{.NetworkSettings.IPAddress}}'
# Output: 172.18.0.3 (only accessible within docker network)

# 5. CHECK PORT MAPPINGS
docker port employee-app
# Output:
# 8000/tcp -> 0.0.0.0:8000

docker port employee-postgres
# Output:
# 5432/tcp -> 0.0.0.0:5433
```

### Kubernetes Access Methods

```bash
# 1. EXTERNAL ACCESS (Users on internet)
# Must go through ALB + Ingress
https://dev.shivalayammtp.club/employees
# Behind the scenes:
# DNS → 52.12.34.56 (ALB IP) → Ingress → Service → Pod

# 2. FROM WITHIN CLUSTER (Pod to Pod)
# Use Kubernetes DNS names
kubectl exec app-pod -n dev -- \
  curl http://employee-service.dev.svc.cluster.local:8000/health

# 3. DEBUG: PORT FORWARD TO LAPTOP
kubectl port-forward svc/employee-service 8000:8000 -n dev
# Then on laptop:
curl http://localhost:8000/employees

# 4. EXEC INTO POD (run command inside)
kubectl exec -it employee-app-xyz1a -n dev -- bash
# Inside pod, connect to service:
curl http://employee-service:8000/employees
curl http://postgres-service:5432/  # (won't work, postgres not HTTP)

# 5. GET POD INTERNAL IPs
kubectl get pods -o wide -n dev
# Output shows POD IP: 10.0.1.100, NODE: ip-10-0-1-50...
# Direct access: kubectl exec ... -- curl http://10.0.1.100:8000

# 6. GET SERVICE DETAILS
kubectl get svc -n dev
# Shows: NAME, TYPE, CLUSTER-IP, EXTERNAL-IP, PORT(S)

kubectl get endpoints -n dev
# Shows: NAME, ENDPOINTS (which Pod IPs Service routes to)

# 7. DESCRIBE FOR DETAILS
kubectl describe svc employee-service -n dev
# Shows: IP, Port mappings, Endpoints, Selector labels
```

---

## PART 3: UNDERSTANDING ENDPOINT RESPONSES

### Health Check Endpoint

```
ENDPOINT: /health
RESPONSE:
{
  "status": "healthy",
  "uptime": "2 hours 34 minutes",
  "database": "connected",
  "timestamp": "2024-06-18T10:30:00Z"
}

WHAT KUBERNETES LOOKS FOR:
- Status Code: 200 (or 2xx)
- Response Time: < 1 second
- Pod marked: Ready ✓

IF FAILS:
- Status Code: 500 or timeout
- Pod marked: NotReady ✗
- Traffic stops going to this Pod
- Kubernetes restarts Pod if liveness probe also fails
```

### List Employees Endpoint

```
ENDPOINT: GET /employees
REQUEST:
curl http://localhost:8000/employees

RESPONSE (200 OK):
[
  {
    "id": 1,
    "name": "John Doe",
    "email": "john@company.com",
    "department": "Engineering",
    "salary": 80000
  },
  {
    "id": 2,
    "name": "Jane Smith",
    "email": "jane@company.com",
    "department": "Marketing",
    "salary": 65000
  }
]

BEHIND THE SCENES:
1. Request hits FastAPI router
2. FastAPI calls handler: get_employees()
3. Handler executes: SELECT * FROM employees
4. PostgreSQL returns rows
5. FastAPI converts to JSON
6. Returns HTTP 200 + JSON body

POSSIBLE RESPONSES:
- 200 OK: Success, returns data
- 404 Not Found: Endpoint doesn't exist
- 500 Internal Server Error: App crashed/DB error
- 503 Service Unavailable: App starting up
```

### Database Connection String

```
FORMAT: postgresql://username:password@host:port/database

EXAMPLES:
1. Docker Compose (internal):
   postgresql://hradmin:hrpassword@postgres:5432/hrdb
   └─ "postgres" = container name (Docker DNS)

2. Docker Compose (external):
   postgresql://hradmin:hrpassword@localhost:5433/hrdb
   └─ localhost:5433 = port mapped on host

3. Kubernetes:
   postgresql://hradmin:hrpassword@postgres-service:5432/hrdb
   └─ "postgres-service" = K8s Service name (CoreDNS)
   └─ Resolves to: 10.96.0.200 (ClusterIP)

4. Kubernetes (cross-namespace):
   postgresql://hradmin:hrpassword@postgres-service.prod.svc.cluster.local:5432/hrdb
   └─ Full FQDN = namespace.svc.cluster.local

5. AWS RDS (external access):
   postgresql://hradmin:password@db-prod.c9akciq32.us-east-1.rds.amazonaws.com:5432/hrdb
   └─ AWS-managed endpoint

PARSING:
postgresql://user:pass@host:port/database
└─ protocol: postgresql
└─ user: hradmin
└─ pass: hrpassword (often variable: ${DB_PASSWORD})
└─ host: postgres (or postgres-service, or RDS endpoint)
└─ port: 5432
└─ database: hrdb
```

---

## PART 4: READING KUBERNETES OUTPUT

### kubectl get pods Output

```bash
$ kubectl get pods -n dev

NAME                                 READY   STATUS    RESTARTS   AGE
employee-app-5f4d8c9b2-xyz1a        1/1     Running   0          2d
employee-app-5f4d8c9b2-xyz2b        1/1     Running   0          2d
postgres-deployment-abc1234-xyz3c   1/1     Running   0          5d

FIELD BREAKDOWN:
┌─ NAME: employee-app-5f4d8c9b2-xyz1a
│  ├─ Prefix: employee-app (Deployment name)
│  ├─ Unique ID: 5f4d8c9b2 (ReplicaSet ID)
│  └─ Pod suffix: xyz1a (random string for uniqueness)
│
├─ READY: 1/1
│  ├─ Current: 1 container ready
│  └─ Total: 1 container total
│  └─ 0/1 = not ready, 1/1 = ready, 2/2 = 2 containers ready
│
├─ STATUS: Running
│  ├─ Pending: Pod scheduled but not started
│  ├─ Running: Pod actively running
│  ├─ Succeeded: Pod completed (one-time job)
│  ├─ Failed: Pod crashed
│  └─ Unknown: Kubelet not responding
│
├─ RESTARTS: 0
│  └─ Pod restarted 0 times
│  └─ High number = app crashing repeatedly
│
└─ AGE: 2d
   └─ Running for 2 days
```

### kubectl get services Output

```bash
$ kubectl get svc -n dev

NAME                 TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)
employee-service    ClusterIP  10.96.0.50      <none>        8000/TCP
postgres-service    ClusterIP  10.96.0.200     <none>        5432/TCP

FIELD BREAKDOWN:
┌─ NAME: employee-service
│  └─ Service identifier
│
├─ TYPE: ClusterIP
│  ├─ ClusterIP: Internal only (no external access)
│  ├─ NodePort: Accessible on node IP:port
│  ├─ LoadBalancer: External LB assigned (AWS: ALB/NLB)
│  └─ ExternalName: External DNS alias
│
├─ CLUSTER-IP: 10.96.0.50
│  ├─ Virtual IP inside cluster
│  ├─ Used by Kubernetes DNS
│  ├─ Not a real machine, virtual load balancer
│  └─ Only reachable within cluster
│
├─ EXTERNAL-IP: <none>
│  ├─ <none> = No external IP (ClusterIP has none)
│  ├─ If type=LoadBalancer: Shows ELB/ALB IP
│  ├─ If type=NodePort: Shows "none" (accessed via node IP)
│  └─ Useful to know: Can you reach this from outside cluster?
│
└─ PORT(S): 8000/TCP
   ├─ Service listens on port 8000
   ├─ Format: Port/Protocol
   ├─ If 8000:8000/TCP = service:8000 → target:8000
   ├─ If 8000:9000/TCP = service:8000 → target:9000
   └─ Multiple ports possible: 8000/TCP, 8443/TCP
```

### kubectl get endpoints Output

```bash
$ kubectl get endpoints -n dev

NAME                 ENDPOINTS
employee-service    10.0.1.100:8000,10.0.2.100:8000,10.0.1.102:8000
postgres-service    10.0.100.100:5432

WHAT THIS MEANS:
┌─ NAME: employee-service
│  └─ Service with this name
│
└─ ENDPOINTS: 10.0.1.100:8000,10.0.2.100:8000
   ├─ Pods currently healthy and ready
   ├─ 10.0.1.100:8000 = Pod IP 1 on port 8000 ✓
   ├─ 10.0.2.100:8000 = Pod IP 2 on port 8000 ✓
   ├─ 10.0.1.102:8000 = Pod IP 3 on port 8000 ✓
   ├─ Service load balances traffic across these 3
   ├─ If readiness probe fails: Pod IP removed from endpoints
   └─ No endpoints? Service has no healthy Pods (requests fail)

EMPTY ENDPOINTS = TROUBLE:
┌─ NAME: some-service
└─ ENDPOINTS: <none>
   ├─ No Pods found matching selector
   ├─ All Pods failing readiness probe
   ├─ Service exists but no traffic can reach it
   └─ Check: kubectl describe svc some-service (see selector)
```

### kubectl describe pod Output

```bash
$ kubectl describe pod employee-app-5f4d8c9b2-xyz1a -n dev

Name:             employee-app-5f4d8c9b2-xyz1a
Namespace:        dev
Priority:         0
Node:             ip-10-0-1-50.ec2.internal        # Which EC2 node
Status:           Running
Reason:           (reason for status)
Message:          (status details)

IP:               10.0.1.100                        # Pod IP inside cluster
IPs:              [10.0.1.100]

Containers:
  employee-app:
    Container ID:    docker://7f3e1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f
    Image:           raviteja21k/employee-service:16
    Image ID:        docker-pullable://raviteja21k/employee-service@sha256:abc123...
    Port:            8000/TCP                       # Container listening port
    Host Port:       0/TCP
    State:           Running                        # Container state
      Started:       2024-06-18T10:30:00Z           # When started
    Ready:           True                           # Readiness probe passed
    Restart Count:   0                              # How many times restarted

    Mounts:
      /var/run/secrets/kubernetes.io/...            # Secret volume

Conditions:
  Type              Status
  ----              ------
  Initialized       True                            # Pod initialized
  Ready             True         ← KEY: Pod ready for traffic
  ContainersReady   True                            # Containers healthy
  PodScheduled      True                            # Pod scheduled on node

Events:                                             # Pod history
  Type     Reason                    Age    Message
  ----     ------                    ----   -------
  Normal   Scheduled                 2d     Pod assigned to ip-10-0-1-50
  Normal   Pulled                    2d     Container image pulled successfully
  Normal   Created                   2d     Container created
  Normal   Started                   2d     Container started
```

### kubectl logs Output

```bash
$ kubectl logs employee-app-5f4d8c9b2-xyz1a -n dev --tail=20

INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete
2024-06-18 10:30:00 - FastAPI app initialized
2024-06-18 10:30:15 - GET /health - 200 OK
2024-06-18 10:30:30 - GET /employees - 200 OK - 45ms
2024-06-18 10:30:45 - POST /employees - 201 Created - 120ms
2024-06-18 10:31:00 - ERROR: Database connection timeout
2024-06-18 10:31:00 - Retrying connection... attempt 1/3
2024-06-18 10:31:05 - Database connection re-established

HOW TO READ:
┌─ 2024-06-18 10:30:15 - GET /health - 200 OK
│  ├─ Timestamp: When this happened
│  ├─ Event: GET /health endpoint called
│  ├─ Status: 200 OK (succeeded)
│  └─ Meaning: Health probe passed ✓
│
├─ 2024-06-18 10:30:30 - GET /employees - 200 OK - 45ms
│  ├─ Event: User called /employees
│  ├─ Status: 200 OK (success)
│  └─ Time: 45ms (response time)
│
└─ 2024-06-18 10:31:00 - ERROR: Database connection timeout
   ├─ Severity: ERROR (problem!)
   ├─ Issue: Connection to database timed out
   └─ Action: Check database Pod, network, credentials

USEFUL FLAGS:
kubectl logs pod-name -n dev --tail=50          # Last 50 lines
kubectl logs pod-name -n dev -f                 # Follow (live update)
kubectl logs pod-name -n dev --timestamps=true  # Add timestamps
kubectl logs pod-name -n dev -c container       # Specific container
kubectl logs pod-name -n dev --previous         # Previous crashed instance
```

---

## PART 5: TRACING AN ERROR

### Example: "Connection refused" Error

```bash
# STEP 1: User reports: "Can't access website"
# They get: Connection refused or timeout

# STEP 2: Check if Pod is running
$ kubectl get pods -n dev
NAME                                READY   STATUS
employee-app-5f4d8c9b2-xyz1a       0/1     CrashLoopBackOff  ← NOT READY

# STEP 3: Check Pod logs
$ kubectl logs employee-app-5f4d8c9b2-xyz1a -n dev

ERROR: Cannot connect to postgres://postgres-service:5432
psycopg2.OperationalError: could not connect to server: No such file or directory
	Is the server running on host "postgres-service" (10.96.0.200) and accepting TCP/IP connections on port 5432?

# STEP 4: Check postgres Service and endpoints
$ kubectl get svc postgres-service -n dev
NAME                 TYPE       CLUSTER-IP      PORT(S)
postgres-service    ClusterIP  10.96.0.200     5432/TCP

$ kubectl get endpoints postgres-service -n dev
NAME                 ENDPOINTS
postgres-service    <none>            ← PROBLEM! No endpoints (no healthy Pods)

# STEP 5: Check postgres Pods
$ kubectl get pods -n dev | grep postgres
postgres-deployment-abc1234-xyz3c   0/1     CrashLoopBackOff

# STEP 6: Check postgres Pod logs
$ kubectl logs postgres-deployment-abc1234-xyz3c -n dev

ERROR: initdb: could not access directory "/var/lib/postgresql/data": Permission denied
FATAL: database files are incompatible with server

# STEP 7: FIX
Postgres Pod crashed due to permission error on volume
Fix: Check PVC, re-create Pod, verify storage mount

$ kubectl delete pod postgres-deployment-abc1234-xyz3c -n dev
# Deployment will recreate it

# STEP 8: VERIFY
$ kubectl get endpoints postgres-service -n dev
NAME                 ENDPOINTS
postgres-service    10.0.100.100:5432  ← NOW HAS ENDPOINT!

$ kubectl get pods -n dev | grep postgres
postgres-deployment-abc1234-xyz3d   1/1     Running      ← NOW RUNNING!

$ kubectl logs employee-app-5f4d8c9b2-xyz1a -n dev
INFO: Connected to database  ← NOW CONNECTED!

# STEP 9: TEST
$ curl http://localhost:8000/employees
[{"id": 1, "name": "John"}, ...]  ← NOW WORKS! ✓
```

---

## PART 6: QUICK COMMAND REFERENCE

```bash
# LISTING & VIEWING
kubectl get pods -n dev                          # List all Pods
kubectl get svc -n dev                           # List all Services
kubectl get endpoints -n dev                     # Show Service endpoints
kubectl get all -n dev                           # Everything at once

# DETAILED INFO
kubectl describe pod <name> -n dev               # Pod details
kubectl describe svc <name> -n dev               # Service details
kubectl describe ingress <name> -n dev           # Ingress details

# LOGS & DEBUGGING
kubectl logs <pod> -n dev                        # View logs
kubectl logs <pod> -n dev -f                     # Follow (live)
kubectl exec <pod> -n dev -- bash               # Shell into Pod
kubectl exec <pod> -n dev -- curl http://svc:8000  # Run command in Pod

# NETWORK
kubectl port-forward svc/<service> 8000:8000 -n dev  # Local access
kubectl get networkpolicy -n dev                 # Check policies

# RESOURCE INFO
kubectl top nodes                                # Node CPU/Memory
kubectl top pods -n dev                          # Pod CPU/Memory

# EVENTS
kubectl get events -n dev --sort-by='.lastTimestamp'  # Recent events

# CONFIG
kubectl get configmap -n dev                     # List ConfigMaps
kubectl describe configmap <name> -n dev         # View ConfigMap content
kubectl get secrets -n dev                       # List Secrets

# ADMIN
kubectl rollout restart deployment/<dep> -n dev  # Restart Deployment
kubectl delete pod <pod> -n dev                  # Delete Pod (recreate it)
```

