# 🚨 KUBERNETES PRODUCTION TROUBLESHOOTING
## Real Scenarios • Actual Commands • Real Outputs • Step-by-Step Fixes

---

## 🎯 QUICK DECISION TREE

```
🚨 PROBLEM REPORTED
        ↓
Is it K8s issue?
├─ YES → Use this guide (K8s Troubleshooting)
│        ├─ Pod not running?
│        ├─ Service failing?
│        ├─ Network issue?
│        └─ Resource issue?
│
├─ MAYBE → Check K8s first, then Linux
│         └─ Use ISOLATION FLOWCHART
│
└─ NO → Jump to Linux troubleshooting guide
```

---

## SCENARIO 1: APP POD STUCK IN "PENDING"

### ⚠️ ISSUE
User reports: "Website not responding"

### 🔍 WHAT TO CHECK

**Step 1: Check Pod Status**
```bash
kubectl get pods -n dev
```

**EXPECTED OUTPUT - GOOD:**
```
NAME                              READY   STATUS    RESTARTS   AGE
employee-app-5f4d8c9b2-xyz1a     1/1     Running   0          2d
employee-app-5f4d8c9b2-xyz2b     1/1     Running   0          1d
```

**ACTUAL OUTPUT - BAD (Current Issue):**
```
NAME                              READY   STATUS     RESTARTS   AGE
employee-app-5f4d8c9b2-xyz1a     0/1     Pending    0          15m
employee-app-5f4d8c9b2-xyz2b     0/1     Pending    0          15m
```

**DIAGNOSIS:** `Pending` = Pod cannot be scheduled on any node

### 🛠️ ROOT CAUSE INVESTIGATION

**Step 2: Describe Pod - See WHY it's Pending**
```bash
kubectl describe pod employee-app-5f4d8c9b2-xyz1a -n dev
```

**OUTPUT - Typical Problem #1: No Resource Available**
```
Name:             employee-app-5f4d8c9b2-xyz1a
Namespace:        dev
Status:           Pending

Conditions:
  Type           Status  Reason
  PodScheduled   False   Unschedulable

Events:
  Type     Reason            Age   Message
  ----     ------            ---   -------
  Warning  FailedScheduling  15m   0/3 nodes available: 
           3 Insufficient memory. CPU 250m too high for nodes.
  Warning  FailedScheduling  14m   0/3 nodes available: 
           3 Insufficient memory.
```

**PROBLEM IDENTIFIED:** 
- ❌ Not enough CPU/Memory on nodes
- ❌ Pod needs: CPU 250m, Memory 256Mi
- ❌ All 3 nodes don't have this available

**Step 3: Check Node Resources**
```bash
kubectl top nodes
```

**OUTPUT:**
```
NAME                             CPU(cores)   MEMORY(Mi)
ip-10-0-1-50.ec2.internal       800m         1200Mi
ip-10-0-2-50.ec2.internal       750m         1100Mi
ip-10-0-3-50.ec2.internal       850m         1300Mi
```

**OUTPUT EXPLANATION:**
- Node 1: Using 800m CPU (80% of 1000m available) → LOW SPACE
- Node 2: Using 750m CPU (75% available)
- Node 3: Using 850m CPU (85% available)
- ❌ NO NODE HAS 250m FREE CPU

**Step 4: Check Node Allocatable Resources**
```bash
kubectl describe nodes ip-10-0-1-50.ec2.internal | grep -A 5 "Allocated resources"
```

**OUTPUT:**
```
Allocated resources:
  (Total limits may be over 100 percent, i.e., overcommitted.)
  Resource           Requests      Limits
  --------           --------      ------
  cpu                750m          1500m
  memory             900Mi         1800Mi
```

**ISSUE CONFIRMED:**
- Node capacity: 1000m CPU, 1500Mi Memory
- Allocated: 750m CPU, 900Mi Memory
- Available: 250m CPU, 600Mi Memory
- Pod needs: 250m CPU (request), 256Mi Memory (available)
- BUT: Multiple Pods competing for same space

### ✅ SOLUTION #1: Add More Nodes (Best for Production)

**Check Auto Scaling Group:**
```bash
aws ec2 describe-launch-templates --launch-template-names eks-nodes
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names eks-nodes-asg
```

**OUTPUT:**
```
AutoScalingGroups:
  - AutoScalingGroupName: eks-nodes-asg
    MinSize: 2
    MaxSize: 5
    DesiredCapacity: 3           ← Currently 3 nodes
    Instances: 3 instances active
```

