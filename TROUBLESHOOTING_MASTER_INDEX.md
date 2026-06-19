# 🚨 PRODUCTION TROUBLESHOOTING MASTER INDEX
## Kubernetes → Linux → Complete Real-Time Debugging Guide

---

## 📚 FILES CREATED (4 Comprehensive Guides)

### 1. **K8S_PRODUCTION_TROUBLESHOOTING.md** (22 KB) ⭐ START HERE

**6 Real Scenarios with Complete Diagnosis & Fixes:**

1. ✓ **Pod Stuck in PENDING** 
   - Issue: Insufficient resources
   - Commands: kubectl describe, kubectl top
   - Output: Actual error messages shown
   - Fix: Scale nodes or reduce requests

2. ✓ **Service Not Responding**
   - Issue: No endpoints, selector mismatch
   - Commands: kubectl get endpoints, kubectl get services
   - Output: Actual mismatch shown
   - Fix: Add correct labels

3. ✓ **Pod Crashing (CrashLoopBackOff)**
   - Issue: DB connection failed
   - Commands: kubectl logs, kubectl logs --previous
   - Output: Actual database error shown
   - Fix: Delete and recreate pod

4. ✓ **High CPU/Memory - OOMKilled**
   - Issue: App exceeding limits
   - Commands: kubectl top pods
   - Output: Actual usage vs limits shown
   - Fix: Increase memory limits

5. ✓ **Stuck Deployment**
   - Issue: Image not found
   - Commands: kubectl describe deployment
   - Output: Actual image error shown
   - Fix: Use correct image tag

6. ✓ **Ingress Not Routing**
   - Issue: Certificate not ready
   - Commands: kubectl get ingress, kubectl get certificate
   - Output: Actual cert status shown
   - Fix: Create certificate issuer

**Plus: Rapid diagnostic commands + Common issues table**

---

### 2. **LINUX_PRODUCTION_TROUBLESHOOTING.md** (23 KB)

**6 Real Scenarios with Complete Diagnosis & Fixes:**

1. ✓ **High CPU - App Slow**
   - Issue: Infinite loop in code
   - Commands: top, strace, gdb
   - Output: Stack traces, CPU usage shown
   - Fix: Remove infinite loop

2. ✓ **Out of Memory - OOM Killer**
   - Issue: Memory leak in application
   - Commands: free, ps, memory-profiler
   - Output: Memory growth graph shown
   - Fix: Fix memory leak with generators

3. ✓ **Disk Full - No Space Left**
   - Issue: Large log files not rotated
   - Commands: du, find, df
   - Output: 12GB in /var/log shown
   - Fix: Truncate logs, update rotation

4. ✓ **Database Connection Issues**
   - Issue: Connection pool leak
   - Commands: psql, lsof, netstat
   - Output: 195 connections shown
   - Fix: Fix connection pool config

5. ✓ **File Corruption - I/O Errors**
   - Issue: Disk failure
   - Commands: smartctl, fsck, dmesg
   - Output: Smart errors shown
   - Fix: Repair filesystem

6. ✓ **Network Connectivity Issues**
   - Issue: Missing routes, interface down
   - Commands: ip addr, route, nslookup
   - Output: Missing gateway shown
   - Fix: Add default route

**Plus: Rapid diagnostic commands + Quick reference table**

---

### 3. **CROSS_ENVIRONMENT_TROUBLESHOOTING.md** (14 KB)

**Isolation Decision Tree: K8s → Linux → Application**

✓ Quick decision tree (2 min)
✓ Full diagnostic flowchart
✓ Step-by-step isolation process
✓ Real scenario decision trees:
  - "Website not loading at all"
  - "Website loads but is VERY SLOW"
  - "Pod keeps crashing"
✓ Isolation checklist (5 sections)
✓ Debugging command sequence
✓ Who to escalate to
✓ Common combinations (what each means)

**Best for:** Narrowing down where problem is

---

### 4. **QUICK_COMMANDS_REFERENCE.md** (13 KB)

**Copy-Paste Ready Commands with Real Outputs**

