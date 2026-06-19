# NETWORK ARCHITECTURE - ONE-PAGE CHEAT SHEET

## LOCAL DEVELOPMENT (Docker Compose)

```
YOUR BROWSER                    DOCKER HOST (Your Laptop)
    |                           ___________________________
    |                          |                           |
    v                          | Docker Bridge Network     |
curl http://localhost:8000     | 172.18.0.0/16            |
    |                          |                           |
    | (port 8000 mapping)      | ┌─────────────────────┐  |
    |                          | │ employee-app        │  |
    +─────────────────────────>| │ Container IP:       │  |
                               | │ 172.18.0.3:8000     │  |
                               | │ Port: 8000 (listen) │  |
                               | │                     │  |
                               | │ ENV:                │  |
                               | │ DB_HOST=postgres    │  |
                               | └────────┬────────────┘  |
                               |          |               |
                               |    Docker DNS            |
                               |  127.0.0.11:53           |
                               |  postgres → 172.18.0.2   |
                               |          |               |
                               | ┌────────v────────────┐  |
                               | │ postgres            │  |
                               | │ Container IP:       │  |
                               | │ 172.18.0.2:5432     │  |
                               | │ Database: hrdb      │  |
                               | └─────────────────────┘  |
                               |___________________________|

PORT MAPPINGS:
- localhost:8000 ──→ container:8000 (FastAPI)
- localhost:5433 ──→ container:5432 (PostgreSQL)
```

---

## PRODUCTION (Kubernetes on AWS)

```
INTERNET USERS                  AWS VPC: 10.0.0.0/16
        |                       _______________________________________________________
        |                      |                                                       |
        v                      | ┌──────────────────────────────────────────────────┐ |
user requests                  | │ AWS ALB (52.12.34.56)                            │ |
dev.shivalayammtp.club         | │ - Port 443 (HTTPS)                               │ |
        |                      | │ - Decrypts TLS                                   │ |
    ┌───────────────────┐      | │ - Adds X-Forwarded headers                       │ |
    │ Route 53 (DNS)    │      | └──────────────┬───────────────────────────────────┘ |
    │ Resolves to:      │      |                │                                    |
    │ 52.12.34.56       │      |                v                                    |
    └───────────────────┘      | ┌──────────────────────────────────────────────────┐ |
                               | │ Ingress Controller (Nginx)                       │ |
                               | │ Pod IP: 10.0.1.101                               │ |
                               | │ Rule: dev.shivalayammtp.club → svc:8000         │ |
                               | └──────────────┬───────────────────────────────────┘ |
                               |                │                                    |
                               |      ┌─────────┴────────┐                           |
                               |      v                 v                            |
                               | ┌─────────────────────────────────────────────────┐ |
                               | │ Service: employee-service (10.96.0.50:8000)    │ |
                               | │ - ClusterIP (internal only)                      │ |
                               | │ - Endpoints:                                     │ |
                               | │   • 10.0.1.100:8000 (Pod 1 - AZ us-east-1a)    │ |
                               | │   • 10.0.2.100:8000 (Pod 2 - AZ us-east-1b)    │ |
                               | │ - Load balances across endpoints                 │ |
                               | └──────────────┬────────────────────────────────┬─┘ |
                               |                │                                │   |
                               |                v                                │   |
                               | ┌──────────────────────────────────────────┐    │   |
                               | │ Pod 1: employee-app (10.0.1.100:8000)   │    │   |
                               | │ FastAPI on 8000                          │    │   |
                               | │ ENV: DB_HOST=postgres-service            │    │   |
                               | │ Needs data → queries database            │    │   |
                               | └──────────────┬───────────────────────────┘    │   |
                               |                │                                │   |
                               |         ┌──────────────┐                        │   |
                               |         │ Kubernetes   │                        │   |
                               |         │ DNS lookup   │                        │   |
                               |         │ (CoreDNS)    │                        │   |
                               |         │ postgres-    │                        │   |
                               |         │ service →    │                        │   |
                               |         │ 10.96.0.200  │                        │   |
                               |         └──────────────┘                        │   |
                               |                │                                │   |
                               |                v                                │   |
                               | ┌──────────────────────────────────────────┐    │   |
                               | │ Service: postgres-service (10.96.0.200) │    │   |
                               | │ - Routes to RDS database                 │    │   |
                               | │ - Endpoint: 10.0.100.100:5432           │    │   |
                               | └──────────────┬───────────────────────────┘    │   |
                               |                │                                │   |
                               |                v                                │   |
                               | ┌──────────────────────────────────────────┐    │   |
                               | │ RDS PostgreSQL                           │    │   |
                               | │ - Primary: 10.0.100.50 (us-east-1a)    │    │   |
                               | │ - Standby: 10.0.101.50 (us-east-1b)    │    │   |
                               | │ - Multi-AZ enabled                       │    │   |
                               | │ - Auto-failover < 2 minutes             │    │   |
                               | └──────────────────────────────────────────┘    │   |
                               |___________________________________________________|
```

