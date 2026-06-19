# 🎓 CROSS-ENVIRONMENT TROUBLESHOOTING - LIVE PRACTICE
## Learn by Doing: Real Commands + Real Outputs from Your Project

---

## 📋 YOUR CURRENT PROJECT SETUP

Your environment has:
- **Docker Compose Services:** Jenkins (8080), SonarQube (9000)
- **Kubernetes:** Minikube available
- **Namespace:** `dev` (where your app runs)
- **Application:** employee-service
- **Database:** PostgreSQL (in K8s)

---

## 🎯 PRACTICE SCENARIO 1: "Website Not Loading"

### THE PROBLEM
A user reports: **"I can't access the employee application at all"**

### THE DECISION TREE

```
Is it K8s problem?
    ↓
    YES - Pods not running / crashing
    NO - Skip to LINUX checks
```

---

## STEP 1: KUBERNETES QUICK CHECK (5 minutes)

### Command 1: Check if Pods are running

```bash
COMMAND:
kubectl get pods -n dev
```

**EXPECTED OUTPUT - HEALTHY:**
```
NAME                              READY   STATUS    RESTARTS   AGE
employee-app-5f4d8c9b2-xyz1a     1/1     Running   0          2d
employee-app-5f4d8c9b2-xyz2b     1/1     Running   0          1d
postgres-deployment-abc1234-xyz3d 1/1     Running   0          3d
```

**What this means:**
- All Pods in `Running` state ✓
- All show `1/1` Ready (container healthy) ✓
- No high `RESTARTS` count (not crashing) ✓

---

**ACTUAL OUTPUT - PROBLEM:**
```
NAME                              READY   STATUS             RESTARTS   AGE
employee-app-5f4d8c9b2-xyz1a     0/1     Pending            0          15m
employee-app-5f4d8c9b2-xyz2b     0/1     CrashLoopBackOff   5          10m
postgres-deployment-abc1234-xyz3d 1/1     Running            0          3d
```

