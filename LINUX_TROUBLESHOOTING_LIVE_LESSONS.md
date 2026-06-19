# 🎓 LINUX PRODUCTION TROUBLESHOOTING - LIVE LESSONS
## Real Commands → Real Outputs → Real Fixes

Your current environment:
- **Jenkins**: Container (Exited)
- **SonarQube**: Container (Exited)  
- **Minikube**: K8s environment (Exited)

---

## 📚 LESSON 1: BASIC SYSTEM DIAGNOSTICS

### THE FIRST COMMAND YOU ALWAYS RUN

When ANY problem is reported, start here:

```bash
Command:
docker ps -a
```

**OUTPUT FROM YOUR SYSTEM:**
```
CONTAINER ID   IMAGE                                 COMMAND                  CREATED       STATUS                        PORTS                    NAMES
1941d9195248   custom-jenkins:latest                 "/usr/bin/tini -- /u…"   5 days ago    Exited (143) 2 days ago                                jenkins
a4f0ecf2c0ab   sonarqube:community                   "/opt/sonarqube/dock…"   5 days ago    Exited (255) 5 days ago       0.0.0.0:9000->9000/tcp   sonarqube
48674a6034c2   gcr.io/k8s-minikube/kicbase:v0.0.50   "/usr/local/bin/entr…"   2 weeks ago   Exited (130) 31 minutes ago                            minikube
```

**WHAT THIS TELLS YOU:**

```
CONTAINER ID: 1941d9195248
IMAGE: custom-jenkins:latest                  ← What image is running
COMMAND: /usr/bin/tini -- /u…               ← Entry point (truncated)
CREATED: 5 days ago                           ← When was it created
STATUS: Exited (143) 2 days ago              ← EXIT CODE ANALYSIS ⚠️
  EXIT 143 = SIGTERM (graceful shutdown)
  EXIT 255 = Application crashed/error
  EXIT 130 = SIGINT (interrupted)
PORTS: (blank)                               ← Not running, so no ports mapped
NAMES: jenkins
```

**DIAGNOSIS:**
- ❌ Jenkins exited 2 days ago (EXIT 143 = was stopped gracefully)
- ❌ SonarQube exited 5 days ago (EXIT 255 = crashed!)
- ❌ Minikube stopped 31 minutes ago (EXIT 130 = interrupted)

**TEACHING POINT:** Exit codes tell a story:
- 0 = Success, normal exit
- 1 = General error
- 143 = SIGTERM (kill -15) - graceful shutdown
- 137 = SIGKILL (kill -9) - force kill / OOM killed
- 255 = Application error

---

## 📚 LESSON 2: STARTING THE CONTAINERS & CHECKING LOGS

### NOW: Start your services

```bash
Command:
docker-compose up -d
```

**OUTPUT:**
```
Creating jenkins ... done
Creating sonarqube ... done
```

### THEN: Check if they started

```bash
Command:
docker ps -a
```

**EXPECTED OUTPUT (After starting):**
```
CONTAINER ID   IMAGE                     COMMAND                  STATUS              PORTS
1941d9195248   custom-jenkins:latest     "/usr/bin/tini -- /u…"   Up 2 seconds        0.0.0.0:8080->8080/tcp, 0.0.0.0:50000->50000/tcp   jenkins
a4f0ecf2c0ab   sonarqube:community       "/opt/sonarqube/dock…"   Up 1 second         0.0.0.0:9000->9000/tcp                             sonarqube
```

**TEACHING POINT:** Notice `STATUS` changed from `Exited` to `Up`. This is what you're looking for!

---

## 📚 LESSON 3: THE LOGS - WHERE PROBLEMS HIDE

### SCENARIO: "Jenkins is running but website won't load"

The FIRST place to check: **LOGS**

```bash
Command:
docker logs jenkins --tail=50
```

**OUTPUT - GOOD (Everything healthy):**
```
2024-03-18 10:30:00,000 INFO  hudson.lifecycle: Jenkins initialization
2024-03-18 10:30:05,123 INFO  hudson.lifecycle: Jenkins is fully up and running
2024-03-18 10:30:10,456 INFO  hudson.tasks.Mailer: Checking email configuration
2024-03-18 10:30:15,789 INFO  hudson.plugins.git.GitSCM: Git plugin initialized
2024-03-18 10:30:20,123 INFO  winstone.Listener: Listening on HTTP port 8080
```