**INCREASE CAPACITY:**
```bash
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name eks-nodes-asg \
  --desired-capacity 5
```

**VERIFY SCALING:**
```bash
watch kubectl get nodes
```

**OUTPUT AFTER 5 MINUTES:**
```
Every 2.0s: kubectl get nodes

NAME                             STATUS   ROLES    AGE     VERSION
ip-10-0-1-50.ec2.internal       Ready    <none>   5d      v1.27.0
ip-10-0-2-50.ec2.internal       Ready    <none>   4d      v1.27.0
ip-10-0-3-50.ec2.internal       Ready    <none>   2d      v1.27.0
ip-10-0-1-51.ec2.internal       Ready    <none>   2m      v1.27.0    ← NEW!
ip-10-0-2-51.ec2.internal       Ready    <none>   1m      v1.27.0    ← NEW!
```

**CHECK PODS NOW RUNNING:**
```bash
kubectl get pods -n dev
```

**OUTPUT - FIXED:**
```
NAME                              READY   STATUS    RESTARTS   AGE
employee-app-5f4d8c9b2-xyz1a     1/1     Running   0          18m
employee-app-5f4d8c9b2-xyz2b     1/1     Running   0          18m
```

### ✅ SOLUTION #2: Reduce Pod Resource Requests (Quick Fix)

**Edit Deployment:**
```bash
kubectl edit deployment employee-app -n dev
```

**CHANGE FROM:**
```yaml
resources:
  requests:
    cpu: "250m"
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

**CHANGE TO:**
```yaml
resources:
  requests:
    cpu: "100m"        # ← Reduced
    memory: "128Mi"    # ← Reduced
  limits:
    cpu: "250m"        # ← Reduced
    memory: "256Mi"    # ← Reduced
```

**SAVE & VERIFY:**
```bash
kubectl get pods -n dev --watch
```

**OUTPUT:**
```
NAME                              READY   STATUS              RESTARTS   AGE
employee-app-5f4d8c9b2-xyz1a     0/1     ContainerCreating   0          0s
employee-app-5f4d8c9b2-xyz1a     1/1     Running             0          3s
employee-app-5f4d8c9b2-xyz2b     0/1     ContainerCreating   0          1s
employee-app-5f4d8c9b2-xyz2b     1/1     Running             0          4s
```

### ✅ VERIFICATION - POD RUNNING

```bash
curl http://localhost:8000/health
```

**OUTPUT:**
```json
{"status": "healthy", "uptime": "0 hours"}
```

---

## SCENARIO 2: POD RUNNING BUT SERVICE NOT RESPONDING

### ⚠️ ISSUE
User reports: "Page loads but shows error"
Status: `kubectl get pods` shows `1/1 Running`
But: Requests fail

### 🔍 WHAT TO CHECK

**Step 1: Check Pod Status (Already OK)**
```bash
kubectl get pods -n dev -o wide
```

**OUTPUT:**
```
NAME                              READY   STATUS    RESTARTS   AGE   IP
employee-app-5f4d8c9b2-xyz1a     1/1     Running   0          2d    10.0.1.100
employee-app-5f4d8c9b2-xyz2b     1/1     Running   0          1d    10.0.2.100
```

**NEXT:** Check if Pod itself is healthy

**Step 2: Test App Directly (Inside Pod)**
```bash
kubectl exec employee-app-5f4d8c9b2-xyz1a -n dev -- \
  curl http://localhost:8000/health
