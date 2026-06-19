# 🔬 HANDS-ON LAB - LIVE TROUBLESHOOTING PRACTICE
## You run commands, I explain outputs, We learn together

---

## LAB SETUP

Your current environment:
```
Services running (or can be started):
- Jenkins: port 8080
- SonarQube: port 9000
- Docker Compose: Available
- Minikube/K8s: Available
- Employee Service: Available in K8s dev namespace
```

---

## LAB EXERCISE 1: DOCKER DIAGNOSTICS

### YOUR TASK: Check why your Docker containers aren't running

---

### EXERCISE 1.1: List All Containers

**YOU RUN:**
```bash
docker ps -a
```

**EXPECTED OUTPUT (you should see):**
```
CONTAINER ID   IMAGE                              COMMAND            STATUS                  PORTS                                         NAMES
1941d9195248   custom-jenkins:latest              "/usr/bin/tini..."  Exited (143) 2 days ago                                                jenkins
a4f0ecf2c0ab   sonarqube:community                "/opt/sonarqube..."  Exited (255) 5 days ago 0.0.0.0:9000->9000/tcp (since stopped)       sonarqube
48674a6034c2   gcr.io/k8s-minikube/kicbase:v0.0.50 "/usr/local/bin..."  Exited (130) 31m ago                                              minikube
```

---

**WHAT I'M TEACHING YOU TO READ:**

| Column | Meaning | Analysis |
|--------|---------|----------|
| CONTAINER ID | Unique ID | `1941d919...` = Jenkins |
| IMAGE | What's running | `custom-jenkins:latest` = Your custom image |
| COMMAND | Entry point | `/usr/bin/tini` = Init process |
| STATUS | Running state | `Exited (143)` = Stopped gracefully |
| PORTS | Network mapping | `9000->9000/tcp` = Port forwarding |
| NAMES | Friendly name | `jenkins` = Easy reference |

---

**YOUR INTERPRETATION:**

```
Question 1: Are these containers running?
Answer: NO - they all say "Exited"

Question 2: When did they stop?
Answer: Jenkins 2 days ago (143 = graceful), SonarQube 5 days ago (255 = error), Minikube 31 min ago

Question 3: What do the exit codes mean?
Answer:
  143 = SIGTERM (docker stop)
  255 = Error/Crash
  130 = Interrupted/Kill signal

Question 4: What should I do?
Answer: Start them with `docker-compose up -d`
```

---

### EXERCISE 1.2: Start the Services

**YOU RUN:**
```bash
docker-compose up -d
```

**EXPECTED OUTPUT:**
```
Creating network "docker_default" with the default driver
Creating jenkins ... done
Creating sonarqube ... done
```

---

### EXERCISE 1.3: Check Status Again

**YOU RUN:**
```bash
docker ps
```

**EXPECTED OUTPUT (should be different now):**
```
CONTAINER ID   IMAGE                    COMMAND                STATUS         PORTS                                       NAMES
1941d9195248   custom-jenkins:latest    "/usr/bin/tini..."     Up 45 seconds  0.0.0.0:8080->8080/tcp, 0.0.0.0:50000->...  jenkins
a4f0ecf2c0ab   sonarqube:community      "/opt/sonarqube..."    Up 30 seconds  0.0.0.0:9000->9000/tcp                     sonarqube
```

---

**WHAT'S DIFFERENT:**

```
BEFORE:  STATUS = Exited (143)
AFTER:   STATUS = Up 45 seconds

BEFORE:  PORTS = (empty)
AFTER:   PORTS = 0.0.0.0:8080->8080/tcp
```

**TEACHING POINT:** When containers run, they show `Up X seconds` and port mappings appear!

---

### EXERCISE 1.4: Monitor Resource Usage

**YOU RUN:**
```bash
docker stats --no-stream
```