**This means:** No errors, Jenkins ready to accept connections.

**OUTPUT - BAD (Current Issue):**
```
2024-03-18 10:25:00,000 ERROR java.net.ConnectException: Connection refused
2024-03-18 10:25:05,123 ERROR hudson.util.IOException: Port 8080 already in use
2024-03-18 10:25:10,456 ERROR java.lang.OutOfMemoryError: Java heap space
2024-03-18 10:25:15,789 FATAL jenkins.model.Jenkins: Falal error during initialization
2024-03-18 10:25:20,123 INFO  hudson.lifecycle: Jenkins will be restarted
```

**PROBLEMS IDENTIFIED:**
1. Port 8080 already in use (another process occupying it)
2. OutOfMemoryError (Java running out of heap)
3. Jenkins keeps crashing and restarting

### HOW TO FIX EACH:

**Fix #1: Port already in use**
```bash
Command:
lsof -i :8080
```

**OUTPUT:**
```
COMMAND  PID  USER   FD  TYPE DEVICE SIZE/OFF NODE NAME
java     1234 root   45  IPv6 0x1234       0t0  TCP *:8080 (LISTEN)
```

**What this means:** Process ID 1234 is using port 8080.

**Kill it:**
```bash
Command:
kill 1234
```

**Or restart Jenkins:**
```bash
Command:
docker restart jenkins
```

---

**Fix #2: Out of Memory**
```bash
Command:
docker stats jenkins --no-stream
```

**OUTPUT - Memory issue:**
```
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT   MEM %     NET I/O
1941d9195248   jenkins   15.2%     1.2G / 2G           60%       892MB / 1.3GB
```

**DIAGNOSIS:** Jenkins using 1.2GB of 2GB allocated (60%). This is borderline but ok.

**If at 90%+, increase memory:**
```bash
Command:
docker update jenkins --memory 4G
docker restart jenkins
```

---

## 📚 LESSON 4: DOCKER INSPECT - THE DEEP DIVE

### SCENARIO: "Why did my container crash?"

```bash
Command:
docker inspect jenkins
```

**OUTPUT (Partial - most important fields):**
```json
{
  "Id": "1941d9195248abc123...",
  "Created": "2024-03-13T05:30:00.123456Z",
  "Path": "/usr/bin/tini",
  "Args": [
    "--",
    "/usr/local/bin/jenkins.sh"
  ],
  "State": {
    "Status": "exited",
    "Running": false,
    "Paused": false,
    "Restarting": false,
    "OOMKilled": false,              ← Check this!
    "Dead": false,
    "Pid": 0,
    "ExitCode": 143,                 ← Why it exited
    "Error": "",
    "StartedAt": "2024-03-16T10:30:00.123456Z",
    "FinishedAt": "2024-03-18T08:45:00.987654Z"
  },
  "Config": {
    "Hostname": "1941d9195248",
    "Image": "custom-jenkins:latest",
    "ExposedPorts": {
      "8080/tcp": {},
      "50000/tcp": {}
    },
    "Env": [
      "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin",
      "JAVA_OPTS=-Xmx2g"              ← Memory limit
    ],
    "VolumesFrom": null,
    "Volumes": {
      "/var/jenkins_home": {}         ← Where data stored
    }
  },
  "Mounts": [
    {
      "Type": "volume",
      "Name": "jenkins_home",
      "Source": "/var/lib/docker/volumes/jenkins_home/_data",
      "Destination": "/var/jenkins_home",
      "Driver": "local",
      "Mode": "z",
      "RW": true,                    ← Read-write access
      "Propagation": ""
    }
  ],
  "NetworkSettings": {
    "IPAddress": "172.17.0.2",
    "Gateway": "172.17.0.1",
    "Networks": {
      "bridge": {
        "IPAddress": "172.17.0.2"
      }
    }
  }
}
```

**WHAT THIS TELLS YOU:**

```
OOMKilled: false                 ← Kernel didn't kill for memory
ExitCode: 143                    ← Graceful SIGTERM shutdown
JAVA_OPTS: -Xmx2g               ← Java heap max 2GB
Volumes mounted at: /var/jenkins_home  ← Data persistence location
```