```

**OUTPUT - GOOD:**
```json
{"status": "healthy"}
```

**OUTPUT - BAD (App Crashed):**
```
error: command terminated with exit code 1
```

**If Bad:** Pod is running but app crashed
- Check logs: `kubectl logs pod-name -n dev`

**Step 3: Check Service Endpoints**
```bash
kubectl get endpoints employee-service -n dev
```

**OUTPUT - GOOD:**
```
NAME                 ENDPOINTS
employee-service    10.0.1.100:8000,10.0.2.100:8000
```

**OUTPUT - BAD (No Endpoints):**
```
NAME                 ENDPOINTS
employee-service    <none>
```

**PROBLEM:** Service has no Pods to route to!

**Step 4: Check Service Selector**
```bash
kubectl describe svc employee-service -n dev
```

**OUTPUT:**
```
Name:              employee-service
Namespace:         dev
Labels:            <none>
Annotations:       <none>
Selector:          app=employee-app      ← Looking for this label
Type:              ClusterIP
IP:                10.96.0.50
Port:              <unset> 8000/TCP
TargetPort:        8000/TCP
Endpoints:         <none>               ← NO PODS MATCH!
Session Affinity:  None
```

**Step 5: Check Pod Labels**
```bash
kubectl get pods -n dev --show-labels
```

**OUTPUT - BAD:**
```
NAME                              STATUS    LABELS
employee-app-5f4d8c9b2-xyz1a     Running   tier=backend          ← WRONG LABEL!
employee-app-5f4d8c9b2-xyz2b     Running   tier=backend
```

**PROBLEM IDENTIFIED:** 
- Service looking for: `app=employee-app`
- Pods have: `tier=backend`
- ❌ Labels don't match!

### ✅ FIX: Add Correct Label to Pods

**Add Label:**
```bash
kubectl label pods -n dev \
  employee-app-5f4d8c9b2-xyz1a \
  employee-app-5f4d8c9b2-xyz2b \
  app=employee-app
```

**VERIFY LABELS:**
```bash
kubectl get pods -n dev --show-labels
```

**OUTPUT - FIXED:**
```
NAME                              STATUS    LABELS
employee-app-5f4d8c9b2-xyz1a     Running   app=employee-app,tier=backend
employee-app-5f4d8c9b2-xyz2b     Running   app=employee-app,tier=backend
```

**CHECK ENDPOINTS NOW:**
```bash
kubectl get endpoints employee-service -n dev
```

**OUTPUT - FIXED:**
```
NAME                 ENDPOINTS
employee-service    10.0.1.100:8000,10.0.2.100:8000
```

**TEST SERVICE:**
```bash
kubectl exec -it employee-app-5f4d8c9b2-xyz1a -n dev -- \
  curl http://employee-service:8000/health
```

**OUTPUT:**
```json
{"status": "healthy"}
```

---

## SCENARIO 3: POD CRASHING (CrashLoopBackOff)

### ⚠️ ISSUE
```bash
kubectl get pods -n dev
```

**OUTPUT:**
```
NAME                              READY   STATUS             RESTARTS   AGE
employee-app-5f4d8c9b2-xyz1a     0/1     CrashLoopBackOff   5          3m
```

**PROBLEM:** Pod starts, crashes, restarts, crashes again (5 times!)

### 🔍 WHAT TO CHECK

**Step 1: Check Recent Logs**
```bash
kubectl logs employee-app-5f4d8c9b2-xyz1a -n dev --tail=50
```

**OUTPUT - Common Issue #1: DB Connection Failed**
```
2024-06-18 10:30:00 - Starting FastAPI app
2024-06-18 10:30:01 - Connecting to database: postgres-service:5432
2024-06-18 10:30:05 - ERROR: could not connect to server: Connection refused
2024-06-18 10:30:05 - Is the server running on host "postgres-service" 
                      (10.96.0.200) and accepting TCP/IP connections on port 5432?
2024-06-18 10:30:05 - FATAL: Database connection failed
2024-06-18 10:30:05 - Application shutting down
```

**PROBLEM:** Cannot connect to database service

**Step 2: Check Database Service**
```bash
kubectl get svc postgres-service -n dev
```

**OUTPUT:**
```
NAME              TYPE       CLUSTER-IP      PORT(S)
postgres-service  ClusterIP  10.96.0.200     5432/TCP
```

**Step 3: Check Database Pod**
```bash
kubectl get pods -n dev | grep postgres
```

**OUTPUT - PROBLEM:**
```
postgres-deployment-abc1234-xyz3c   0/1     CrashLoopBackOff   3          2m
```

**Database Pod is also crashing!**

**Step 4: Check DB Pod Logs**
```bash
kubectl logs postgres-deployment-abc1234-xyz3c -n dev
```

**OUTPUT:**
```
ERROR: initdb: could not access directory "/var/lib/postgresql/data": 
       Permission denied

DETAIL: 
  Initializing database failed, directory not writable by postgres user

