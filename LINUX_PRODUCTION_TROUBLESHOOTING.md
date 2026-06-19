# 🐧 LINUX PRODUCTION TROUBLESHOOTING
## Real Scenarios • Actual Commands • Real Outputs • Step-by-Step Fixes

### WHEN TO USE THIS GUIDE
**K8s verified healthy** → Pods running, services working → **Issue must be Linux-level**

---

## 🎯 QUICK DECISION TREE

```
K8s looks good ✓
└─ Issue must be OS-level
   ├─ CPU/Memory problem?
   ├─ Disk/Filesystem issue?
   ├─ Network connectivity?
   ├─ Process/Service problem?
   ├─ Security/Permissions?
   └─ File system corruption?
```

---

## SCENARIO 1: HIGH CPU - APP SLOW OR HANGING

### ⚠️ ISSUE
Users report: "Website is very slow"
K8s check: All Pods running ✓

### 🔍 WHAT TO CHECK

**Step 1: Check Overall System CPU**
```bash
top -b -n 1
```

**OUTPUT - GOOD:**
```
top - 10:35:42 up 45 days, 2:15,  2 users,  load average: 0.45, 0.52, 0.48
Tasks:  98 total,   2 running,  96 sleeping,   0 stopped,   0 zombie
%Cpu(s):  15.2 us,   3.8 sy,   0.0 ni,  80.1 id,   0.5 wa,   0.2 hi,  0.2 si,  0.0 st
MiB Mem :   7932.0 total,  3456.0 free,  2789.0 used,  1687.0 buff/cache
MiB Swap:   2048.0 total,  2048.0 free,     0.0 used.  4321.0 avail Mem

PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND
5432 ubuntu   20   0 1234567 456789  23456 S  8.5  5.8   2:34.56 python
2345 ubuntu   20   0  456789 234567  12345 S  6.2  3.0   1:23.45 postgres
```

**OUTPUT - BAD (Current Issue):**
```
top - 10:35:42 up 5 days, 0:15,  1 user,  load average: 8.5, 7.2, 6.8
Tasks: 120 total,   5 running, 115 sleeping,  0 stopped,  0 zombie
%Cpu(s):  95.2 us,   4.1 sy,   0.0 ni,   0.5 id,   0.1 wa,  0.1 hi,  0.0 si,  0.0 st
MiB Mem :   7932.0 total,   234.0 free,  7500.0 used,   198.0 buff/cache
MiB Swap:   2048.0 total,  1024.0 free,  1024.0 used.     45.0 avail Mem

PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND
8765 ubuntu   20   0 2456789 1897654 45678 R 95.2 24.0  45:23.12 python
1234 ubuntu   20   0  987654  567890 34567 R 82.3 7.2   32:15.89 postgres
```

**DIAGNOSIS:**
- ❌ CPU usage: 95.2% (should be < 30%)
- ❌ Load average: 8.5 (way too high)
- ❌ python process using 95% CPU
- ❌ Very low free memory (234MB)

**Step 2: Find the Problematic Process**
```bash
ps aux --sort=-%cpu | head -10
```

**OUTPUT:**
```
USER       PID %CPU %MEM    VSZ   RSS TTY STAT START   TIME COMMAND
ubuntu    8765 95.2 24.0 2456789 1897654 ?  R  10:00  45:23 python /app/main.py
ubuntu    1234 82.3 7.2  987654 567890  ?  S  09:45  32:15 /usr/lib/postgresql/bin/postgres
ubuntu    5432 8.5 5.8  1234567 456789  ?  S  08:30  2:34 python -m uvicorn app.main:app
root      1     0.1 0.2  191456  12345  ?  S  Jun15   1:23 /sbin/init
```

**PROBLEM:** python (PID 8765) consuming 95% CPU

**Step 3: Get Process Details**
```bash
cat /proc/8765/cmdline | tr '\0' ' '; echo
```

**OUTPUT:**
```
/usr/bin/python3 /app/main.py
```

**Step 4: Check for Infinite Loops or Busy Code**
```bash
strace -c -p 8765 2>&1 | head -30
```