**Problems identified:**
1. ❌ Pod `xyz1a` is `Pending` (can't be scheduled)
2. ❌ Pod `xyz2b` is `CrashLoopBackOff` (crashing repeatedly - 5 restarts!)
3. ✓ PostgreSQL running (good)

**DIAGNOSIS:** This IS a K8s problem!

---

### Command 2: Check Services

```bash
COMMAND:
kubectl get svc -n dev
```

**EXPECTED OUTPUT - HEALTHY:**
```
NAME               TYPE       CLUSTER-IP      PORT(S)
employee-service  ClusterIP  10.96.0.50      8000/TCP
postgres-service  ClusterIP  10.96.0.200     5432/TCP
```

**What this means:**
- Services exist ✓
- They have ClusterIP (internal addresses) ✓

---

### Command 3: Check Endpoints

```bash
COMMAND:
kubectl get endpoints -n dev
```

**EXPECTED OUTPUT - HEALTHY:**
```
NAME               ENDPOINTS
employee-service  10.0.1.100:8000,10.0.2.100:8000
postgres-service  10.0.1.150:5432
```

**What this means:**
- Services connected to Pods ✓
- employee-service has 2 endpoints (2 Pods running) ✓
- Database accessible ✓

---

**ACTUAL OUTPUT - PROBLEM:**
```
NAME               ENDPOINTS
employee-service  <none>
postgres-service  <none>
```

**Problem:** No Pods behind services! Even if Pods exist, they're not connected.

---

### Command 4: Find WHY Pods are failing

```bash
COMMAND:
kubectl describe pod employee-app-5f4d8c9b2-xyz2b -n dev
```

**OUTPUT - Common Issue #1: Pod Pending**
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
           3 Insufficient memory. Requested 256Mi but only 50Mi available.
```

**ROOT CAUSE:** Not enough memory on any node to schedule Pod!

---

**OUTPUT - Common Issue #2: Pod Crashing**
```
Name:             employee-app-5f4d8c9b2-xyz2b
Namespace:        dev
Status:           Running
RestartCount:     5

Events:
  Type     Reason             Age   From               Message
  ----     ------             ---   ----               -------
  Normal   Created            10m   kubelet            Created container employee-app
  Normal   Started            10m   kubelet            Started container employee-app
  Warning  BackOff            9m    kubelet            Back-off restarting failed container
  Warning  BackOff            8m    kubelet            Back-off restarting failed container
  Normal   Created            7m    kubelet            Created container employee-app
  Normal   Started            7m    kubelet            Started container employee-app
  Warning  BackOff            6m    kubelet            Back-off restarting failed container
```

**Pattern:** Creates → Starts → Crashes → Repeats

**Check logs to see WHY:**

```bash
COMMAND:
kubectl logs employee-app-5f4d8c9b2-xyz2b -n dev --previous
```

**OUTPUT - Revealing the cause:**
```
2024-03-18 10:30:00 - Starting FastAPI application
2024-03-18 10:30:05 - Connecting to database: postgres-service:5432
2024-03-18 10:30:10 - ERROR: could not connect to server: Connection refused
2024-03-18 10:30:10 - Is the server running on host "postgres-service" (10.96.0.200) 
                      and accepting TCP/IP connections on port 5432?
2024-03-18 10:30:10 - FATAL: Database connection failed, exiting
```

**ROOT CAUSE:** Cannot connect to PostgreSQL!

---

## DIAGNOSIS: K8S PROBLEM FOUND ✓

**Your findings:**
- ❌ Pod Pending (insufficient resources)
- ❌ Pod Crashing (database connection failed)
- ❌ No endpoints (services empty)

**Next step:** Use **K8S_TROUBLESHOOTING.md** scenarios to fix

---

---

## STEP 2: LINUX CHECK (if K8s healthy, go here)

### IF K8s looks good, check the OS layer:

```bash
COMMAND:
ssh -i your-key.pem ubuntu@<node-ip>
```

---

### Command 1: Check CPU

```bash
COMMAND:
top -b -n 1 | head -10
```

**OUTPUT - HEALTHY:**
```
top - 10:35:42 up 45 days, 2:15,  2 users,  load average: 0.45, 0.52, 0.48
Tasks:  98 total,   2 running,  96 sleeping,   0 stopped,   0 zombie
%Cpu(s):  15.2 us,   3.8 sy,   0.0 ni,  80.1 id,   0.5 wa,   0.2 hi,  0.2 si,  0.0 st

PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND
5432 ubuntu   20   0 1234567 456789  23456 S  8.5  5.8   2:34.56 python
2345 ubuntu   20   0  456789 234567  12345 S  6.2  3.0   1:23.45 postgres
```

**Checklist:**
- ✓ Load average: 0.45 (low)
- ✓ %CPU idle: 80.1% (plenty of headroom)
- ✓ No zombie processes
- ✓ No processes at 100% CPU

---

**OUTPUT - PROBLEM:**
```
top - 10:35:42 up 5 days, 0:15,  1 user,  load average: 8.5, 7.2, 6.8
Tasks: 120 total,   5 running, 115 sleeping,  0 stopped,  0 zombie
%Cpu(s):  95.2 us,   4.1 sy,   0.0 ni,   0.5 id,   0.1 wa,  0.1 hi,  0.0 si,  0.0 st

PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND
8765 ubuntu   20   0 2456789 1897654 45678 R 95.2 24.0  45:23.12 python
1234 ubuntu   20   0  987654  567890 34567 R 82.3 7.2   32:15.89 postgres
```

**Problems:**
- ❌ Load average: 8.5 (way too high!)
- ❌ CPU idle: 0.5% (system maxed out!)
- ❌ One process at 95% CPU
- ❌ Another at 82% CPU

**DIAGNOSIS:** HIGH CPU PROBLEM! → Use LINUX_TROUBLESHOOTING Scenario 1

---

### Command 2: Check Memory

```bash
COMMAND:
free -h
```

**OUTPUT - HEALTHY:**
```
              total        used        free      shared  buff/cache   available
Mem:          7.7Gi       2.3Gi       4.2Gi       87Mi       1.2Gi       4.5Gi
Swap:         2.0Gi       0.0Gi       2.0Gi
```

**Checklist:**
- ✓ Free: 4.2Gi (plenty!)
- ✓ Available: 4.5Gi (buffer is there)
- ✓ Swap used: 0Gi (not needed)

---

**OUTPUT - PROBLEM:**
```
              total        used        free      shared  buff/cache   available
Mem:          7.7Gi       7.4Gi       234Mi       98Mi       123Mi        156Mi
Swap:         2.0Gi       1.8Gi       187Mi
```

**Problems:**
- ❌ Free: 234Mi (very low! < 500MB = warning)
- ❌ Available: 156Mi (critical!)
- ❌ Swap used: 1.8Gi (disk swapping happening - SLOW!)

**DIAGNOSIS:** MEMORY LEAK! → Use LINUX_TROUBLESHOOTING Scenario 2

---

### Command 3: Check Disk

```bash
COMMAND:
df -h
```

**OUTPUT - HEALTHY:**
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/xvda1       20G   8.5G  11.5G 43%  /
/dev/xvdb1      100G   24G   76G   24%  /mnt/data
tmpfs           3.8G  0.1G   3.7G  2%   /dev/shm
```

**Checklist:**
- ✓ Root (/) at 43% (plenty of space)
- ✓ /mnt/data at 24% (lots available)
- ✓ tmpfs at 2% (normal)

---

**OUTPUT - PROBLEM:**
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/xvda1       20G  20G   0G   100% /
/dev/xvdb1      100G  95G  4.8G 95%  /mnt/data
tmpfs           3.8G  3.8G  0G   100% /dev/shm
```

**Problems:**
- ❌ Root (/) at 100% (NO SPACE!)
- ❌ /mnt/data at 95% (nearly full)
- ❌ tmpfs at 100% (shared memory full)

**DIAGNOSIS:** DISK FULL! → Use LINUX_TROUBLESHOOTING Scenario 3

---

### Command 4: Check for OS Errors

```bash
COMMAND:
dmesg | tail -20
```

**OUTPUT - HEALTHY:**
```
[2024-03-18 10:00:00] kernel: [12345.123456] audit: type=1400 
           audit(1234567890.123:123): apparmor="ALLOWED" 
[2024-03-18 10:01:00] kernel: [12400.234567] floppy0: no floppy controllers found
[2024-03-18 10:02:00] systemd[1]: Started Session c1 of user ubuntu.
```

**Checklist:**
- ✓ No ERROR messages
- ✓ No OUT OF MEMORY
- ✓ No I/O errors
- ✓ No CORRUPTION

---

**OUTPUT - PROBLEM:**
```
[2024-03-18 09:30:00] kernel: [3456.234567] Out of memory: 
           Kill process 8765 (python) score 567 or sacrifice child
[2024-03-18 09:30:01] kernel: [3456.234568] Killed process 8765 (python) 
           total-vm:2456789kB, anon-rss:5234567kB
[2024-03-18 09:35:00] kernel: [3700.123456] EXT4-fs error (device xvda1): 
           bad entry in directory: rec_len % 4 != 0
[2024-03-18 09:40:00] kernel: [3950.654321] Buffer I/O error on device xvda1, 
           logical block 123456
```

**Problems:**
- ❌ OOM Killer killed process
- ❌ Filesystem corruption detected

**DIAGNOSIS:** OS-level failure! → Use LINUX_TROUBLESHOOTING Scenario 2 & 5

---

## DIAGNOSIS: LINUX PROBLEM FOUND ✓

**If you found any of:**
- ❌ High CPU (>80%)
- ❌ Low memory (<500MB)
- ❌ Disk full (>90%)
- ❌ I/O errors in dmesg

**Next step:** Use **LINUX_TROUBLESHOOTING.md** scenarios to fix

---

---

## STEP 3: DATABASE CHECK

### IF K8s and Linux are healthy, check database:

```bash
COMMAND:
kubectl exec <app-pod> -n dev -- \
  psql -h postgres-service -U employee_user -d employeedb -c "SELECT 1"
```

**OUTPUT - HEALTHY:**
```
 ?column?
----------
        1
(1 row)
```

**What this means:**
- ✓ Database service reachable ✓
- ✓ Credentials working ✓
- ✓ Query executing ✓

---

**OUTPUT - PROBLEM:**
```
psql: could not translate host name "postgres-service" to address: Name or service not known
```

**Problem:** DNS not resolving postgres-service!

**DIAGNOSIS:** K8s DNS or network issue → Back to K8S_TROUBLESHOOTING

---

### Check Database Performance

```bash
COMMAND:
kubectl exec <postgres-pod> -n dev -- \
  psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

**OUTPUT - HEALTHY:**
```
 count
-------
    12
(1 row)
```

**What this means:**
- ✓ Only 12 connections (normal range)
- ✓ Not overwhelmed

---

**OUTPUT - PROBLEM:**
```
 count
-------
   195
(1 row)
```

**Problem:** 195 connections! Should be 10-50

**DIAGNOSIS:** Connection leak → Use LINUX_TROUBLESHOOTING Scenario 4

---

## DIAGNOSIS: DATABASE PROBLEM FOUND ✓

**If database checks fail:**
- Connection errors → K8s network issue
- Too many connections → Application leak
- Query slow → Database optimization needed

---

---

## STEP 4: APPLICATION CHECK

### IF everything else healthy, check application:

```bash
COMMAND:
kubectl logs <pod> -n dev --tail=100
```

**OUTPUT - HEALTHY:**
```
2024-03-18 10:30:00 - [INFO] Starting FastAPI application
2024-03-18 10:30:05 - [INFO] Connected to database: postgres-service:5432
2024-03-18 10:30:10 - [INFO] Loading configuration from environment
2024-03-18 10:30:15 - [INFO] Server running on 0.0.0.0:8000
2024-03-18 10:30:20 - [INFO] /health endpoint responding
2024-03-18 10:30:25 - [INFO] Processing request: GET /employees
2024-03-18 10:30:26 - [INFO] Returned 42 employees
```

**Checklist:**
- ✓ No ERROR messages
- ✓ Connected to database ✓
- ✓ Server running ✓
- ✓ Requests processing ✓

---

**OUTPUT - PROBLEM:**
```
2024-03-18 10:30:00 - [INFO] Starting FastAPI application
2024-03-18 10:30:05 - [ERROR] Database connection failed: timeout
2024-03-18 10:30:05 - [ERROR] Could not initialize application
2024-03-18 10:30:05 - [CRITICAL] Application shutting down
```

**Problem:** Application can't connect to database!

**DIAGNOSIS:** Either database is down (check DB), or network connectivity issue (check K8s)

---

### Check Application Health Endpoint

```bash
COMMAND:
kubectl exec <pod> -n dev -- curl http://localhost:8000/health
```

**OUTPUT - HEALTHY:**
```json
{"status": "healthy", "uptime": "2 hours", "db": "connected"}
```

**What this means:**
- ✓ Application responding ✓
- ✓ Database connected ✓

---

**OUTPUT - PROBLEM:**
```
{"status": "unhealthy", "error": "database_connection_failed"}
```

**Problem:** Application reporting database connection failure!

**DIAGNOSIS:** Database issue or network connectivity → Check database or K8s

---

## DIAGNOSIS: APPLICATION PROBLEM FOUND ✓

**If application checks fail:**
- Database errors → Check database connectivity
- Logic errors in logs → Debug code
- No logs (crashed) → Check K8s restart status

---

---

## 🎯 COMPLETE ISOLATION FLOWCHART - YOUR CHECKLIST

Use this exact sequence:

```
┌─────────────────────────────────────────────────────────────┐
│ USER REPORTS PROBLEM: "Website not working / slow / errors" │
└─────────────────────────────────────────────────────────────┘
                           ↓

┌─ TIER 1: KUBERNETES ──────────────────────────────────────────┐
│                                                                │
│ Run 3 commands (30 seconds):                                  │
│  1. kubectl get pods -n dev                                   │
│     ├─ All Running? YES → Continue to next                   │
│     └─ Any Pending/Crashing? NO → STOP HERE                  │
│                                  → Use K8S_TROUBLESHOOTING.md │
│                                                                │
│  2. kubectl get endpoints -n dev                              │
│     ├─ Have endpoints? YES → Continue                        │
│     └─ Empty? NO → STOP HERE                                 │
│                  → Use K8S_TROUBLESHOOTING.md Scenario 2      │
│                                                                │
│  3. kubectl top pods -n dev                                   │
│     ├─ Under limits? YES → Continue                          │
│     └─ Over limits? NO → STOP HERE                           │
│                        → Use K8S_TROUBLESHOOTING.md Scenario 4│
│                                                                │
│ Result: K8s HEALTHY? ✓ Continue to TIER 2                    │
│         K8s PROBLEM? ✗ FIX with K8S_TROUBLESHOOTING.md       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
                           ↓

┌─ TIER 2: LINUX OS ────────────────────────────────────────────┐
│                                                                │
│ SSH to node and run 4 commands (1 minute):                   │
│  1. top -b -n 1 | head -3                                    │
│     ├─ CPU idle > 20%? YES → Continue                       │
│     └─ CPU idle < 20%? NO → STOP HERE                       │
│                          → Use LINUX_TROUBLESHOOTING.md      │
│                            Scenario 1 (HIGH CPU)              │
│                                                                │
│  2. free -h                                                   │
│     ├─ Free memory > 500MB? YES → Continue                   │
│     └─ Free memory < 500MB? NO → STOP HERE                   │
│                               → Use LINUX_TROUBLESHOOTING.md │
│                                 Scenario 2 (MEMORY LEAK)      │
│                                                                │
│  3. df -h /                                                   │
│     ├─ Disk < 85%? YES → Continue                           │
│     └─ Disk > 85%? NO → STOP HERE                           │
│                        → Use LINUX_TROUBLESHOOTING.md        │
│                          Scenario 3 (DISK FULL)              │
│                                                                │
│  4. dmesg | tail -20                                          │
│     ├─ No errors? YES → Continue                            │
│     └─ Has errors? NO → STOP HERE                           │
│                        → Use LINUX_TROUBLESHOOTING.md        │
│                          Scenario 5 (FILE CORRUPTION)        │
│                                                                │
│ Result: Linux HEALTHY? ✓ Continue to TIER 3                 │
│         Linux PROBLEM? ✗ FIX with LINUX_TROUBLESHOOTING.md  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
                           ↓

┌─ TIER 3: DATABASE ────────────────────────────────────────────┐
│                                                                │
│ From app pod:                                                 │
│  1. psql -h postgres-service -U user -d db -c "SELECT 1"    │
│     ├─ Works? YES → Continue                                │
│     └─ Fails? NO → STOP HERE                                │
│                   → K8s networking problem                    │
│                   → Use K8S_TROUBLESHOOTING.md               │
│                                                                │
│  2. SELECT count(*) FROM pg_stat_activity;                   │
│     ├─ Connections < 50? YES → Continue                     │
│     └─ Connections > 100? NO → STOP HERE                    │
│                               → Use LINUX_TROUBLESHOOTING.md │
│                                 Scenario 4 (CONNECTION LEAK)  │
│                                                                │
│ Result: Database HEALTHY? ✓ Continue to TIER 4              │
│         Database PROBLEM? ✗ Fix DB or connections            │
│                                                                │
└────────────────────────────────────────────────────────────────┘
                           ↓

┌─ TIER 4: APPLICATION ─────────────────────────────────────────┐
│                                                                │
│  1. kubectl logs <pod> -n dev --tail=50                       │
│     ├─ No errors? YES → Continue                            │
│     └─ Has errors? NO → STOP HERE                           │
│                        → Debug application code               │
│                        → Fix and redeploy                     │
│                                                                │
│  2. curl http://localhost:8000/health                         │
│     ├─ Healthy response? YES → Continue                      │
│     └─ Error response? NO → STOP HERE                        │
│                           → Application issue                 │
│                           → Check logs for details            │
│                                                                │
│ Result: App HEALTHY? ✓ SYSTEM OK                             │
│         App PROBLEM? ✗ Fix application code                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
                           ↓

┌─────────────────────────────────────────────────────────────┐
│ ALL TIERS HEALTHY ✓                                          │
│ Problem resolved OR issue is external (network/user side)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 QUICK REFERENCE TABLE

| Tier | What to Check | Command | Pass Criteria | Fail → Action |
|------|---|---|---|---|
| K8s | Pod status | `kubectl get pods -n dev` | All Running, 1/1 Ready | K8S_TROUBLESHOOTING Scenario 1-3 |
| K8s | Endpoints | `kubectl get endpoints -n dev` | Has endpoints | K8S_TROUBLESHOOTING Scenario 2 |
| K8s | Resources | `kubectl top pods -n dev` | Under limits | K8S_TROUBLESHOOTING Scenario 4 |
| Linux | CPU | `top -b -n 1` | idle > 20% | LINUX_TROUBLESHOOTING Scenario 1 |
| Linux | Memory | `free -h` | free > 500MB | LINUX_TROUBLESHOOTING Scenario 2 |
| Linux | Disk | `df -h /` | usage < 85% | LINUX_TROUBLESHOOTING Scenario 3 |
| Linux | Errors | `dmesg \| tail -20` | No errors | LINUX_TROUBLESHOOTING Scenario 5 |
| DB | Connection | `psql ... SELECT 1` | Works | K8s network issue |
| DB | Connections | `SELECT count(*)...` | < 50 | LINUX_TROUBLESHOOTING Scenario 4 |
| App | Logs | `kubectl logs ...` | No errors | Debug code |
| App | Health | `curl /health` | Healthy response | Fix app code |

---

## 💡 REMEMBER THESE PRINCIPLES

1. **Check in order:** K8s → Linux → Database → Application
2. **Never skip:** False positive at one tier wastes 1+ hour
3. **Fix at root:** If Linux problem, don't increase K8s resources
4. **One at a time:** Fix one issue before checking next tier
5. **Document:** Save commands and outputs for team/future reference