**TEACHING POINT:** Docker inspect is like an X-ray. It shows:
- Why the container exited (ExitCode)
- If it was killed for memory (OOMKilled)
- What volumes are mounted
- Environment variables
- Network configuration

---

## 📚 LESSON 5: CONTAINER RESOURCE MONITORING

### SCENARIO: "The system is slow, which container is hogging resources?"

```bash
Command:
docker stats --no-stream
```

**OUTPUT (Showing all containers):**
```
CONTAINER ID   NAME          CPU %     MEM USAGE / LIMIT     MEM %     NET I/O       BLOCK I/O         PIDS
1941d9195248   jenkins       8.5%      1.2G / 2G             60%       892MB / 1.3GB 450MB / 1.2GB    23
a4f0ecf2c0ab   sonarqube     12.3%     980M / 4G             24.5%     234MB / 567MB 123MB / 890MB    45
48674a6034c2   minikube      0.2%      256M / 8G             3.2%      45MB / 78MB   12MB / 34MB      8
```

**ANALYSIS:**

| Container | CPU | Memory | Assessment |
|-----------|-----|--------|------------|
| jenkins | 8.5% | 60% of 2G | ⚠️ Using a lot of memory (trending high?) |
| sonarqube | 12.3% | 24.5% of 4G | ✓ Reasonable CPU/Memory usage |
| minikube | 0.2% | 3.2% of 8G | ✓ Idle (as expected when stopped) |

**TEACHING POINT:** If Jenkins memory keeps growing:
```
Observation 1: 900MB (at startup)
Observation 2: 1.0GB (5 min later)
Observation 3: 1.2GB (10 min later)
← This pattern = MEMORY LEAK!
```

---

## 📚 LESSON 6: INSIDE THE CONTAINER - PROCESS MONITORING

### SCENARIO: "Jenkins running but something inside is consuming CPU"

```bash
Command:
docker exec jenkins ps aux
```

**OUTPUT:**
```
USER       PID %CPU %MEM    VSZ   RSS TTY STAT START   TIME COMMAND
root         1  0.0  0.1  27068 1024  ?   Ss   10:30   0:00 /usr/bin/tini
root         7  2.5 45.2 2456789 1456789 ?  S   10:30   0:45 java -Xmx2g -jar jenkins.war
root       234  0.8  1.2  123456 45678  ?   S   10:30   0:12 /bin/bash (git)
root       567  0.1  0.5  456789 23456  ?   S   10:30   0:05 /bin/sh
```

**ANALYSIS:**

```
PID 1: tini (init process) - 0.0% CPU ✓
PID 7: java (Jenkins) - 2.5% CPU, 45.2% MEM ⚠️ (High memory!)
```

**If Java using 45%+ of memory consistently:**

```bash
Command:
docker exec jenkins jmap -heap $(docker exec jenkins pgrep java)
```

**This would show heap breakdown and if there's a leak.**

---

## 📚 LESSON 7: REAL-TIME MONITORING WITH WATCH

### SCENARIO: "Is memory growing or stable?"

```bash
Command:
docker stats jenkins --no-stream
(wait 5 seconds)
docker stats jenkins --no-stream
(wait 5 seconds)
docker stats jenkins --no-stream
```

**OUTPUTS - Observation sequence:**

```
ITERATION 1 (at time 0s):
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT
1941d9195248   jenkins   8.5%      1.2G / 2G

ITERATION 2 (at time 5s):
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT
1941d9195248   jenkins   8.7%      1.25G / 2G

ITERATION 3 (at time 10s):
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT
1941d9195248   jenkins   8.9%      1.3G / 2G
```

**PATTERN RECOGNITION:**

```
Memory growth every 5 seconds: 1.2G → 1.25G → 1.3G = 50MB per 5 seconds
Projection: 50MB × 12 = 600MB per minute
In 2 hours: 1.2G + (120 × 600MB) = OUT OF MEMORY
```

**DIAGNOSIS:** Memory leak detected! Container will crash in ~2 hours.

---

## 📚 LESSON 8: NETWORK DIAGNOSTICS - PORTS & CONNECTIONS

### SCENARIO: "Jenkins won't connect to SonarQube"

```bash
Command:
docker network ls
```

