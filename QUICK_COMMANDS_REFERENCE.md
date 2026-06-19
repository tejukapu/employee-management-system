# ⚡ PRODUCTION TROUBLESHOOTING - QUICK COMMANDS
## Copy-Paste Ready • Real Outputs • Rapid Diagnosis

---

## 🚨 CRITICAL FIRST RESPONSE (3 minutes)

Run this when problem reported:

```bash
# 1. K8s Status
kubectl get all -n dev 2>&1

# 2. Problem Pods
kubectl get pods -n dev | grep -v Running

# 3. Events (recent issues)
kubectl get events -n dev --sort-by='.lastTimestamp' | tail -10

# 4. Pod Details (if any failing)
for pod in $(kubectl get pods -n dev -o name); do
  kubectl describe $pod -n dev 2>&1 | grep -A 5 "Events:"
done
```

---

## KUBERNETES COMMANDS

### List & Check Status

```bash
# All Pods status
kubectl get pods -n dev
# Output: Shows READY, STATUS, RESTARTS, AGE

# Services
kubectl get svc -n dev
# Output: Shows TYPE, CLUSTER-IP, PORT(S)

# Service Endpoints
kubectl get endpoints -n dev
# Output: Shows ENDPOINTS (Pod IPs service routes to)

# Everything
kubectl get all -n dev
# Output: All resources at once

# Pod resources
kubectl top pods -n dev
# Output: Shows CPU and MEMORY per Pod
```

### Detailed Debugging

```bash
# Full pod details
kubectl describe pod <pod-name> -n dev
# Output: Status, Conditions, Events, Resource limits

# Pod logs (last 50 lines)
kubectl logs <pod-name> -n dev --tail=50
# Output: Application output

# Follow logs (live)
kubectl logs <pod-name> -n dev -f
# Output: Streaming logs

# Previous crashed instance logs
kubectl logs <pod-name> -n dev --previous
# Output: Logs from last crash

# Run command inside pod
kubectl exec <pod-name> -n dev -- <command>
# Example: kubectl exec app-pod -n dev -- curl localhost:8000/health

# Get interactive shell
kubectl exec -it <pod-name> -n dev -- bash

# Port forward to localhost
kubectl port-forward svc/<svc-name> 8000:8000 -n dev
# Then: curl http://localhost:8000/employees

# Node status
kubectl get nodes
# Output: NODE name, STATUS (Ready?), ROLES, AGE, VERSION

# Node resources
kubectl top nodes
# Output: CPU and MEMORY per node

# Deployment status
kubectl get deployment -n dev
# Output: READY, UP-TO-DATE, AVAILABLE

# Rollout status
kubectl rollout status deployment/<dep-name> -n dev
# Output: Deployment progress
```

### Quick Fixes

```bash
# Restart pod (forces recreate)
kubectl delete pod <pod-name> -n dev

# Restart entire deployment
kubectl rollout restart deployment/<dep-name> -n dev

# Change image
kubectl set image deployment/<dep> <container>=<image>:<tag> -n dev

# Change resource limits
kubectl set resources deployment/<dep> \
  --limits=cpu=500m,memory=512Mi \
  --requests=cpu=200m,memory=256Mi -n dev

# Scale deployment
kubectl scale deployment/<dep> --replicas=5 -n dev

# Edit deployment
kubectl edit deployment/<dep> -n dev
# (Opens editor, modify YAML, save to apply)
```

### Diagnostic One-Liners

```bash
# Are all pods running?
kubectl get pods -n dev --field-selector=status.phase!=Running | tail -n +2

# Do all services have endpoints?
for svc in $(kubectl get svc -n dev -o name); do
  echo "Service: $svc"
  kubectl get endpoints $svc -n dev
done

# Check pod to service connectivity
kubectl exec <app-pod> -n dev -- \
  curl -v http://postgres-service:5432 2>&1 | head -10

# Find problematic pod
kubectl get pods -n dev -o wide | grep -E "Pending|CrashLoop"

# Check recent errors
kubectl get events -n dev --sort-by='.lastTimestamp' | grep -i error
```

---

## LINUX COMMANDS (SSH to Node)

### System Status

```bash
# Overall system
top -b -n 1
# Output: CPU%, Memory %, Processes, Load average

# Memory detailed
free -h
# Output: Total, Used, Free, Available

# Disk usage
df -h
# Output: Filesystem usage per mount

# Which process using most CPU
ps aux --sort=-%cpu | head -5
# Output: %CPU highest first

# Which process using most memory
ps aux --sort=-%mem | head -5
# Output: %MEM highest first

# Connections count
netstat -an | grep ESTABLISHED | wc -l
# Output: Number

# Listen ports
netstat -tln | grep LISTEN
# Output: Listening services and ports
```

### Detailed Analysis