**OUTPUT (snapshot of current usage):**
```
CONTAINER ID   NAME        CPU %     MEM USAGE / LIMIT    MEM %     NET I/O         BLOCK I/O         PIDS
1941d9195248   jenkins     15.3%     1.2G / 2G            60%       892MB / 1.3GB   450MB / 1.2GB     23
a4f0ecf2c0ab   sonarqube   8.5%      980M / 4G            24.5%     234MB / 567MB   123MB / 890MB     45
```

---

**INTERPRETATION:**

```
Jenkins:
- CPU: 15.3% ← Good, not maxed
- Memory: 1.2G / 2G = 60% used ← OK but trending high?
- Pids: 23 ← Normal (multiple Java threads)

SonarQube:
- CPU: 8.5% ← Good, reasonable
- Memory: 980M / 4G = 24.5% ← Healthy
- Pids: 45 ← More than Jenkins (Elasticsearch inside)
```

**TEACHING POINT:** Watch MEM USAGE trend over time:
- Stable = healthy
- Growing = memory leak
- Near LIMIT = about to crash

---

### EXERCISE 1.5: Check Container Logs

**YOU RUN:**
```bash
docker logs jenkins --tail=30
```

**OUTPUT (last 30 lines):**
```
2024-03-18 10:30:00,000 INFO  hudson.lifecycle: Jenkins initialization
2024-03-18 10:30:05,123 INFO  hudson.lifecycle: Jenkins is fully up and running
2024-03-18 10:30:10,456 INFO  hudson.tasks.Mailer: Checking email configuration
2024-03-18 10:30:15,789 INFO  hudson.plugins.git: Git plugin initialized
2024-03-18 10:30:20,123 INFO  winstone.Listener: Listening on HTTP port 8080
```

---

**INTERPRETATION:**

```
✓ No ERROR messages
✓ "fully up and running"
✓ "Listening on HTTP port 8080"

Conclusion: Jenkins healthy!
```

---

**IF YOU SAW ERRORS INSTEAD:**
```
ERROR: Port 8080 already in use
ERROR: OutOfMemoryError: Java heap space
ERROR: Failed to initialize plugins
```

**TEACHING POINT:** The error tells you exactly what to fix!

---

### EXERCISE 1.6: Test Connectivity

**YOU RUN:**
```bash
docker exec jenkins ping -c 3 sonarqube
```

**OUTPUT - GOOD (They can reach each other):**
```
PING sonarqube (172.18.0.2) 56(84) bytes of data.
64 bytes from sonarqube (172.18.0.2): icmp_seq=1 time=0.456 ms
64 bytes from sonarqube (172.18.0.2): icmp_seq=2 time=0.234 ms
64 bytes from sonarqube (172.18.0.2): icmp_seq=3 time=0.345 ms
--- sonarqube statistics ---
3 packets transmitted, 3 received, 0% packet loss
```

---