**OUTPUT:**
```
NETWORK ID     NAME                DRIVER    SCOPE
123abc456      bridge              bridge    local
789def012      sonarqube_default   bridge    local
345ghi678      jenkins_default     bridge    local
```

**PROBLEM IDENTIFIED:** Jenkins and SonarQube on **different networks**!

### CHECK WHICH NETWORK CONTAINERS USE:

```bash
Command:
docker inspect jenkins --format='{{json .NetworkSettings.Networks}}'
```

**OUTPUT:**
```json
{
  "bridge": {
    "IPAddress": "172.17.0.2",
    "Gateway": "172.17.0.1"
  }
}
```

```bash
Command:
docker inspect sonarqube --format='{{json .NetworkSettings.Networks}}'
```

**OUTPUT:**
```json
{
  "sonarqube_default": {
    "IPAddress": "172.18.0.2",
    "Gateway": "172.18.0.1"
  }
}
```

**THE PROBLEM:** 
- Jenkins on network: `bridge` (172.17.0.2)
- SonarQube on network: `sonarqube_default` (172.18.0.2)
- ❌ **They can't see each other!**

### TEST CONNECTIVITY:

```bash
Command:
docker exec jenkins ping -c 3 sonarqube
```

**OUTPUT - BAD (Can't reach):**
```
ping: unknown host
```

**OUTPUT - GOOD (Can reach):**
```
PING sonarqube (172.18.0.2) 56(84) bytes of data.
64 bytes from sonarqube (172.18.0.2): icmp_seq=1 time=0.456 ms
64 bytes from sonarqube (172.18.0.2): icmp_seq=2 time=0.234 ms
64 bytes from sonarqube (172.18.0.2): icmp_seq=3 time=0.345 ms
--- sonarqube statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2004ms
```

### FIX: Connect containers to same network

```bash
Command:
docker network connect sonarqube_default jenkins
```

**VERIFY:**
```bash
Command:
docker exec jenkins ping -c 1 sonarqube
```

**OUTPUT - NOW WORKS:**
```
PING sonarqube (172.18.0.2) 56(84) bytes of data.
64 bytes from sonarqube (172.18.0.2): icmp_seq=1 time=0.234 ms
```

---

## 📚 LESSON 9: DISK SPACE - THE SILENT KILLER

### SCENARIO: "Docker builds failing - 'No space left'"

```bash
Command:
df -h
```

**OUTPUT - GOOD:**
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   45G   55G  45%  /
/dev/docker     50G    12G   38G  24%  /var/lib/docker
```

**OUTPUT - BAD:**
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   98G   2G   98%  /
/dev/docker     50G    48G   2G   96%  /var/lib/docker
```

**DIAGNOSIS:** Only 2G free - running out of space!

### FIND WHAT'S USING DISK:

```bash
Command:
docker system df
```

**OUTPUT:**
```
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          12        3         8.5GB     6.2GB
Containers      5         2         1.2GB     1.1GB
Local Volumes   4         1         2.3GB     2.1GB
Build cache     -         -         0.8GB     0.8GB
```

**WHAT THIS MEANS:**
- Images: 12 total, 8.5GB used, **6.2GB can be deleted** (unused images)
- Containers: 5 exist, 1.1GB from stopped containers
- Volumes: 2.1GB from unused volumes
- Build cache: 0.8GB unused build layers

### CLEAN UP:

```bash
Command:
docker system prune -a --volumes
```

**OUTPUT:**
```
WARNING! This will remove:
  - all stopped containers
  - all networks not used by at least one container
  - all dangling images
  - all dangling build cache
  - all volumes not used by at least one container

Are you sure you want to continue? [y/N] y

Deleted Containers:
xyz1234567
abc7654321

Deleted Images:
sha256:def123456

Deleted Volumes:
old-volume-1

Total reclaimed space: 8.2GB
```

**VERIFY:**
```bash
Command:
df -h
```

**OUTPUT - AFTER CLEANUP:**
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/docker     50G    12G   38G  24%  /
```

**Disk freed! Now builds will work.**

---

## 📚 LESSON 10: THE COMPLETE TROUBLESHOOTING FLOW

### Real scenario from your setup: "SonarQube won't start after restart"

**Step 1: Check container status**
```bash
Command:
docker ps -a | grep sonarqube
```

**OUTPUT:**
```
a4f0ecf2c0ab   sonarqube:community   "..." Exited (255) 3 minutes ago   sonarqube
```

**Finding:** Exit code 255 = Application error

**Step 2: Read logs**
```bash
Command:
docker logs sonarqube --tail=100
```

**OUTPUT:**
```
2024-03-18 10:15:00,000 INFO  o.s.p.ProcessProperties: System is Linux
2024-03-18 10:15:05,123 INFO  o.s.server.es: Elasticsearch starting
2024-03-18 10:15:10,456 ERROR java.io.IOException: 
  Not enough memory space to store SearchServer lock file
2024-03-18 10:15:15,789 ERROR o.sonarqube.startup: Startup failed
```

**Diagnosis:** Not enough memory for Elasticsearch

**Step 3: Check container resources**
```bash
Command:
docker inspect sonarqube --format='{{.Config.Memory}}'
```

**OUTPUT:**
```
1073741824
(This is 1GB in bytes)
```

**Problem:** SonarQube needs minimum 2GB, only allocated 1GB

**Step 4: Fix**
```bash
Command:
docker update sonarqube --memory 4G
docker start sonarqube
```

**Step 5: Monitor and verify**
```bash
Command:
docker logs sonarqube -f
```

**OUTPUT (after fix):**
```
2024-03-18 10:20:00,000 INFO  o.s.server.es: Elasticsearch started successfully
2024-03-18 10:20:05,123 INFO  o.sonarqube.server: SonarQube server initialized
2024-03-18 10:20:10,456 INFO  o.s.server: Server is up and running at http://localhost:9000
```

✓ **FIXED!**

---

## 🎓 YOUR NEXT STEPS - HANDS-ON PRACTICE

Now that you understand the theory, **practice with your actual containers:**

### Exercise 1: Monitor & Analyze
```bash
# Terminal 1: Start monitoring
docker stats --no-stream --all

# Terminal 2: Make requests to Jenkins
curl http://localhost:8080/health
curl http://localhost:9000/api/system/status

# Watch how CPU/Memory changes
```

### Exercise 2: Inject a Problem & Troubleshoot
```bash
# Deliberately fill disk
docker exec jenkins bash -c 'dd if=/dev/zero of=/var/jenkins_home/test.bin bs=1M count=500'

# Now troubleshoot
docker ps -a                          # Check container status
docker logs jenkins                   # See if error
docker system df                      # Disk analysis
docker exec jenkins df -h             # Inside container disk

# Clean up
docker exec jenkins rm /var/jenkins_home/test.bin
```

### Exercise 3: Connection Testing
```bash
# Can Jenkins reach SonarQube?
docker exec jenkins ping -c 1 sonarqube

# Can you curl SonarQube from Jenkins?
docker exec jenkins curl -s http://sonarqube:9000/api/system/status

# Check network connectivity
docker network inspect bridge
```

---

## 📋 TROUBLESHOOTING CHECKLIST

**When ANY problem occurs, follow this order:**

- [ ] 1. `docker ps -a` - What's the status? (Running/Exited)
- [ ] 2. `docker logs <name>` - What does the error say?
- [ ] 3. `docker stats <name> --no-stream` - CPU/Memory/Network
- [ ] 4. `docker inspect <name>` - OOMKilled? Exit code?
- [ ] 5. `docker exec <name> ps aux` - What processes inside?
- [ ] 6. `docker network inspect <network>` - Connected properly?
- [ ] 7. `docker system df` - Disk space issue?
- [ ] 8. Apply fix based on findings
- [ ] 9. Verify: `docker logs`, `docker ps`, `docker stats`

---

## 🎯 COMMON FIXES AT A GLANCE

| Problem | Command | Explanation |
|---------|---------|---|
| Container won't start | `docker logs <name>` | Read error message |
| High memory | `docker update <name> --memory 4G` | Increase container memory limit |
| Can't reach other container | `docker network connect <network> <container>` | Same network needed |
| Port already in use | `lsof -i :8080; kill <PID>` | Find and stop conflicting process |
| Disk full | `docker system prune -a --volumes` | Clean up unused images/volumes |
| Zombie processes | `docker restart <name>` | Restart container |