✓ Critical first response (3 min)
✓ Kubernetes commands (list, check, debug, fix)
✓ Linux commands (system, analysis, errors)
✓ Database commands (connections, performance)
✓ Networking commands (DNS, routes, ports)
✓ Combined diagnostics
✓ Monitoring - live watch
✓ Quick reference matrix
✓ Copy-paste command sets
✓ Emergency responses

**Best for:** When you need a command NOW

---

## 🎯 QUICK DECISION: WHICH FILE TO USE?

```
PROBLEM REPORTED
        ↓
        
When I need...
├─ "Complete step-by-step guide for K8s issues"
│  └─ USE: K8S_PRODUCTION_TROUBLESHOOTING.md
│
├─ "Complete step-by-step guide for Linux issues"
│  └─ USE: LINUX_PRODUCTION_TROUBLESHOOTING.md
│
├─ "To figure out WHERE the problem is"
│  └─ USE: CROSS_ENVIRONMENT_TROUBLESHOOTING.md
│
├─ "A command to run RIGHT NOW"
│  └─ USE: QUICK_COMMANDS_REFERENCE.md
│
└─ "Everything organized by problem type"
   └─ USE: This file (MASTER INDEX)
```

---

## 📊 FILE COMPARISON

| File | Content | Length | Best For | Time |
|------|---------|--------|----------|------|
| K8S_PRODUCTION_TROUBLESHOOTING.md | 6 K8s scenarios + fixes | 22 KB | K8s issues | 20 min read |
| LINUX_PRODUCTION_TROUBLESHOOTING.md | 6 Linux scenarios + fixes | 23 KB | Linux issues | 20 min read |
| CROSS_ENVIRONMENT_TROUBLESHOOTING.md | Decision trees + flowcharts | 14 KB | Isolation | 5 min read |
| QUICK_COMMANDS_REFERENCE.md | Commands + outputs | 13 KB | Quick lookup | Copy-paste |

**Total: 72 KB of complete troubleshooting material**

---

## 🚨 REAL SCENARIO EXAMPLES

### Example 1: "Website Down"

```
User: "Website not working!"
You: 30 seconds diagnosis

1. kubectl get pods -n dev
   Output: All running ✓
   
2. kubectl get endpoints -n dev
   Output: Services have endpoints ✓
   
3. kubectl top pods -n dev
   Output: Resources under limit ✓
   
4. SSH to node: top -b -n 1
   Output: CPU 15%, Memory OK ✓
   
5. kubectl logs <pod> -n dev
   Output: No errors ✓
   
Decision: Check AWS ALB / DNS
↓
USE: CROSS_ENVIRONMENT_TROUBLESHOOTING.md (Scenario A)
```

### Example 2: "App Super Slow"

```
User: "Website very slow, sometimes times out"
You: 45 seconds diagnosis

1. kubectl get pods -n dev
   Output: All running ✓
   
2. kubectl top pods -n dev
   Output: CPU 85%, Memory 92% ← HIGH!
   
Decision: CPU or Memory issue
↓
USE: LINUX_PRODUCTION_TROUBLESHOOTING.md (Scenario 1 or 2)
↓
Run: top -b -n 1
Output: python 95% CPU, infinite loop ← FOUND IT!
↓
Fix: Remove infinite loop in code
```

### Example 3: "Pod Keeps Crashing"

```
User: "Pod keeps restarting, service unhealthy"
You: 30 seconds diagnosis

1. kubectl get pods -n dev
   Output: CrashLoopBackOff ✗
   
2. kubectl logs <pod> -n dev --tail=30
   Output: "Database connection refused"
   
3. kubectl get svc postgres-service -n dev
   Output: No endpoints ✗
   
Decision: Database Pod also failing
↓
USE: K8S_PRODUCTION_TROUBLESHOOTING.md (Scenario 3)
↓
Run: kubectl logs postgres-pod -n dev --previous
Output: "/var/lib/postgresql/data: Permission denied"
↓
Fix: Delete pod (Deployment recreates), PVC remounts
```

---

## 📈 TROUBLESHOOTING FLOWCHART

