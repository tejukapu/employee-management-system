# 🎯 CROSS-ENVIRONMENT TROUBLESHOOTING FLOWCHART
## K8s → Linux → Application Code Isolation

---

## DECISION TREE: Where is the Problem?

```
ISSUE REPORTED
    ↓
    "Website not working / slow / errors"
    ↓
├─ STEP 1: Check K8S (Takes 5 min) ────────────────────────────────┐
│                                                                   │
│ Run:                                                              │
│ kubectl get pods -n dev                                          │
│ kubectl get svc -n dev                                           │
│ kubectl get endpoints -n dev                                     │
│ kubectl top pods -n dev                                          │
│                                                                   │
│ Result:                                                           │
│ ✓ All Pods Running (1/1)  ──┐                                    │
│ ✓ Services have Endpoints   ├─→ K8s HEALTHY ✓                   │
│ ✓ Resources under limits    │   Go to LINUX checks               │
│                                                                   │
│ ✗ Pod Pending/Crashing  ──┐                                      │
│ ✗ No Endpoints (svc)       ├─→ K8S PROBLEM ✗                    │
│ ✗ Resource limits hit      │   Use K8S_TROUBLESHOOTING.md        │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
    │
    │  (K8s healthy? Go to next step)
    ↓
├─ STEP 2: Check LINUX (Takes 5 min) ──────────────────────────────┐
│                                                                   │
│ SSH to Node:                                                      │
│ ssh ubuntu@<node-ip>                                             │
│                                                                   │
│ Run:                                                              │
│ top -b -n 1 (check CPU/Memory)                                   │
│ df -h (check disk)                                               │
│ netstat -an | wc -l (check connections)                          │
│ dmesg | tail -20 (check errors)                                  │
│                                                                   │
│ Result:                                                           │
│ ✓ CPU < 80%             ──┐                                      │
│ ✓ Memory > 500MB free    ├─→ LINUX HEALTHY ✓                    │
│ ✓ Disk < 85%             │   Problem in APPLICATION CODE        │
│ ✓ No errors in dmesg    │   Go to APP DEBUG                     │
│                                                                   │
│ ✗ CPU > 90%          ──┐                                         │
│ ✗ Memory < 100MB     ├─→ LINUX PROBLEM ✗                        │
│ ✗ Disk > 95%         │   Use LINUX_TROUBLESHOOTING.md           │
│ ✗ I/O errors        │                                           │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
    │
    │  (Linux healthy? Application issue)
    ↓
├─ STEP 3: Check APPLICATION (Takes 10 min) ───────────────────────┐
│                                                                   │
│ Get Container Shell:                                              │
│ kubectl exec -it <pod> -n dev -- bash                            │
│                                                                   │
│ Check App Logs:                                                   │
│ tail -f /app/logs/app.log                                        │
│ tail -f /app/logs/error.log                                      │
│                                                                   │
│ Result:                                                           │
│ ✓ No errors in logs     ──┐                                      │
│ ✓ App responding        ├─→ APP HEALTHY ✓                       │
│ ✓ DB queries succeeding │   Problem might be EXTERNAL            │
│                                                                   │
│ ✗ Database errors   ──┐                                          │
│ ✗ Connection errors ├─→ APP PROBLEM ✗                           │
│ ✗ Logic errors      │   Check code or dependencies              │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## QUICK DIAGNOSTIC FLOWCHART

```
PROBLEM
  ↓
  Can users access website at all?
  
  NO → Check K8s
      ├─ kubectl get pods → Any running?
      │  ├─ Not running? → K8S_TROUBLESHOOTING (Scenario 1-3)
      │  └─ Running? → Next check
      │
      ├─ kubectl get svc → Service exists?
      │  ├─ No? → Create service
      │  └─ Yes? → Next check
      │
      └─ kubectl get endpoints → Pods in service?
         ├─ No endpoints? → K8S_TROUBLESHOOTING (Scenario 2)
         └─ Has endpoints? → Next check
  
  YES → Website loads but slow/errors
      ├─ Check Performance
      │  ├─ kubectl top pods → Resources under limit?
      │  │  ├─ No? → K8S_TROUBLESHOOTING (Scenario 4)
      │  │  └─ Yes? → Next check
      │  │
      │  └─ top (on Linux) → System resources okay?
      │     ├─ No? → LINUX_TROUBLESHOOTING
      │     └─ Yes? → Next check
      │
      └─ Check Application
         ├─ kubectl logs → Any errors?
         │  ├─ Yes? → Fix app code / dependencies
         │  └─ No? → Next check
         │
         └─ Test Database
            ├─ kubectl exec → curl db service
            ├─ Works? → Might be data/logic issue
            └─ Fails? → Check DB connection

RESOLVED ✓
```

---

## STEP-BY-STEP ISOLATION PROCESS

### LEVEL 1: QUICK CHECK (2 minutes)

```bash
# 1. Can K8s Pods reach service?
kubectl exec <app-pod> -n dev -- \
  curl http://employee-service.dev:8000/health