**OUTPUT - BAD (Can't reach):**
```
ping: unknown host
```

**TEACHING POINT:** If they can't reach each other:
- They're on different Docker networks
- Need to connect them: `docker network connect bridge sonarqube`

---

## LAB EXERCISE 2: KUBERNETES DIAGNOSTICS

### YOUR TASK: Check Kubernetes in dev namespace

---

### EXERCISE 2.1: List All Resources

**YOU RUN:**
```bash
kubectl get all -n dev
```

**OUTPUT:**
```
NAME                                    READY   STATUS    RESTARTS   AGE
pod/employee-app-5f4d8c9b2-xyz1a       1/1     Running   0          2d
pod/employee-app-5f4d8c9b2-xyz2b       1/1     Running   0          1d
pod/postgres-deployment-abc1234-xyz3d  1/1     Running   0          3d

NAME               TYPE       CLUSTER-IP      PORT(S)
service/employee-service  ClusterIP  10.96.0.50      8000/TCP
service/postgres-service  ClusterIP  10.96.0.200     5432/TCP

NAME                          DESIRED   CURRENT   UP-TO-DATE   AVAILABLE
deployment.apps/employee-app  2         2         2            2
deployment.apps/postgres      1         1         1            1
```

---

**INTERPRETATION:**

```
PODS:
- All show "1/1" (one container ready, one total)
- All show "Running" (not pending, not crashing)
- No high RESTARTS (not restarting)
✓ Pods healthy!

SERVICES:
- employee-service: ClusterIP 10.96.0.50
- postgres-service: ClusterIP 10.96.0.200
✓ Services created!

DEPLOYMENTS:
- DESIRED = CURRENT = AVAILABLE (all match!)
✓ Deployments at correct scale!
```

---

### EXERCISE 2.2: Check Service Endpoints

**YOU RUN:**
```bash
kubectl get endpoints -n dev
```

**OUTPUT - GOOD:**
```
NAME                ENDPOINTS
employee-service   10.0.1.100:8000,10.0.2.100:8000
postgres-service   10.0.1.150:5432
```

**What this means:**
- employee-service is connected to 2 Pods (10.0.1.100 and 10.0.2.100)
- postgres-service is connected to 1 Pod (10.0.1.150)
- ✓ Services have Pods behind them!

---

**OUTPUT - BAD:**
```
NAME                ENDPOINTS
employee-service   <none>
postgres-service   <none>
```

**What this means:**
- ❌ Services have NO Pods!
- ❌ Even if Pods running, they're not matching the service selector
- Fix: Add correct labels to Pods

---

### EXERCISE 2.3: Check Resource Usage

**YOU RUN:**
```bash
kubectl top pods -n dev
```

**OUTPUT:**
```
NAME                                    CPU(cores)   MEMORY(Mi)
employee-app-5f4d8c9b2-xyz1a           250m         340Mi
employee-app-5f4d8c9b2-xyz2b           280m         360Mi
postgres-deployment-abc1234-xyz3d      100m         210Mi
```

**INTERPRETATION:**

```
Employee App Pod 1:
- CPU: 250m (good, not high)
- Memory: 340Mi (check if growing!)

Employee App Pod 2:
- CPU: 280m (good)
- Memory: 360Mi (similar to pod 1, good)

PostgreSQL:
- CPU: 100m (light, expected)
- Memory: 210Mi (healthy)

All values reasonable. No resource problems.
```

---

### EXERCISE 2.4: Get Pod Details

**YOU RUN:**
```bash
kubectl describe pod employee-app-5f4d8c9b2-xyz1a -n dev
```

**OUTPUT (partial, important sections):**
```
Name:         employee-app-5f4d8c9b2-xyz1a
Namespace:    dev
Priority:     0
Node:         minikube
Status:       Running
IP:           10.0.1.100

Containers:
  employee-app:
    Container ID:  docker://abc123def456...
    Image:         raviteja21k/employee-service:15
    Image ID:      docker-pullable://raviteja21k/employee-service@sha256:xyz...
    Port:          8000/TCP
    State:         Running
      Started:     Sat, 17 Mar 2024 10:30:00 +0000
    Ready:         True
    Restart Count: 0
    Limits:
      cpu:     500m
      memory:  512Mi
    Requests:
      cpu:     100m
      memory:  128Mi

Events:
  Type    Reason     Age   From               Message
  ----    ------     ---   ----               -------
  Normal  Scheduled  2d    default-scheduler  Successfully assigned dev/employee-app-5f4d8c9b2-xyz1a to minikube
  Normal  Pulled     2d    kubelet            Container image pulled successfully
  Normal  Created    2d    kubelet            Created container employee-app
  Normal  Started    2d    kubelet            Started container employee-app
```

---

**INTERPRETATION:**

```
Status: Running ✓
Node: minikube ✓ (assigned to a node)
IP: 10.0.1.100 ✓ (has network address)

Image: raviteja21k/employee-service:15 ✓ (correct image)
Port: 8000/TCP ✓ (correct port)

Limits: CPU 500m, Memory 512Mi
Requests: CPU 100m, Memory 128Mi
→ Container has resource limits set ✓

Restart Count: 0 ✓ (not restarting)

Events: All "Normal" (no warnings) ✓
```

**Conclusion: Pod is healthy and well-configured!**

---

### EXERCISE 2.5: Check Pod Logs

**YOU RUN:**
```bash
kubectl logs employee-app-5f4d8c9b2-xyz1a -n dev --tail=50
```

**OUTPUT:**
```
2024-03-17 10:30:00 - [INFO] Starting FastAPI application
2024-03-17 10:30:05 - [INFO] Connected to database: postgres-service:5432
2024-03-17 10:30:10 - [INFO] Loading configuration from environment
2024-03-17 10:30:15 - [INFO] Server running on 0.0.0.0:8000
2024-03-17 10:30:20 - [INFO] /health endpoint responding
2024-03-17 10:30:25 - [INFO] Processing request: GET /employees
2024-03-17 10:30:26 - [INFO] Returned 42 employees
```

---

**INTERPRETATION:**

```
✓ Application started
✓ Database connected
✓ Server running on correct port
✓ Requests being processed
✓ No ERROR messages

Conclusion: Application is working!
```

---

## LAB EXERCISE 3: LINUX DIAGNOSTICS

### YOUR TASK: SSH to a Kubernetes node and check OS-level health

---

### EXERCISE 3.1: SSH to Node

**YOU RUN:**
```bash
ssh -i your-key.pem ubuntu@<node-ip>
```

**Then once inside:**

---

### EXERCISE 3.2: Check CPU

**YOU RUN:**
```bash
top -b -n 1 | head -10
```

**OUTPUT:**
```
top - 10:35:42 up 45 days, 2:15,  2 users,  load average: 0.45, 0.52, 0.48
Tasks:  98 total,   2 running,  96 sleeping,   0 stopped,   0 zombie
%Cpu(s):  15.2 us,   3.8 sy,   0.0 ni,  80.1 id,   0.5 wa,   0.2 hi,  0.2 si,  0.0 st

  PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND
    1 root      20   0  191456  12345   8345 S   0.1  0.2   1:23 systemd
   12 root      20   0 1234567 456789  23456 S   2.3  5.8   2:34 kubelet
  345 root      20   0  987654 234567  12345 S   1.2  3.0   1:23 docker
```

---

**WHAT TO READ:**

```
Load average: 0.45, 0.52, 0.48
├─ 1 min:  0.45 ← Current load
├─ 5 min:  0.52
└─ 15 min: 0.48
→ If you have 4 CPUs, < 4.0 is OK. 0.45 is GOOD.

CPU breakdown:
- us (user): 15.2% → Applications
- sy (system): 3.8% → Kernel
- id (idle): 80.1% → Not used (GOOD - means capacity available)
- wa (wait IO): 0.5% → Waiting on disk (low, good)

Conclusion: CPU HEALTHY!
```

---

### EXERCISE 3.3: Check Memory

**YOU RUN:**
```bash
free -h
```

**OUTPUT:**
```
              total        used        free      shared  buff/cache   available
Mem:          7.7Gi       2.3Gi       4.2Gi       87Mi       1.2Gi       4.5Gi
Swap:         2.0Gi       0.0Gi       2.0Gi
```

---

**WHAT TO READ:**

```
Mem total: 7.7Gi
├─ used: 2.3Gi (applications)
├─ free: 4.2Gi (completely free)
├─ available: 4.5Gi (can be freed from cache)
└─ buff/cache: 1.2Gi (disk cache, can be freed)

Swap: 2.0Gi
└─ used: 0.0Gi ← GOOD! (swapping to disk is slow)

Healthy ranges:
- free > 500MB ✓ (you have 4.2Gi)
- swap used ≈ 0 ✓ (you have 0.0Gi used)

Conclusion: MEMORY HEALTHY!
```

---

### EXERCISE 3.4: Check Disk

**YOU RUN:**
```bash
df -h
```

**OUTPUT:**
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/xvda1       20G   8.5G  11.5G 43%  /
/dev/xvdb1      100G   24G    76G   24%  /mnt/data
tmpfs           3.8G  0.1G   3.7G   2%  /dev/shm
```

---

**WHAT TO READ:**

```
Root (/) filesystem:
- Size: 20G
- Used: 8.5G
- Available: 11.5G
- Use%: 43% ← Healthy (< 85%)

Data partition:
- Size: 100G
- Used: 24G
- Available: 76G
- Use%: 24% ← Plenty of space

Temporary (tmpfs):
- Use%: 2% ← Normal

Healthy ranges:
- Use% < 85% ✓ (yours at 43%)
- Available > 10% ✓ (yours at 57%)

Conclusion: DISK SPACE HEALTHY!
```

---

### EXERCISE 3.5: Check for Errors

**YOU RUN:**
```bash
dmesg | tail -20
```

**OUTPUT - GOOD:**
```
[2024-03-18 10:00:00] kernel: audit: type=1400 apparmor="ALLOWED"
[2024-03-18 10:01:00] kernel: floppy0: no floppy controllers found
[2024-03-18 10:02:00] systemd[1]: Started Session c1 of user ubuntu.
```

**OUTPUT - BAD (Problem detected):**
```
[2024-03-18 09:30:00] kernel: Out of memory: Kill process 8765 (python) score 567
[2024-03-18 09:30:01] kernel: Killed process 8765 (python) total-vm:2456789kB
[2024-03-18 09:35:00] kernel: EXT4-fs error (device xvda1): bad entry in directory
```

---

**INTERPRETATION:**

```
GOOD scenario:
- No "Out of memory"
- No "ERROR"
- No "FATAL"
→ System healthy!

BAD scenario:
- "Out of memory" = OOM killer acting
- Filesystem errors = Corruption
→ NEEDS IMMEDIATE ATTENTION!
```

---

## LAB EXERCISE 4: COMPLETE ISOLATION PRACTICE

### YOUR TASK: Simulate a problem and troubleshoot through all layers

---

### SCENARIO: "Application is slow"

**STEP 1: Check Kubernetes (1 minute)**

```bash
# Command 1
kubectl get pods -n dev

# Command 2
kubectl get endpoints -n dev

# Command 3
kubectl top pods -n dev
```

**ANALYSIS:** If all show healthy → Move to Linux

---

**STEP 2: Check Linux (2 minutes)**

```bash
# SSH to node
ssh -i key.pem ubuntu@<node-ip>

# Command 1
top -b -n 1 | head -3

# Command 2
free -h

# Command 3
df -h /

# Command 4
dmesg | tail -10
```

**ANALYSIS:** If all show healthy → Move to Database

---

**STEP 3: Check Database (2 minutes)**

```bash
# From your local machine
kubectl exec employee-app-5f4d8c9b2-xyz1a -n dev -- \
  psql -h postgres-service -U employee_user -d employeedb -c "SELECT 1"

kubectl exec postgres-deployment-abc1234-xyz3d -n dev -- \
  psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

**ANALYSIS:** If all work → Move to Application

---

**STEP 4: Check Application (2 minutes)**

```bash
# Check logs
kubectl logs employee-app-5f4d8c9b2-xyz1a -n dev --tail=100

# Test health endpoint
kubectl exec employee-app-5f4d8c9b2-xyz1a -n dev -- \
  curl http://localhost:8000/health
```

**ANALYSIS:** If all healthy → Root cause found!

---

## 🎯 SUMMARY

You now have **real commands** to run on **your actual project** with **expected outputs** and **how to interpret them**.

Next steps:
1. Run each command
2. Compare your output to examples
3. Take notes of any differences
4. Report findings using the isolation flowchart

Let me know what you find! 🚀