```
PROBLEM REPORTED
    ↓
    Start CROSS_ENVIRONMENT_TROUBLESHOOTING.md
    ↓
    ├─ K8s Check (5 min)
    │  ├─ Healthy ✓ → Go to Linux Check
    │  └─ Issue ✗ → USE K8S_PRODUCTION_TROUBLESHOOTING.md
    │
    ├─ Linux Check (5 min)
    │  ├─ Healthy ✓ → Go to Application Check
    │  └─ Issue ✗ → USE LINUX_PRODUCTION_TROUBLESHOOTING.md
    │
    ├─ Application Check (5 min)
    │  ├─ Healthy ✓ → External issue (user/network side)
    │  └─ Issue ✗ → Fix app code or dependencies
    │
    └─ PROBLEM ISOLATED
       ↓
       USE QUICK_COMMANDS_REFERENCE.md for specific commands
```

---

## ✅ SECTION 1: KUBERNETES ISSUES

### When to Use K8S_PRODUCTION_TROUBLESHOOTING.md

**Use if you see:**
- ✗ Pod Status: Pending
- ✗ Pod Status: CrashLoopBackOff
- ✗ Pod Status: ImagePullBackOff
- ✗ Pod Status: OOMKilled
- ✗ Deployment Status: Stuck rolling out
- ✗ Service with <none> Endpoints
- ✗ Ingress with <pending> ADDRESS

**Commands to check first:**
```bash
kubectl get pods -n dev
kubectl get svc -n dev
kubectl get endpoints -n dev
```

**If any showing problems:**
→ Open K8S_PRODUCTION_TROUBLESHOOTING.md

**Find matching scenario (1-6) and follow step-by-step**

---

## ✅ SECTION 2: LINUX ISSUES

### When to Use LINUX_PRODUCTION_TROUBLESHOOTING.md

**Use if:**
- Pods running ✓
- Services working ✓
- BUT: System slow / unresponsive / errors

**Commands to check first:**
```bash
ssh ubuntu@<node-ip>
top -b -n 1         # CPU > 80%?
free -h             # Memory < 500MB?
df -h /             # Disk > 90%?
dmesg | tail -20    # Errors?
```

**If any showing problems:**
→ Open LINUX_PRODUCTION_TROUBLESHOOTING.md

**Find matching scenario (1-6) and follow step-by-step**

---

## ✅ SECTION 3: ISOLATION PROCESS

### Using CROSS_ENVIRONMENT_TROUBLESHOOTING.md

**When to use:** You don't know WHERE the problem is

**Step 1: K8s Check (3 minutes)**
```bash
kubectl get all -n dev
kubectl get endpoints -n dev
kubectl top pods -n dev
```

**Step 2: Linux Check (3 minutes)**
```bash
ssh ubuntu@<node-ip>
top -b -n 1
free -h
df -h /
```

**Step 3: Application Check (3 minutes)**
```bash
kubectl logs <pod> -n dev --tail=50
kubectl exec <pod> -n dev -- curl localhost:8000/health
```

**Result: Problem isolated to one area**
→ Use specific guide (K8s or Linux)

---

## ✅ SECTION 4: QUICK COMMANDS

### Using QUICK_COMMANDS_REFERENCE.md

**When to use:** You need a command to run

**Find your scenario:**
- Pod failing → "Pod Deep Dive" section
- Database not accessible → "Database Check" section
- System slow → "Performance diagnosis" section
- Everything down → "Emergency responses" section

**Copy-paste the commands and run**

---

## 📋 COMPLETE CHECKLIST

Use this to systematically eliminate possibilities:

```
☐ LEVEL 1: KUBERNETES (2 minutes)
  ☐ kubectl get pods → Any not Running?
  ☐ kubectl get svc → Service exists?
  ☐ kubectl get endpoints → Service has endpoints?
  ☐ kubectl top pods → Resources under limit?
  
  Result:
  ✓ All healthy → Go to Level 2
  ✗ Issue found → K8S_PRODUCTION_TROUBLESHOOTING.md

☐ LEVEL 2: LINUX (3 minutes)
  SSH to node:
  ☐ top -b -n 1 → CPU < 80%?
  ☐ free -h → Memory > 500MB?
  ☐ df -h / → Disk < 85%?
  ☐ dmesg | tail → Any errors?
  
  Result:
  ✓ All healthy → Go to Level 3
  ✗ Issue found → LINUX_PRODUCTION_TROUBLESHOOTING.md

☐ LEVEL 3: DATABASE (2 minutes)
  ☐ kubectl get pod (db) → Running?
  ☐ kubectl logs (db) → Any errors?
  ☐ kubectl exec → Can connect to DB?
  
  Result:
  ✓ All healthy → Go to Level 4
  ✗ Issue found → Check DB logs / LINUX guide

☐ LEVEL 4: APPLICATION (2 minutes)
  ☐ kubectl logs → Any errors?
  ☐ kubectl exec → curl localhost:8000/health
  ☐ Check DB connection → psql test
  
  Result:
  ✓ All healthy → Issue is external (user/network)
  ✗ Issue found → Fix application code

TOTAL TIME: ~10 minutes to isolate problem
```