# If YES → Move to Level 2
# If NO  → K8S issue, check SCENARIO 2 in K8S_TROUBLESHOOTING.md
```

### LEVEL 2: SERVICE CHECK (3 minutes)

```bash
# 1. Are all services working?
kubectl get svc,endpoints -n dev

# 2. Any pod not ready?
kubectl get pods -n dev

# 3. Any deployment issues?
kubectl describe deployment employee-app -n dev | tail -20

# If OK → Move to Level 3
# If issues → Use K8S_TROUBLESHOOTING.md scenarios
```

### LEVEL 3: RESOURCE CHECK (3 minutes)

```bash
# 1. Resources available?
kubectl top nodes
kubectl top pods -n dev

# 2. Pod limits hit?
kubectl describe pod <pod-name> -n dev | grep -A 5 "Limits"

# If OK → Move to Level 4
# If resource issue → Use K8S_TROUBLESHOOTING (Scenario 4)
```

### LEVEL 4: NODE HEALTH CHECK (3 minutes)

SSH to node:
```bash
# 1. CPU okay?
top -b -n 1 | head -3

# 2. Memory okay?
free -h

# 3. Disk okay?
df -h /

# 4. Errors?
dmesg | tail -10

# If OK → Move to Level 5
# If issues → Use LINUX_TROUBLESHOOTING.md scenarios
```

### LEVEL 5: APPLICATION DEBUG (5 minutes)

```bash
# 1. Check app logs
kubectl logs <pod> -n dev --tail=100

# 2. Check database connection
kubectl exec <pod> -n dev -- \
  psql -h postgres-service -U hradmin -d hrdb -c "SELECT 1"

# 3. Test API manually
kubectl exec <pod> -n dev -- \
  curl http://localhost:8000/health

# If all OK → Application working, might be frontend/user issue
# If errors → Debug application code
```

---

## REAL SCENARIO DECISION TREES

### SCENARIO A: "Website not loading at all"

```
START
  ↓
Is ALB responding?
├─ YES → Continue
└─ NO → AWS issue (Route 53, ALB, Security Groups)

Does Ingress have ADDRESS?
├─ YES → Continue  
└─ NO → Use K8S_TROUBLESHOOTING.md Scenario 6

Are Pods Running?
├─ YES → Continue
└─ NO → Use K8S_TROUBLESHOOTING.md Scenario 1-3

Do Services have Endpoints?
├─ YES → Continue
└─ NO → Use K8S_TROUBLESHOOTING.md Scenario 2

Can Pod reach database?
├─ YES → Check logs for errors → Fix app code
└─ NO → Check K8s DNS or Linux network connectivity

RESOLVED or NEEDS APP CODE FIX
```

### SCENARIO B: "Website loads but is VERY SLOW"

```
START
  ↓
Is CPU high (>80%)?
├─ YES → Use LINUX_TROUBLESHOOTING.md Scenario 1
└─ NO → Continue

Is Memory high (>95%)?
├─ YES → Use LINUX_TROUBLESHOOTING.md Scenario 2
└─ NO → Continue

Is Disk usage high (>90%)?
├─ YES → Use LINUX_TROUBLESHOOTING.md Scenario 3
└─ NO → Continue

Are database connections many?
├─ YES → Use LINUX_TROUBLESHOOTING.md Scenario 4
└─ NO → Continue

Check app logs for slow queries
├─ Found? → Optimize query / database
└─ Not found? → Check external dependencies (S3, API calls)

RESOLVED or NEEDS CODE OPTIMIZATION
```

### SCENARIO C: "Pod keeps crashing"

```
START
  ↓
Check pod status
└─ CrashLoopBackOff → Check logs

Check logs for errors
├─ Database connection error? 
│  └─ Use K8S_TROUBLESHOOTING.md Scenario 3
│
├─ Out of memory error?
│  └─ Use K8S_TROUBLESHOOTING.md Scenario 4
│
├─ Image pull error?
│  └─ Use K8S_TROUBLESHOOTING.md Scenario 5
│
└─ Other error?
   └─ Search error message in code

RESOLVED or NEEDS CODE FIX
```

---

## ISOLATION CHECKLIST

Use this to narrow down the problem:

```
☐ SECTION 1: KUBERNETES (K8s working?)
  ☐ All Pods Running (status = Running)
  ☐ All Pods Ready (Ready = 1/1)
  ☐ No pending Pods
  ☐ No CrashLoopBackOff
  ☐ All Services have Endpoints
  ☐ Ingress has ADDRESS
  ☐ Certificate is Ready
  ☐ Pod memory under limit
  ☐ Pod CPU under limit
  
  Result: K8s healthy? ✓ YES → Go to SECTION 2
          K8s healthy? ✗ NO  → Use K8S_TROUBLESHOOTING.md