---

## KEY DIFFERENCES

| Aspect | Docker Compose | Kubernetes |
|--------|---|---|
| **Environment** | Your laptop | AWS/Cloud data center |
| **Service Discovery** | Docker DNS (127.0.0.11:53) | Kubernetes DNS (10.96.0.10:53) |
| **Scaling** | Manual | Automatic (HPA) |
| **Failure Recovery** | Manual restart | Auto-restart + replication |
| **High Availability** | No | Yes (Multi-AZ) |
| **Database** | Container (ephemeral) | AWS RDS (persistent) |
| **External Access** | localhost:port | Domain + ALB |

---

## TYPICAL REQUEST TIMES

### Docker Compose
- DNS: 1ms (localhost, instant)
- App processing: 50ms
- DB query: 20ms
- **Total: 70ms**

### Kubernetes (Mumbai user to Virginia)
- Geographic latency: 150ms
- DNS: 2ms (internal) + 50ms (Route53)
- TLS: 150ms
- App + DB: 200ms
- **Total: 550ms**

---

## FLOW COMPARISON

### How Request Flows (Docker Compose)
```
localhost:8000 → app container (172.18.0.3)
                  ↓ DB lookup
                  "postgres" → DNS (127.0.0.11:53)
                  ↓
                  172.18.0.2:5432 (postgres container)
                  ↓
                  Response back
```

### How Request Flows (Kubernetes)
```
dev.shivalayammtp.club → DNS (Route53)
                         ↓
                         52.12.34.56 (ALB)
                         ↓
                         Ingress Controller
                         ↓
                         Ingress rule matches
                         ↓
                         employee-service:8000 (10.96.0.50)
                         ↓
                         Pod endpoints [10.0.1.100, 10.0.2.100]
                         ↓ (load balance)
                         Pod 1 or Pod 2
                         ↓ DB lookup
                         postgres-service → CoreDNS (10.96.0.10:53)
                         ↓
                         10.96.0.200 (postgres Service)
                         ↓
                         10.0.100.100:5432 (RDS)
                         ↓
                         Response
```

---

## KUBERNETES OBJECTS AT A GLANCE

```
DEPLOYMENT          → Creates and manages Pods
                      Ensures desired replicas always running
                      Handles updates and rollbacks

SERVICE             → Virtual load balancer
                      Routes traffic to Pods with matching labels
                      3 types: ClusterIP, NodePort, LoadBalancer

POD                 → Smallest unit, contains container(s)
                      Has internal IP (10.0.x.x)
                      Usually created by Deployment

CONFIGMAP           → Non-secret config storage
                      Key-value pairs (plain text)
                      Mounted as env vars or files

SECRET              → Encrypted config storage
                      Passwords, tokens, credentials
                      Encrypted at rest in etcd

INGRESS             → HTTP(S) router
                      Routes domains/paths to Services
                      Needs Ingress Controller (like Nginx)

NAMESPACE           → Virtual cluster subdivision
                      Isolates resources (dev, staging, prod)
```

---

## MUST-KNOW COMMANDS