FATAL: database files are incompatible with server
```

**ROOT CAUSE:** Volume permission issue

**Step 5: Check PVC (Persistent Volume Claim)**
```bash
kubectl get pvc -n dev
```

**OUTPUT:**
```
NAME                     STATUS   VOLUME
postgres-data-pvc        Bound    pv-postgres-001
```

**Check PV Details:**
```bash
kubectl describe pv pv-postgres-001
```

**OUTPUT:**
```
Name:         pv-postgres-001
Capacity:     10Gi
Access Modes: [ReadWriteOnce]
Reclaim Policy: Delete
Status:       Bound
Claim:        dev/postgres-data-pvc
Message:      
Source:
  awsElasticBlockStore:
    volumeID:   vol-0a1b2c3d4e5f
    fsType:     ext4
    partition:  0
```

### ✅ FIX: Delete and Recreate PVC

**Delete Pod (forces PVC remount):**
```bash
kubectl delete pod postgres-deployment-abc1234-xyz3c -n dev
```

**Deployment will recreate it:**
```bash
watch kubectl get pods -n dev | grep postgres
```

**OUTPUT - Recovering:**
```
postgres-deployment-abc1234-xyz3d   0/1     ContainerCreating   0          3s
postgres-deployment-abc1234-xyz3d   1/1     Running             0          8s
```

**Check Logs Now:**
```bash
kubectl logs postgres-deployment-abc1234-xyz3d -n dev
```

**OUTPUT - FIXED:**
```
2024-06-18 10:32:00 - PostgreSQL 15 initialized successfully
2024-06-18 10:32:05 - Ready to accept connections
```

**Check App Pod Now:**
```bash
kubectl get pods -n dev
```

**OUTPUT - FIXED:**
```
NAME                              READY   STATUS    RESTARTS   AGE
employee-app-5f4d8c9b2-xyz1a     1/1     Running   0          2m
postgres-deployment-abc1234-xyz3d 1/1     Running   0          1m
```

---

## SCENARIO 4: HIGH CPU/MEMORY - PODS GETTING KILLED

### ⚠️ ISSUE
```bash
kubectl get pods -n dev
```

**OUTPUT:**
```
NAME                              READY   STATUS      RESTARTS   AGE
employee-app-5f4d8c9b2-xyz1a     0/1     OOMKilled   3          5m
employee-app-5f4d8c9b2-xyz2b     0/1     OOMKilled   2          3m
```

**PROBLEM:** OOMKilled = Out Of Memory Killed

### 🔍 WHAT TO CHECK

**Step 1: Check Pod Resource Usage**
```bash
kubectl top pods -n dev
```

**OUTPUT:**
```
NAME                              CPU(cores)   MEMORY(Mi)
employee-app-5f4d8c9b2-xyz1a     250m         340Mi        ← EXCEEDS 256Mi LIMIT!
employee-app-5f4d8c9b2-xyz2b     280m         380Mi        ← EXCEEDS 256Mi LIMIT!
postgres-deployment-abc1234-xyz3d 100m        210Mi
```

**PROBLEM IDENTIFIED:** Pods using more memory than limit!
- Pod memory limit: 256Mi
- App using: 340Mi, 380Mi
- ❌ OVER LIMIT → KILLED

**Step 2: Check Deployment Limits**
```bash
kubectl describe deployment employee-app -n dev | grep -A 10 "Limits"
```

**OUTPUT:**
```
resources:
  limits:
    cpu: 250m
    memory: 256Mi       ← TOO LOW!
  requests:
    cpu: 100m
    memory: 128Mi
```

### ✅ FIX: Increase Memory Limit

**Option 1: Edit Deployment Directly**
```bash
kubectl set resources deployment employee-app -n dev \
  --limits=cpu=500m,memory=512Mi \
  --requests=cpu=200m,memory=256Mi
```

**OUTPUT:**
```
deployment.apps/employee-app resource limits updated
```

**Option 2: Edit YAML**
```bash
kubectl edit deployment employee-app -n dev
```

**CHANGE:**
```yaml
resources:
  limits:
    cpu: "250m"    →  "500m"
    memory: "256Mi" →  "512Mi"
  requests:
    cpu: "100m"     →  "200m"
    memory: "128Mi"  →  "256Mi"