```bash
# Process details
ps aux | grep <process-name>
# Output: Full process line

# Full command line of PID
cat /proc/<PID>/cmdline | tr '\0' ' '; echo
# Output: Complete command with args

# Process threads (for hung processes)
top -p <PID> -H
# Output: Threads of process, CPU% each

# CPU per thread (for infinite loops)
ps -eLf | grep <PID>
# Output: All threads of PID

# Files open by process
lsof -p <PID> | wc -l
# Output: Number of file handles

# Network connections by process
netstat -anp 2>/dev/null | grep <PID>
# Output: Connections this process has

# I/O statistics
iostat -x 1 5
# Output: 5 iterations of disk I/O

# Active disk I/O processes
iotop -b -n 1
# Output: Top processes by disk I/O
```

### Error Detection

```bash
# Kernel errors
dmesg | tail -20
# Output: Recent kernel messages

# OOM killer events
dmesg | grep -i "oom"
# Output: Out of memory events

# Disk errors
dmesg | grep -i "error\|fail\|corrupt"
# Output: Any I/O or filesystem errors

# Filesystem check needed?
dmesg | grep -i "fsck\|needs_recovery"
# Output: If filesystem damaged

# Network errors
dmesg | grep -i "network\|eth\|down"
# Output: Network issues

# System journal errors
journalctl -xn | head -50
# Output: Systemd recent events
```

### Process Management

```bash
# Kill process by PID
kill -9 <PID>

# Kill all processes matching name
killall -9 <process-name>

# Force kill hung process
kill -SIGKILL <PID>

# Graceful stop
kill -SIGTERM <PID>

# Get process group
ps -o pgid= -p <PID>

# Kill entire process group
kill -9 -$(ps -o pgid= -p <PID>)
```

---

## DATABASE COMMANDS

### Connection Status

```bash
# Check PostgreSQL running
ps aux | grep postgres | grep -v grep
# Output: postgres process line

# Connections to DB
psql -U postgres -d postgres -c \
  "SELECT count(*) FROM pg_stat_activity;"
# Output: Number of connections

# Who's connected
psql -U postgres -d postgres -c \
  "SELECT usename, count(*) FROM pg_stat_activity GROUP BY usename;"
# Output: Connections per user

# Long running queries
psql -U postgres -d postgres -c \
  "SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
   FROM pg_stat_activity 
   WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"
# Output: Queries running > 5 min

# Kill connection
psql -U postgres -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
   WHERE usename = 'app_user' AND query_start < now() - interval '1 hour';"
# Output: Killed old connections
```

### Performance Check

```bash
# Table sizes
psql -U postgres -d hrdb -c \
  "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
   FROM pg_tables WHERE schemaname != 'pg_catalog' 
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
# Output: Biggest tables first

# Missing indexes
psql -U postgres -d hrdb -c \
  "SELECT schemaname, tablename, attname 
   FROM pg_stat_user_tables t 
   JOIN pg_attribute a ON a.attrelid = t.relid 
   WHERE seq_scan > idx_scan AND seq_tup_read > 100000;"
# Output: Columns needing indexes

# Cache hit ratio
psql -U postgres -d hrdb -c \
  "SELECT sum(heap_blks_read) as heap_read, 
          sum(heap_blks_hit) as heap_hit, 
          sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio 
   FROM pg_statio_user_tables;"
# Output: Cache efficiency (should be > 0.99)
```

---

## NETWORKING COMMANDS

```bash
# DNS resolution
nslookup postgres-service.dev.svc.cluster.local 10.96.0.10
# Output: Should resolve to service IP

# Network interface status
ip addr show
# Output: All interfaces and IPs

# Routes
route -n
# Output: Network routing table

# Which interface has route to server
ip route get 10.96.0.50
# Output: Interface and route details

# Open ports
netstat -tln
# Output: Listening ports

# Process on port
netstat -tlnp 2>/dev/null | grep :8000
# Output: Process listening on port 8000

# Connection to service
nc -zv postgres-service.dev 5432
# Output: Connection successful or timed out

# Packet trace
tcpdump -i eth0 -n port 5432 -A
# Output: Live packet capture

# Service reachability
curl -v http://postgres-service.dev:5432
# Output: Connection attempt details
```

---

## COMBINED DIAGNOSTICS

### "Pod is failing" - Full diagnosis

```bash
# 1. Pod status
kubectl describe pod <pod-name> -n dev

# 2. Recent logs
kubectl logs <pod-name> -n dev --tail=100

# 3. Previous crash logs
kubectl logs <pod-name> -n dev --previous

# 4. Check health
kubectl exec <pod-name> -n dev -- curl localhost:8000/health

# 5. Check dependencies
kubectl exec <pod-name> -n dev -- \
  psql -h postgres-service -U hradmin -d hrdb -c "SELECT 1"

# If all failing → SSH to node and run:
top -b -n 1 | head -5
free -h
df -h /
dmesg | tail -20
```

### "System slow" - Performance diagnosis

```bash
# K8s side
kubectl top nodes
kubectl top pods -n dev

# Linux side (SSH to slow node)
top -b -n 1              # Overall CPU/Memory
ps aux --sort=-%cpu | head -5   # CPU hogs
ps aux --sort=-%mem | head -5   # Memory hogs
iostat -x 1 5            # Disk I/O
free -h                  # Memory details

# Database side (if app is DB-heavy)
psql -U postgres -d postgres -c \
  "SELECT pid, query_start, state, query FROM pg_stat_activity 
   ORDER BY query_start;"
```