---

## 🎓 HOW TO USE THESE GUIDES

### First Time Setup
1. Read CROSS_ENVIRONMENT_TROUBLESHOOTING.md (15 min)
   - Understand the isolation process
   - Learn the decision tree

2. Read K8S_PRODUCTION_TROUBLESHOOTING.md (20 min)
   - Understand K8s issues
   - Learn how to debug each scenario

3. Read LINUX_PRODUCTION_TROUBLESHOOTING.md (20 min)
   - Understand Linux issues
   - Learn how to debug each scenario

4. Bookmark QUICK_COMMANDS_REFERENCE.md
   - Use for daily reference

### When Problem Occurs
1. Open CROSS_ENVIRONMENT_TROUBLESHOOTING.md
   → Follow isolation process (10 min)

2. Open specific guide (K8s or Linux)
   → Find matching scenario (5 min)

3. Open QUICK_COMMANDS_REFERENCE.md
   → Copy-paste commands (1 min)

4. Apply fix and verify

---

## 📊 PROBLEM TO SOLUTION MATRIX

| Problem | Probable Cause | Guide | Time |
|---------|---|---|---|
| Website completely down | K8s Pod issues | K8S guide Scenario 1-3 | 10 min |
| Website slow | CPU or Memory high | LINUX guide Scenario 1-2 | 10 min |
| Pod crashing | App error or DB | K8S guide Scenario 3 + LINUX check | 15 min |
| Disk full | Log files not rotated | LINUX guide Scenario 3 | 5 min |
| DB connection refused | Too many connections | LINUX guide Scenario 4 | 10 min |
| Intermittent errors | Network or filesystem | CROSS_ENV guide + specific | 15 min |

---

## 🆘 EMERGENCY ESCALATION

**If after 10 minutes of these guides problem not found:**

1. Check recent deployments
   ```bash
   kubectl rollout history deployment employee-app -n dev
   ```

2. Rollback if recent change
   ```bash
   kubectl rollout undo deployment employee-app -n dev
   ```

3. Scale deployment down/up
   ```bash
   kubectl scale deployment employee-app --replicas=0 -n dev
   kubectl scale deployment employee-app --replicas=3 -n dev
   ```

4. Contact:
   - **K8s issue** → DevOps team
   - **Linux/Hardware** → System Admin team
   - **Database** → DBA team
   - **Application code** → Developer team

---

## 💡 KEY PRINCIPLES

1. **Always follow the order:** K8s → Linux → App
2. **Never skip levels** (saves time, prevents false leads)
3. **Use commands in order shown** (each builds on previous)
4. **Document what you find** (helps next person)
5. **When in doubt, check logs** (logs always tell the truth)

---

## 📞 FILE REFERENCE QUICK LINKS

- **K8s issues?** → K8S_PRODUCTION_TROUBLESHOOTING.md
- **Linux issues?** → LINUX_PRODUCTION_TROUBLESHOOTING.md
- **Don't know which?** → CROSS_ENVIRONMENT_TROUBLESHOOTING.md
- **Need a command?** → QUICK_COMMANDS_REFERENCE.md
- **Lost?** → This file (MASTER INDEX)

---

## ✨ YOU NOW HAVE

✅ 4 comprehensive troubleshooting guides (72 KB)
✅ 12 complete real scenarios with fixes
✅ 100+ copy-paste ready commands
✅ Decision trees and flowcharts
✅ Isolation process
✅ Emergency procedures
✅ Escalation guidelines

**Ready for production issues! 🚀**