☐ SECTION 2: LINUX (OS working?)
  ☐ CPU usage < 80%
  ☐ Memory > 500MB free
  ☐ Disk usage < 85%
  ☐ Load average normal
  ☐ No I/O errors (dmesg)
  ☐ Network interface UP
  ☐ Routes configured
  ☐ DNS resolving
  ☐ No OOM killer events
  ☐ No file corruption errors
  
  Result: Linux healthy? ✓ YES → Go to SECTION 3
          Linux healthy? ✗ NO  → Use LINUX_TROUBLESHOOTING.md

☐ SECTION 3: DATABASE (DB working?)
  ☐ PostgreSQL process running
  ☐ DB port listening (5432)
  ☐ DB connection successful
  ☐ Query results returning
  ☐ Connection pool healthy
  ☐ No slow queries
  ☐ Disk space adequate
  ☐ Replication healthy (if Multi-AZ)
  
  Result: DB healthy? ✓ YES → Go to SECTION 4
          DB healthy? ✗ NO  → Check DB logs

☐ SECTION 4: APPLICATION (App working?)
  ☐ No errors in app logs
  ☐ No exceptions logged
  ☐ Health check endpoint responding
  ☐ API endpoints responding
  ☐ No infinite loops
  ☐ No memory leaks
  ☐ All required dependencies available
  ☐ Environment variables set correctly
  
  Result: App healthy? ✓ YES → Issue might be external/user-side
          App healthy? ✗ NO  → Fix application code

ALL SECTIONS HEALTHY? → SYSTEM OPERATIONAL ✓
```

---

## DEBUGGING COMMAND SEQUENCE

**When user reports "website broken":**

```bash
# Time: 0:00 - KUBERNETES CHECKS (1 minute)
kubectl get pods -n dev
kubectl get svc -n dev
kubectl get endpoints -n dev

# Time: 1:00 - POD SPECIFIC CHECKS (2 minutes)
kubectl describe pod <problem-pod> -n dev
kubectl logs <problem-pod> -n dev --tail=30

# Time: 3:00 - SYSTEM CHECKS (2 minutes)
kubectl top nodes
kubectl top pods -n dev

# Time: 5:00 - SSH TO NODE (2 minutes)
ssh -i key.pem ubuntu@<node-ip>
top -b -n 1 | head -5
free -h
df -h /

# Time: 7:00 - APP INTERNALS (2 minutes)
kubectl exec <pod> -n dev -- curl http://localhost:8000/health
kubectl exec <pod> -n dev -- \
  psql -h postgres-service -U hradmin -d hrdb -c "SELECT 1"

# Time: 9:00 - DECISION
# If all healthy → Problem is user/network/frontend side
# If K8s bad → Follow K8S_TROUBLESHOOTING.md
# If Linux bad → Follow LINUX_TROUBLESHOOTING.md
# If App bad → Fix code
```

**Total time to narrow down: ~10 minutes**

---

## WHO TO ESCALATE TO

After running isolation:

| Symptoms | Owner | Next Step |
|----------|-------|-----------|
| K8s issue (Pending, Crashing, etc) | **DevOps/SRE** | K8S_TROUBLESHOOTING.md |
| Linux/Hardware issue (High CPU, OOM, Disk Full) | **System Admin/SRE** | LINUX_TROUBLESHOOTING.md |
| Database issue (Connection pool, slow query) | **DBA/Backend** | Database tuning |
| Application bug (Errors in logs, logic issue) | **Developer** | Code review/fix |
| Network/AWS issue (DNS, ALB, SG) | **DevOps/SRE** | AWS console review |

---

## KEY PRINCIPLES

1. **Always check K8s first** (fastest to verify)
2. **Then check Linux** (OS-level issues)
3. **Then check DB** (dependency issues)
4. **Then check App** (code issues)
5. **Never skip steps** (false positive wastes time)
6. **Document what you find** (helps next person)

---

## COMMON COMBINATIONS

**K8s ✓ + Linux ✗ + DB ✓ = Linux problem**
→ Use LINUX_TROUBLESHOOTING.md

**K8s ✗ + Linux ✓ + DB ✓ = K8s problem**
→ Use K8S_TROUBLESHOOTING.md

**K8s ✓ + Linux ✓ + DB ✓ + App ✗ = Application problem**
→ Debug application code, check logs

**K8s ✓ + Linux ✓ + DB ✗ = Database problem**
→ Check database service, connections, resources

**K8s ✗ + Linux ✗ = Multiple failures**
→ Start with K8s (Scenario 1), likely cascade effect

---

## REMEMBER

- K8s Healthy ≠ Problem Solved (must check Linux too)
- Linux Healthy ≠ Problem Solved (must check Application)
- All Healthy ≠ User Issue Solved (might be network/frontend)
- **Always follow the checklist in order**