```

**VERIFY:**
```bash
kubectl rollout status deployment employee-app -n dev
```

**OUTPUT:**
```
deployment "employee-app" successfully rolled out
```

**CHECK PODS:**
```bash
kubectl top pods -n dev
```

**OUTPUT - FIXED:**
```
NAME                              CPU(cores)   MEMORY(Mi)
employee-app-5f4d8c9b2-xyz1a     250m         340Mi        ✓ Under new limit (512Mi)
employee-app-5f4d8c9b2-xyz2b     280m         360Mi        ✓ Under new limit (512Mi)
```

---

## SCENARIO 5: STUCK DEPLOYMENT - PODS NOT UPDATING

### ⚠️ ISSUE
```bash
kubectl get deployment -n dev
```

**OUTPUT:**
```
NAME            READY   UP-TO-DATE   AVAILABLE   AGE
employee-app    2/3     1            2           10m
```

**PROBLEM:** 3 replicas desired, only 1 up-to-date, 2 on old version

### 🔍 WHAT TO CHECK

**Step 1: Check Rollout Status**
```bash
kubectl rollout status deployment employee-app -n dev
```

**OUTPUT:**
```
Waiting for deployment "employee-app" to progress. Timeout waiting for deployment 
"employee-app" to be available on Worker Node 1:
  Replica on node "ip-10-0-1-50" failed to progress.
  New Pod failed to reach Ready state.
```

**Step 2: Describe Deployment Events**
```bash
kubectl describe deployment employee-app -n dev | tail -30
```

**OUTPUT:**
```
Events:
  Type     Reason            Age    From                   Message
  ----     ------            ----   ----                   -------
  Normal   ScalingUp         10m    deployment-controller  Scaled up replica set
  Warning  FailedCreate      9m     replicaset-controller  Error creating Pod
           image pull error: manifest not found. 
           Repository raviteja21k/employee-service@sha256:xxxxx not found: 
           name unknown: The image with digest 'sha256:xxxxx' does not exist
  Warning  FailedCreate      8m     replicaset-controller  Error creating Pod
```

**ROOT CAUSE:** Docker image not found!
- Image: `raviteja21k/employee-service:16`
- ❌ Image not on Docker Hub

### ✅ FIX: Use Valid Image

**Step 1: Check Available Images**
```bash
docker images | grep employee
```

**Local OUTPUT:**
```
raviteja21k/employee-service   15     abc123      1 GB    2 days ago
raviteja21k/employee-service   14     def456      1 GB    3 days ago
```

**Tag 16 doesn't exist! Use tag 15:**

**Step 2: Update Deployment Image**
```bash
kubectl set image deployment employee-app \
  employee-app=raviteja21k/employee-service:15 \
  -n dev
```

**OUTPUT:**
```
deployment.apps/employee-app image updated
```

**Step 3: Monitor Rollout**
```bash
kubectl rollout status deployment employee-app -n dev
```

**OUTPUT - Progressing:**
```
Waiting for rollout to finish: 2 of 3 updated replicas are available...
Waiting for rollout to finish: 2 of 3 updated replicas are available...
deployment "employee-app" successfully rolled out
```

**VERIFY:**
```bash
kubectl get deployment -n dev
```

**OUTPUT - FIXED:**
```
NAME            READY   UP-TO-DATE   AVAILABLE   AGE
employee-app    3/3     3            3           12m
```

---

## SCENARIO 6: INGRESS NOT ROUTING TRAFFIC

### ⚠️ ISSUE
User reports: "Can't access dev.shivalayammtp.club"

### 🔍 WHAT TO CHECK

**Step 1: Check Ingress**
```bash
kubectl get ingress -n dev
```

**OUTPUT:**
```
NAME               CLASS   HOSTS                        ADDRESS         PORTS
employee-ingress   nginx   dev.shivalayammtp.club      <pending>       80, 443
```

**PROBLEM:** ADDRESS is `<pending>` (no ALB assigned)

**Step 2: Describe Ingress**
```bash
kubectl describe ingress employee-ingress -n dev
```

**OUTPUT:**
```
Name:             employee-ingress
Namespace:        dev
Ingress Class:    nginx
Default backend:  <default>
Rules:
  Host                        Path  Backends
  ----                        ----  --------
  dev.shivalayammtp.club     /     employee-service:8000
Status:
  Load Balancer Ingress:

Events:
  Type     Reason  Age   From                      Message
  ----     ------  ----  ----                      -------
  Warning  Sync    5m    nginx-ingress-controller  
           error on ingress sync, retrying. Error: 
           certificate not ready: waiting for acme challenge propagation
```

**ROOT CAUSE:** SSL certificate not issued

**Step 3: Check Certificate**
```bash
kubectl get certificate -n dev
```

**OUTPUT:**
```
NAME                    READY   SECRET              AGE
employee-ingress-cert   False   employee-ingress    5m
```

**Certificate not ready!**

**Step 4: Describe Certificate**
```bash
kubectl describe certificate employee-ingress-cert -n dev
```

**OUTPUT:**
```
Name:         employee-ingress-cert
Namespace:    dev
API Version:  cert-manager.io/v1