**OUTPUT - Sample:**
```
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
 45.32    1.234567        45678     23456         select
 32.15     0.876543        21098     43210         epoll_wait
 15.23     0.415789        8934      52341         write
  5.12     0.139876        1234      113456       read
  2.18     0.059876        23        2634         mmap
```

**PROBLEM:** Massive amount of syscalls, indicates busy loop or bad code

**Step 5: Check Which Python Method is Hogging CPU**
```bash
top -p 8765 -H
```

**OUTPUT:**
```
top - 10:45:22 up 5 days, 0:25,  1 user,  load average: 8.2, 7.5, 7.1
Threads:  12 total,   5 running,   7 sleeping,   0 stopped,  0 zombie
%Cpu(s): 94.8 us,   4.2 sy,   0.0 ni,   0.8 id,   0.2 wa,  0.0 hi,  0.0 si,  0.0 st

PID   PPID TID %CPU %MEM     TIME+ S COMMAND
8765  8765  8765 28.3 24.0  12:34.56 R python3
8765  8765  8766 27.9 24.0  11:45.23 R python3
8765  8765  8767 26.5 24.0  11:23.45 R python3
8765  8765  8768 11.2 24.0   5:12.34 R python3
8765  8765  8769  0.4 24.0   0:23.45 S python3
```

**Multiple threads spinning! Indicates infinite loop in code**

### ✅ FIX: Identify Infinite Loop

**Step 1: Get Process Stack Trace**
```bash
gdb -batch -ex "thread apply all bt" -p 8765 2>/dev/null | head -50
```

**OUTPUT - Showing Infinite Loop:**
```
Thread 1 (Thread 0x7fff8a123400 (LWP 8765)):
#0  0x00007f1234567890 in process_employees (data=0x7fff8a000000) at /app/routes/employees.py:45
#1  0x00007f1234567800 in handle_request (request=0x7fff8a111111) at /app/main.py:120
#2  0x00007f1234567700 in uvicorn_handler () at /usr/lib/python3.9/site-packages/uvicorn/server.py:256
```

**Issue at `/app/routes/employees.py:45`**

**Step 2: Check the Code**
```bash
sed -n '40,50p' /app/routes/employees.py
```

**OUTPUT:**
```
40:  def process_employees(data):
41:      results = []
42:      while True:                    ← ⚠️ INFINITE LOOP!
43:          for employee in data:
44:              results.append(employee)
45:              # Missing break condition
46:          if not results:
47:              break
48:  return results
```

### ✅ SOLUTION: Fix Code

**Update Code:**
```bash
cat > /app/routes/employees.py << 'EOF'
def process_employees(data):
    results = []
    for employee in data:                # ← Fixed: removed while True
        results.append(employee)
    return results
EOF
```

**Restart Application (via K8s):**
```bash
kubectl rollout restart deployment employee-app -n dev
```

**VERIFY CPU RETURNS TO NORMAL:**
```bash
top -b -n 1 | head -3
```

**OUTPUT - FIXED:**
```
top - 10:50:42 up 5 days, 0:30,  1 user,  load average: 0.45, 0.52, 0.48
Tasks:  95 total,   1 running,  94 sleeping,   0 stopped,  0 zombie
%Cpu(s):  12.2 us,   2.8 sy,   0.0 ni,  84.5 id,   0.3 wa,  0.2 hi,  0.0 si,  0.0 st
```

---

## SCENARIO 2: OUT OF MEMORY - OOM KILLER

### ⚠️ ISSUE
System suddenly becomes unresponsive
Processes killed abruptly

### 🔍 WHAT TO CHECK

**Step 1: Check Available Memory**
```bash
free -h
```

**OUTPUT - BAD:**
```
              total        used        free      shared  buff/cache   available
Mem:          7.7Gi       7.4Gi       234Mi       98Mi       123Mi        156Mi
Swap:         2.0Gi       1.8Gi       187Mi
```

**PROBLEM:**
- ❌ Free memory: 234MB (should be > 1GB)
- ❌ Swap used: 1.8GB (high disk I/O penalty)
- ❌ Available: 156MB (very low!)