```bash
# View
kubectl get pods -n dev                 # List Pods
kubectl get svc -n dev                  # List Services
kubectl describe pod <name> -n dev      # Details
kubectl logs <pod> -n dev               # View logs

# Debug
kubectl exec <pod> -n dev -- bash      # Shell into Pod
kubectl exec <pod> -n dev -- curl http://svc:8000  # Run cmd
kubectl port-forward svc/<svc> 8000:8000 -n dev  # Local access

# Monitor
kubectl top nodes                       # Node resource usage
kubectl top pods -n dev                 # Pod resource usage
kubectl get events -n dev               # Recent events

# Fix
kubectl delete pod <pod> -n dev        # Force restart
kubectl rollout restart deploy/<dep> -n dev  # Restart Deployment
```

---

## SECURITY GROUPS (AWS)

```
ALB Security Group:
├─ Inbound: 443 from 0.0.0.0/0 (HTTPS from internet) ✓
├─ Inbound: 80 from 0.0.0.0/0 (HTTP redirect) ✓
└─ Outbound: All to EKS SG

EKS Security Group:
├─ Inbound: 8000 from ALB SG (traffic from ALB) ✓
├─ Inbound: 443 from 0.0.0.0/0 (kubectl access) ✓
├─ Outbound: All (to reach RDS, internet, etc.)
└─ Outbound: 5432 to RDS SG

RDS Security Group:
├─ Inbound: 5432 from EKS SG ONLY (database from Pods) ✓
├─ Inbound: Nothing else
└─ Outbound: Deny all (DB doesn't initiate connections)
```

---

## ENDPOINTS EXPLAINED

```
Every Service needs Endpoints (actual Pod IPs):

ClusterIP Service
├─ Cluster IP: 10.96.0.50 (virtual, doesn't exist)
└─ Endpoints: 10.0.1.100, 10.0.2.100 (real Pod IPs)
   ├─ kube-proxy watches for changes
   ├─ Updates iptables rules dynamically
   └─ If Pod dies: removed from endpoints
   └─ If Pod starts: added to endpoints
   └─ Traffic automatically redirected ✓

No Endpoints = Problem:
Endpoints: <none>
└─ No Pods found matching selector labels
└─ Service exists but can't route traffic anywhere
└─ All requests fail
```

---

## MULTI-AZ FAILOVER

```
NORMAL:
  AZ-a: Pod 1, DB Primary  →  RUNNING ✓
  AZ-b: Pod 2, DB Standby  →  RUNNING ✓

AZ-a FAILS:
  AZ-a: DOWN ✗
  AZ-b: Pod 2, DB new Primary  →  AUTO-PROMOTED ✓
  
Recovery: Pod 1 recreated in AZ-b ✓
Result: Still running, no manual intervention

When AZ-a recovers:
  Rebalance Pods back
  Create new Standby
  Re-establish replication
  Back to normal ✓
```

---

## TROUBLESHOOTING QUICK GUIDE

```
Issue: "Website not working"
├─→ Check External Access
│   └─ Is ALB receiving traffic from internet?
│      curl https://dev.shivalayammtp.club
│
├─→ Check Internal Routing
│   └─ Are Pods ready?
│      kubectl get pods -n dev
│      Look for: 1/1 Ready, Running status
│
├─→ Check Database
│   └─ Can Pods reach DB?
│      kubectl logs pod | grep -i database
│      Check: postgres-service endpoints exist
│
└─→ Check Logs
    └─ What exactly failed?
       kubectl logs <pod> -n dev
       Look for: ERROR, exception, stacktrace
```

---

## REMEMBER

✓ **Services** are virtual load balancers (IPs don't exist)
✓ **Pods** have real IPs (10.0.x.x) that change
✓ **DNS** names abstract IP changes (always use names)
✓ **ClusterIP** = internal only (no external access)
✓ **Ingress** = only way external users access
✓ **Multi-AZ** = automatic failover < 2 minutes
✓ **RDS** = managed database, you don't manage nodes
✓ **Secrets** = passwords encrypted at rest

---

**Print this page as your quick reference!**