### "Database not accessible" - Connectivity diagnosis

```bash
# From app pod
kubectl exec <app-pod> -n dev -- \
  nslookup postgres-service.dev.svc.cluster.local

kubectl exec <app-pod> -n dev -- \
  nc -zv postgres-service 5432

kubectl exec <app-pod> -n dev -- \
  psql -h postgres-service -U hradmin -d hrdb -c "SELECT version();"

# From node
ssh ubuntu@<node-ip>
nc -zv postgres-service.dev 5432
psql -h postgres-service -U hradmin -d hrdb -c "SELECT version();"

# Check service
kubectl get svc postgres-service -n dev
kubectl get endpoints postgres-service -n dev
```

---

## MONITORING - LIVE WATCH

```bash
# Watch pods updating
watch kubectl get pods -n dev

# Watch resources in real-time
watch kubectl top pods -n dev

# Watch events
watch kubectl get events -n dev --sort-by='.lastTimestamp'

# Watch specific pod
watch kubectl describe pod <pod-name> -n dev

# System monitoring (on Linux)
watch top -b -n 1

# Connections growing?
watch -n 5 'psql -U postgres -d postgres -c \
  "SELECT count(*) FROM pg_stat_activity"'
```

---

## QUICK REFERENCE MATRIX

| Problem | K8s Command | Linux Command |
|---------|---|---|
| Pod won't start | `kubectl logs --previous` | SSH node: `top`, `dmesg` |
| Service not responding | `kubectl get endpoints` | SSH node: `netstat -tln` |
| High CPU | `kubectl top pods` | `top -b -n 1` |
| High Memory | `kubectl top pods` | `free -h` |
| Disk Full | `kubectl get pv` | `df -h` |
| DB Connection Error | `kubectl exec ... curl db` | SSH node: `psql` test |
| Slow Queries | `kubectl logs` | `psql pg_stat_activity` |
| OOM Killed | `kubectl logs` | `dmesg \| grep oom` |

---

## COPY-PASTE COMMAND SETS

### Set 1: Full Status Report
```bash
echo "=== PODS ===" && kubectl get pods -n dev
echo "=== SERVICES ===" && kubectl get svc -n dev
echo "=== ENDPOINTS ===" && kubectl get endpoints -n dev
echo "=== EVENTS ===" && kubectl get events -n dev --sort-by='.lastTimestamp' | tail -5
echo "=== RESOURCES ===" && kubectl top pods -n dev
```

### Set 2: Pod Deep Dive
```bash
POD="employee-app-5f4d8c9b2-xyz1a"
echo "=== POD DESCRIBE ===" && kubectl describe pod $POD -n dev
echo "=== POD LOGS ===" && kubectl logs $POD -n dev --tail=30
echo "=== POD HEALTH ===" && kubectl exec $POD -n dev -- curl localhost:8000/health
```

### Set 3: Linux Diagnostics
```bash
echo "=== CPU ===" && top -b -n 1 | head -3
echo "=== MEMORY ===" && free -h
echo "=== DISK ===" && df -h /
echo "=== LOAD ===" && uptime
echo "=== ERRORS ===" && dmesg | tail -5
```

### Set 4: Database Check
```bash
POD="postgres-deployment-abc1234-xyz3c"
echo "=== DB POD STATUS ===" && kubectl get pod $POD -n dev
echo "=== DB CONNECTIONS ===" && kubectl exec $POD -n dev -- \
  psql -U postgres -d postgres -c "SELECT count(*) FROM pg_stat_activity;"
echo "=== DB RUNNING QUERIES ===" && kubectl exec $POD -n dev -- \
  psql -U postgres -d postgres -c "SELECT query, query_start FROM pg_stat_activity WHERE state = 'active';"
```

---

## EMERGENCY RESPONSES

### If everything is down:
```bash
# 1. Check what's actually broken
kubectl get all -n dev 2>&1 | grep -E "0/|ERROR|Pending|CrashLoop"

# 2. Get node status
kubectl get nodes

# 3. Check events for clues
kubectl get events -n dev --sort-by='.lastTimestamp' | tail -20

# 4. If nodes down, check AWS
aws ec2 describe-instances --filters "Name=tag:cluster,Values=my-cluster" \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name]'

# 5. If no immediate fix visible, scale down and up
kubectl scale deployment employee-app --replicas=0 -n dev
kubectl scale deployment employee-app --replicas=3 -n dev
```

### If K8s healthy but app broken:
```bash
# 1. Check app logs
kubectl logs -l app=employee-app -n dev --all-containers=true --tail=100

# 2. Check database
kubectl exec <db-pod> -n dev -- psql -U postgres -d postgres -c "SELECT 1"

# 3. Force restart app
kubectl rollout restart deployment/employee-app -n dev

# 4. Wait for recovery
kubectl rollout status deployment/employee-app -n dev
```