Status:
  Conditions:
    Last Transition Time:  2024-06-18T10:30:00Z
    Message:               Waiting for HTTP-01 challenge propagation
    Reason:                Waiting
    Status:                False
    Type:                  Ready

Events:
  Type     Reason                 Age   From          Message
  ----     ------                 ----  ----          -------
  Normal   Issuing                5m    cert-manager  Issuing certificate as Secret does not exist
  Normal   Generated              5m    cert-manager  Internally generated new private key and CSR
  Normal   OrderCreated           5m    cert-manager  Created Order resource "employee-ingress-..." 
  Warning  IssuerNotReady         4m    cert-manager  Certificate issuer does not exist
```

**PROBLEM:** No issuer configured

### ✅ FIX: Create Certificate Issuer

**Create Issuer (Let's Encrypt):**
```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@shivalayammtp.club
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

**UPDATE INGRESS ANNOTATION:**
```bash
kubectl annotate ingress employee-ingress -n dev \
  cert-manager.io/cluster-issuer=letsencrypt-prod \
  --overwrite
```

**MONITOR CERTIFICATE:**
```bash
watch kubectl get certificate -n dev
```

**OUTPUT - After 2-3 minutes:**
```
NAME                    READY   SECRET              AGE
employee-ingress-cert   True    employee-ingress    7m
```

**CHECK INGRESS NOW:**
```bash
kubectl get ingress -n dev
```

**OUTPUT - FIXED:**
```
NAME               CLASS   HOSTS                        ADDRESS         PORTS
employee-ingress   nginx   dev.shivalayammtp.club      10.0.1.101      80, 443
```

**TEST INGRESS:**
```bash
curl https://dev.shivalayammtp.club/employees
```

**OUTPUT:**
```json
[{"id": 1, "name": "John"}, ...]
```

---

## 🛠️ RAPID DIAGNOSTIC COMMANDS

### Get Everything
```bash
kubectl get all -n dev
```

### Pod Debugging
```bash
# Get detailed info
kubectl describe pod <name> -n dev

# View logs
kubectl logs <name> -n dev -f --tail=50

# Previous crashed instance logs
kubectl logs <name> -n dev --previous

# Run command inside
kubectl exec <name> -n dev -- <command>

# Get shell
kubectl exec -it <name> -n dev -- bash
```

### Service Debugging
```bash
# List services
kubectl get svc -n dev

# Get endpoints
kubectl get endpoints -n dev

# Test connectivity
kubectl exec <pod> -n dev -- curl http://service:port

# Port forward for local testing
kubectl port-forward svc/service-name 8000:8000 -n dev
```

### Resource Debugging
```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods -n dev

# Check node memory/cpu
kubectl describe node <node-name>

# PVC status
kubectl get pvc -n dev
```

### Events
```bash
# Recent events
kubectl get events -n dev --sort-by='.lastTimestamp'

# Watch events live
kubectl get events -n dev --watch
```

---

## 📊 COMMON ISSUES REFERENCE TABLE

| Status | Issue | Check Command | Fix |
|--------|-------|---|---|
| Pending | No resources | `kubectl describe pod` | Scale nodes/reduce requests |
| CrashLoopBackOff | App crashes | `kubectl logs --previous` | Fix app, check DB connection |
| ImagePullBackOff | Image not found | `kubectl describe pod` | Use correct image tag |
| ErrImagePull | Network issue | `kubectl logs` | Check image registry access |
| OOMKilled | Out of memory | `kubectl top pods` | Increase memory limits |
| Not Ready | Health check fails | `kubectl logs` | Check /health endpoint |
| Terminating | Pod stuck | `kubectl delete pod --grace-period=0 --force` | Force delete |

---

## ✅ VERIFICATION CHECKLIST

- [ ] All Pods are Running (1/1 Ready)
- [ ] All Services have Endpoints
- [ ] All PVCs are Bound
- [ ] Ingress has ADDRESS assigned
- [ ] Certificate is Ready
- [ ] No Recent Events (warnings)
- [ ] Resource usage under limits
- [ ] External traffic reaches app

If ALL ✓ → **K8s is HEALTHY, move to Linux checks**