**Step 2: See What's Using Memory**
```bash
ps aux --sort=-%mem | head -5
```

**OUTPUT:**
```
USER       PID %CPU %MEM    VSZ   RSS TTY STAT START   TIME COMMAND
ubuntu    8765  8.5 67.2 2456789 5234567 ?  S  10:00  2:34 /usr/bin/python3 /app/main.py
ubuntu    1234  2.3 12.4  987654 987654  ?  S  09:45  1:23 /usr/lib/postgresql/bin/postgres
ubuntu    5432  1.2 5.8   1234567 456789  ?  S  08:30  0:45 /usr/sbin/nginx
root       989  0.1 2.1   234567  167890 ?  S  08:00  0:12 /usr/bin/kubelet
```

**DIAGNOSIS:**
- Python app: 67.2% of RAM (5.2 GB!)
- Should use max 20-30% (1.5-2.3 GB)
- ❌ Memory leak in application

**Step 3: Check for OOM Events**
```bash
dmesg | grep -i "out of memory" | tail -20
```

**OUTPUT:**
```
[3456.234567] Out of memory: Kill process 8765 (python) score 567 or sacrifice child
[3456.234568] Killed process 8765 (python) total-vm:2456789kB, anon-rss:5234567kB, file-rss:45678kB, shmem-rss:98765kB, UID:1000 pgtables:12345kB
[3457.123456] kswapd0: page allocation stalled for 45000ms, order:0, mode:0x26420ca(GFP_TEMPORARY), nodemask=(null)
```

**Confirmed:** Kernel killed process due to OOM

**Step 4: Analyze Memory Growth**
```bash
watch -n 5 'ps aux | grep python | grep -v grep'
```

**OUTPUT - Over Time:**
```
Every 5.0s: ps aux | grep python | grep -v grep

10:50:42: ubuntu 8765 2.5 15.2 ... 1201234 ? S
10:50:47: ubuntu 8765 2.6 18.5 ... 1456789 ? S
10:50:52: ubuntu 8765 2.7 21.3 ... 1689876 ? S
10:50:57: ubuntu 8765 2.9 25.7 ... 2034567 ? S
```

**PATTERN:** Memory growing 5% every 5 seconds → Memory leak!

### ✅ FIX: Find Memory Leak

**Use Memory Profiler:**
```bash
pip install memory-profiler
python -m memory_profiler /app/main.py
```

**OUTPUT - Showing Leak:**
```
Line #    Mem usage    Increment   Line Contents
================================================
    15    39.2 MiB     0.0 MiB   @profile
    16    39.2 MiB     0.0 MiB   def fetch_employees():
    17    39.2 MiB     0.0 MiB       employees = []
    18    39.2 MiB     0.0 MiB       for i in range(100000):
    19    45.8 MiB     6.6 MiB           emp_dict = {}
    20    89.4 MiB    43.6 MiB           emp_dict['data'] = get_large_data()  ← LEAK HERE!
    21    89.4 MiB     0.0 MiB           employees.append(emp_dict)
    22    89.4 MiB     0.0 MiB       return employees  ← Never freed!
```

**Issue:** Large data not freed after function ends

**Fix Code:**
```python
# BAD (leaks memory):
def fetch_employees():
    employees = []
    for i in range(100000):
        emp_dict = {}
        emp_dict['data'] = get_large_data()
        employees.append(emp_dict)
    return employees

# GOOD (properly managed):
def fetch_employees():
    for i in range(100000):
        emp_dict = {}
        emp_dict['data'] = get_large_data()
        yield emp_dict  # ← Generator: memory freed after use
        del emp_dict
```

**Restart App:**
```bash
kubectl rollout restart deployment employee-app -n dev
```

**VERIFY MEMORY NORMAL:**
```bash
watch -n 10 'free -h | grep Mem'
```

**OUTPUT - FIXED:**
```
Mem:          7.7Gi       2.3Gi       4.2Gi       87Mi       1.2Gi       4.5Gi
```

---

## SCENARIO 3: DISK FULL - NO SPACE LEFT

### ⚠️ ISSUE
Application can't write files
Error: "No space left on device"

### 🔍 WHAT TO CHECK

**Step 1: Check Disk Usage**
```bash
df -h
```

**OUTPUT - BAD:**
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/xvda1       20G   20G   0G 100% /
/dev/xvdb1      100G   95G  4.8G 95% /mnt/data
tmpfs           3.8G  3.8G    0G 100% /dev/shm
```

**PROBLEM:**
- ❌ Root (/) at 100% - NO SPACE!
- ❌ /mnt/data at 95% - nearly full
- ❌ tmpfs at 100% - shared memory full

**Step 2: Find What's Using Disk**
```bash
du -sh /* 2>/dev/null | sort -hr | head -10
```

**OUTPUT:**
```
12G     /var
5.6G    /home
1.2G    /opt
456M    /tmp
234M    /usr
123M    /app
45M     /etc
```

**Problem:** `/var` using 12GB (likely logs!)

**Step 3: Find Large Log Files**
```bash
find /var -type f -size +100M 2>/dev/null | sort -k5 -hr
```

**OUTPUT:**
```
/var/log/syslog                          4.2G    size    Mar 18 10:30
/var/log/auth.log                        3.1G    size    Mar 18 10:25
/var/log/nginx/access.log               2.8G    size    Mar 18 10:20
/var/log/nginx/error.log                1.5G    size    Mar 18 10:15
```

**ROOT CAUSE:** Massive log files not rotated

**Step 4: Check Log Rotation Config**
```bash
cat /etc/logrotate.d/nginx
```

**OUTPUT - BAD:**
```
/var/log/nginx/*.log {
    daily
    missingok
    rotate 365      ← Keeps 365 days! Way too much
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
}
```

### ✅ FIX: Clean Logs

**Option 1: Emergency - Truncate Logs**
```bash
sudo truncate -s 0 /var/log/syslog
sudo truncate -s 0 /var/log/auth.log
sudo truncate -s 0 /var/log/nginx/access.log
```

**VERIFY:**
```bash
df -h /
```

**OUTPUT - After Truncate:**
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/xvda1       20G   4.1G  16G  21% /
```

**Option 2: Proper Fix - Update Log Rotation**
```bash
cat > /etc/logrotate.d/nginx << 'EOF'
/var/log/nginx/*.log {
    daily
    missingok
    rotate 7              ← Keep only 7 days
    maxage 30            ← Delete after 30 days
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        if [ -f /var/run/nginx.pid ]; then
            kill -USR1 `cat /var/run/nginx.pid`
        fi
    endscript
}
EOF
```

**Test Rotation:**
```bash
logrotate -f /etc/logrotate.d/nginx
```

**Verify:**
```bash
ls -lh /var/log/nginx/
```

**OUTPUT - After Rotation:**
```
-rw-r--r-- 1 www-data adm   45M Mar 18 10:30 access.log
-rw-r--r-- 1 www-data adm   12M Mar 18 10:00 access.log.1.gz
-rw-r--r-- 1 www-data adm    8M Mar 17 23:00 access.log.2.gz
```

---

## SCENARIO 4: DATABASE CONNECTION ISSUES

### ⚠️ ISSUE
App errors: "too many connections"
Database slowly responding

### 🔍 WHAT TO CHECK

**Step 1: Check PostgreSQL Processes**
```bash
ps aux | grep postgres
```

**OUTPUT - BAD:**
```
postgres  1234  0.2 12.4  987654 987654  ?  S  09:45  1:23 /usr/lib/postgresql/bin/postgres
postgres  1245  0.1  0.5  345678 45678   ?  S  09:46  0:12 postgres: ubuntu db1 idle
postgres  1246  0.2  0.5  345678 45678   ?  S  09:47  0:15 postgres: ubuntu db1 idle
postgres  1247  0.1  0.4  345678 34567   ?  S  09:48  0:10 postgres: ubuntu db1 idle
... (many more)
```

**Step 2: Check Active Connections**
```bash
psql -U postgres -d postgres -c \
  "SELECT count(*) as connection_count FROM pg_stat_activity;"
```

**OUTPUT - BAD:**
```
 connection_count
------------------
              195
```

**PROBLEM:** 195 connections (normal is 10-50)

**Step 3: Find Connection Hogs**
```bash
psql -U postgres -d postgres -c \
  "SELECT usename, count(*) as connections 
   FROM pg_stat_activity 
   GROUP BY usename 
   ORDER BY connections DESC;"
```

**OUTPUT:**
```
  usename  | connections
-----------+-------------
 app_user  |         150
 admin     |          30
 monitor   |          10
 postgres  |           5
```

**DIAGNOSIS:** app_user has 150 connections (connection leak!)

**Step 4: Check Connection Pool Config**
```bash
ps aux | grep sqlalchemy
cat /app/config.py | grep -i pool
```

**OUTPUT - BAD:**
```
# config.py
DATABASE_POOL_SIZE = 50
DATABASE_MAX_OVERFLOW = 200
```

**Problem:** App creating 250 potential connections (50 + 200)

**Step 5: Monitor Connection Growth**
```bash
watch -n 5 "psql -U postgres -d postgres -c \
  \"SELECT count(*) FROM pg_stat_activity WHERE usename='app_user';\""
```

**OUTPUT:**
```
Every 5.0s: 
count
-----
  45
  
Every 5.0s:
count
-----
  78

Every 5.0s:
count
-----
 145
```

**Pattern:** Growing without limit = connection leak in app

### ✅ FIX: Connection Pool Issues

**Step 1: Fix Connection Pool Config**
```bash
cat > /app/config.py << 'EOF'
# config.py
DATABASE_POOL_SIZE = 10        # ← Reduced from 50
DATABASE_MAX_OVERFLOW = 5      # ← Reduced from 200
DATABASE_POOL_TIMEOUT = 30     # ← Force close after 30s idle
DATABASE_POOL_RECYCLE = 3600   # ← Recycle after 1 hour

# Enable connection pooling logging
import logging
logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)
EOF
```

**Step 2: Find Connection Leak in Code**
```bash
grep -rn "\.connect()" /app --include="*.py" | grep -v "pool"
```

**OUTPUT - Finding Leak:**
```
/app/routes/employees.py:45: conn = psycopg2.connect(db_url)  ← NOT USING POOL!
/app/utils/db.py:23: self.conn = engine.connect()  ← Missing close()
```

**Fix Code:**
```python
# BAD - Leaking connections:
def get_employees():
    conn = psycopg2.connect('postgresql://...')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees")
    return cursor.fetchall()
    # ❌ Connection never closed!

# GOOD - Proper connection management:
from sqlalchemy import create_engine
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    engine = create_engine('postgresql://...', pool_size=10)
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()  # ✓ Always closed

def get_employees():
    with get_db_connection() as conn:
        result = conn.execute("SELECT * FROM employees")
        return result.fetchall()
```

**Step 3: Restart Application**
```bash
kubectl rollout restart deployment employee-app -n dev
```

**VERIFY CONNECTIONS DROP:**
```bash
watch -n 5 "psql -U postgres -d postgres -c \
  \"SELECT count(*) FROM pg_stat_activity WHERE usename='app_user';\""
```

**OUTPUT - FIXED:**
```
Every 5.0s:
count
-----
  12

Every 5.0s:
count
-----
  15

Every 5.0s:
count
-----
  13
```

**Connection count stable at ~13 (normal!)**

---

## SCENARIO 5: FILE CORRUPTION - CORRUPTED FILESYSTEM

### ⚠️ ISSUE
File read errors
Application fails to access data files
Error: "Input/output error"

### 🔍 WHAT TO CHECK

**Step 1: Check Filesystem Errors**
```bash
dmesg | grep -i "error\|corrupt\|ioerror" | tail -20
```

**OUTPUT - BAD:**
```
[3456.234567] EXT4-fs error (device xvda1): ext4_lookup:1234: inode #5678: comm python3: bad entry in directory: rec_len % 4 != 0 - offset=0, inode=5678, rec_len=0, name_len=0
[3457.123456] EXT4-fs (xvda1): mounted filesystem with ordered data mode. Opts: (null)
[3458.654321] Buffer I/O error on device xvda1, logical block 123456
[3459.234567] lost page write due to I/O error on /app
```

**Filesystem corruption detected!**

**Step 2: Check Disk Health**
```bash
sudo smartctl -a /dev/xvda1 2>/dev/null | grep -i "error\|fail"
```

**OUTPUT - BAD:**
```
SMART Self-test log
Num  Test_Type  Status                 FailureHour  LBA_of_first_error
#1   Short offline  Completed: read failure        0x0000123456789abc
#2   Extended offline  Completed: read failure     0x000fedcba987654
SMART overall-health self-assessment test result: FAILED!
```

**Diagnosis:** Disk failure with read errors

**Step 3: Check File Integrity**
```bash
sudo fsck -n /dev/xvda1  # -n = don't fix, just check
```

**OUTPUT - BAD:**
```
e2fsck 1.45.5 (07-Jan-2020)
Warning! /dev/xvda1 is mounted.
/dev/xvda1 contains a file system with errors, check forced.
Pass 1: Checking inodes, blocks, and sizes
Inode 5678 has invalid mode (0x00000000).
   FIXED
Inode 5679, i_size is 0, but it has 1 block.  FIXED.
Pass 2: Checking directory structure
...
```

### ✅ FIX: Repair Filesystem

**WARNING: Must stop services first**

**Step 1: Stop Kubernetes Node**
```bash
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
```

**OUTPUT:**
```
node/ip-10-0-1-50.ec2.internal drained
```

**Step 2: SSH to Node**
```bash
ssh -i key.pem ubuntu@<node-ip>
```

**Step 3: Unmount Filesystem**
```bash
sudo umount /dev/xvda1
```

**Step 4: Run Full Repair**
```bash
sudo fsck -y /dev/xvda1  # -y = auto-fix all errors
```

**OUTPUT:**
```
e2fsck 1.45.5 (07-Jan-2020)
/dev/xvda1: recovering journal
/dev/xvda1: **WARNING** - A file system was mounted while it was running fsck with the -n flag.
Pass 1: Checking inodes, blocks, and sizes
Inode 5678 has invalid mode (0x00000000).
   FIXED
...
e2fsck: aborted
```

**Step 5: Remount and Verify**
```bash
sudo mount /dev/xvda1 /
df -h
```

**OUTPUT:**
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/xvda1       20G  12G   8.0G 60% /
```

**Step 6: Bring Node Back Online**
```bash
kubectl uncordon <node-name>
```

**OUTPUT:**
```
node/ip-10-0-1-50.ec2.internal uncordoned
```

**Step 7: Verify Pods Reschedule**
```bash
kubectl get pods -n dev
```

**OUTPUT:**
```
NAME                              READY   STATUS    RESTARTS   AGE
employee-app-5f4d8c9b2-xyz1a     1/1     Running   0          2m
```

---

## SCENARIO 6: NETWORK CONNECTIVITY ISSUES

### ⚠️ ISSUE
App can't reach database
DNS not resolving
Connection timeouts

### 🔍 WHAT TO CHECK

**Step 1: Test DNS Resolution**
```bash
nslookup postgres-service.dev.svc.cluster.local 10.96.0.10
```

**OUTPUT - GOOD:**
```
Server:         10.96.0.10
Address:        10.96.0.10#53

Name:   postgres-service.dev.svc.cluster.local
Address: 10.96.0.200
```

**OUTPUT - BAD:**
```
Server:         10.96.0.10
Address:        10.96.0.10#53

** server can't find postgres-service.dev.svc.cluster.local: NXDOMAIN
```

**PROBLEM:** DNS server not responding

**Step 2: Check Network Interfaces**
```bash
ip addr show | grep -A 5 "inet"
```

**OUTPUT - GOOD:**
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9001
    inet 10.0.1.50/24 brd 10.0.1.255 scope global eth0
3: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500
    inet 172.17.0.1/16 scope global docker0
```

**OUTPUT - BAD:**
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536
    inet 127.0.0.1/8 scope host lo
```

**PROBLEM:** Only loopback interface up, eth0 DOWN!

**Step 3: Bring Interface Up**
```bash
sudo ip link set eth0 up
```

**Verify:**
```bash
ip addr show eth0
```

**OUTPUT:**
```
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9001
    inet 10.0.1.50/24 brd 10.0.1.255 scope global eth0
```

**Step 4: Check Network Routes**
```bash
route -n
```

**OUTPUT - GOOD:**
```
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         10.0.1.1        0.0.0.0         UG    100    0        0 eth0
10.0.0.0        0.0.0.0         255.255.0.0     U     0      0        0 eth0
169.254.0.0     0.0.0.0         255.255.0.0     U     1002   0        0 eth0
```

**OUTPUT - BAD (No Default Route):**
```
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
10.0.0.0        0.0.0.0         255.255.0.0     U     0      0        0 eth0
```

**PROBLEM:** No default gateway!

**Step 5: Add Default Route**
```bash
sudo route add default gw 10.0.1.1
```

**Verify:**
```bash
route -n
```

**OUTPUT - FIXED:**
```
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         10.0.1.1        0.0.0.0         UG    100    0        0 eth0
10.0.0.0        0.0.0.0         255.255.0.0     U     0      0        0 eth0
```

**Step 6: Make Persistent (if needed)**
```bash
cat >> /etc/network/interfaces << 'EOF'
auto eth0
iface eth0 inet dhcp
EOF
```

**Restart Network:**
```bash
sudo systemctl restart networking
```

---

## 🛠️ RAPID DIAGNOSTIC COMMANDS

### System Health Check
```bash
# CPU, Memory, Disk all-in-one
echo "=== CPU ===" && top -b -n 1 | head -3
echo "=== Memory ===" && free -h | grep Mem
echo "=== Disk ===" && df -h | grep -E "^/dev"
echo "=== Load ===" && uptime

# Process list sorted by resource
ps aux --sort=-%cpu | head -5
ps aux --sort=-%mem | head -5
```

### Disk I/O Analysis
```bash
iostat -x 1 5  # 5 iterations, 1-sec interval
iotop -b -n 1  # Top I/O processes
```

### Network Analysis
```bash
netstat -an | grep ESTABLISHED | wc -l  # Active connections
ss -s  # Socket statistics
iftop -n  # Live bandwidth usage
```

### Process Monitoring
```bash
# Find what process is hogging resources
ps aux --sort=-%cpu | head -1
ps aux --sort=-%mem | head -1

# Check if process still running
ps -p <PID>

# Get full command line
cat /proc/<PID>/cmdline | tr '\0' ' '; echo

# Get file handles
lsof -p <PID> | wc -l
```

### Kernel/System Errors
```bash
dmesg | tail -50
dmesg | grep -i "error\|fail\|oom\|killed"
journalctl -xn  # Recent systemd logs
```

---

## 📋 QUICK REFERENCE

| Problem | Command | Interpretation |
|---------|---------|---|
| High CPU | `top -b -n 1` | If %CPU > 80% and not expected |
| High Memory | `free -h` | If available < 500MB |
| High Disk I/O | `iostat -x 1 5` | If %util > 90% |
| Disk Full | `df -h` | If Use% > 90% |
| Many Connections | `netstat -an \| wc -l` | If > 1000 |
| DNS Not Working | `nslookup <host> 8.8.8.8` | Should return IP |
| Network Down | `ip addr show eth0` | Should show UP status |
| File Corruption | `dmesg \| grep -i error` | Should be empty |

---

## ✅ LINUX VERIFICATION CHECKLIST

- [ ] CPU usage < 80%
- [ ] Memory available > 500MB
- [ ] Disk usage < 85%
- [ ] All network interfaces UP
- [ ] Routes configured correctly
- [ ] No error messages in dmesg
- [ ] DNS resolving correctly
- [ ] No zombie processes
- [ ] No OOM killer events
- [ ] File systems not corrupted

If ALL ✓ → **LINUX is HEALTHY** → Issue likely in application code

