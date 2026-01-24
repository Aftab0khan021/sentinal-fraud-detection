# SentinAL Architecture Documentation

## System Context (C4 Level 1)

### Overview
SentinAL is an AI-powered fraud detection system using Graph Neural Networks (GNN) and GraphRAG for explainable fraud analysis.

### System Context Diagram

```mermaid
C4Context
    title System Context - SentinAL Fraud Detection Platform

    Person(analyst, "Fraud Analyst", "Reviews fraud cases and investigations")
    Person(admin, "System Administrator", "Manages system configuration and monitoring")
    Person(developer, "Developer", "Integrates SentinAL into applications")
    
    System(sentinal, "SentinAL Platform", "AI-powered fraud detection using GNN and GraphRAG")
    
    System_Ext(payment, "Payment Gateway", "Processes financial transactions")
    System_Ext(identity, "Identity Provider", "OAuth/SAML authentication")
    System_Ext(pagerduty, "PagerDuty", "Incident management and on-call")
    System_Ext(slack, "Slack", "Team notifications and alerts")
    System_Ext(monitoring, "External Monitoring", "Uptime monitoring services")
    
    Rel(analyst, sentinal, "Analyzes fraud cases", "HTTPS/Web UI")
    Rel(admin, sentinal, "Configures and monitors", "HTTPS/Grafana")
    Rel(developer, sentinal, "Integrates via API", "HTTPS/REST API")
    
    Rel(sentinal, payment, "Analyzes transactions from", "REST API")
    Rel(sentinal, identity, "Authenticates users via", "OAuth 2.0/JWT")
    Rel(sentinal, pagerduty, "Sends critical alerts to", "Webhook")
    Rel(sentinal, slack, "Sends notifications to", "Webhook")
    Rel(monitoring, sentinal, "Monitors uptime", "HTTPS")
    
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

### External Dependencies
- **Payment Gateway**: Source of transaction data for fraud analysis
- **Identity Provider**: User authentication and authorization
- **PagerDuty**: Critical incident alerting
- **Slack**: Team notifications and warnings
- **External Monitoring**: Uptime and availability monitoring

---

## Container Diagram (C4 Level 2)

### Container Architecture

```mermaid
C4Container
    title Container Diagram - SentinAL Platform

    Person(user, "User", "Fraud analyst or developer")

    Container_Boundary(lb, "Load Balancer") {
        Container(nginx, "NGINX", "Load Balancer", "Routes traffic, SSL termination, rate limiting")
    }

    Container_Boundary(app, "Application Layer") {
        Container(api1, "API Instance 1", "FastAPI", "Fraud detection API")
        Container(api2, "API Instance 2", "FastAPI", "Fraud detection API")
        Container(api3, "API Instance 3", "FastAPI", "Fraud detection API")
        Container(frontend, "Web Frontend", "React/TypeScript", "User interface for fraud analysis")
    }

    Container_Boundary(data, "Data Layer") {
        ContainerDb(redis_master, "Redis Master", "Redis", "Primary cache and session store")
        ContainerDb(redis_replica1, "Redis Replica 1", "Redis", "Cache replica")
        ContainerDb(redis_replica2, "Redis Replica 2", "Redis", "Cache replica")
        Container(sentinel, "Redis Sentinel", "Redis Sentinel", "HA and failover management")
    }

    Container_Boundary(monitoring, "Monitoring & Observability") {
        Container(prometheus, "Prometheus", "Metrics", "Time-series metrics database")
        Container(grafana, "Grafana", "Visualization", "Dashboards and alerts")
        Container(jaeger, "Jaeger", "Tracing", "Distributed tracing")
        Container(alertmanager, "AlertManager", "Alerting", "Alert routing and notification")
    }

    Rel(user, nginx, "Uses", "HTTPS")
    Rel(nginx, api1, "Routes to", "HTTP")
    Rel(nginx, api2, "Routes to", "HTTP")
    Rel(nginx, api3, "Routes to", "HTTP")
    Rel(nginx, frontend, "Serves", "HTTP")

    Rel(api1, redis_master, "Reads/Writes", "Redis Protocol")
    Rel(api2, redis_master, "Reads/Writes", "Redis Protocol")
    Rel(api3, redis_master, "Reads/Writes", "Redis Protocol")

    Rel(redis_master, redis_replica1, "Replicates to", "Redis Protocol")
    Rel(redis_master, redis_replica2, "Replicates to", "Redis Protocol")
    Rel(sentinel, redis_master, "Monitors", "Redis Protocol")
    Rel(sentinel, redis_replica1, "Monitors", "Redis Protocol")
    Rel(sentinel, redis_replica2, "Monitors", "Redis Protocol")

    Rel(api1, jaeger, "Sends traces", "UDP")
    Rel(api2, jaeger, "Sends traces", "UDP")
    Rel(api3, jaeger, "Sends traces", "UDP")

    Rel(prometheus, api1, "Scrapes metrics", "HTTP")
    Rel(prometheus, api2, "Scrapes metrics", "HTTP")
    Rel(prometheus, api3, "Scrapes metrics", "HTTP")
    Rel(prometheus, alertmanager, "Sends alerts", "HTTP")
    Rel(grafana, prometheus, "Queries", "HTTP")
    Rel(grafana, jaeger, "Queries", "HTTP")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

### Technology Stack
- **Load Balancer**: NGINX (SSL termination, rate limiting, health checks)
- **API**: FastAPI (Python 3.11+, async/await)
- **Frontend**: React 18 + TypeScript + Vite
- **Cache**: Redis 7 (Sentinel for HA)
- **Metrics**: Prometheus + Grafana
- **Tracing**: OpenTelemetry + Jaeger
- **Alerting**: AlertManager + PagerDuty + Slack

---

## Component Diagram (C4 Level 3)

### API Component Architecture

```mermaid
C4Component
    title Component Diagram - SentinAL API

    Container_Boundary(api, "FastAPI Application") {
        Component(auth, "Authentication", "JWT/OAuth", "User authentication and authorization")
        Component(fraud_detection, "Fraud Detection", "GNN Model", "Graph neural network fraud detection")
        Component(explainer, "GraphRAG Explainer", "LangChain + Ollama", "AI-powered fraud explanations")
        Component(cache_mgr, "Cache Manager", "Redis Client", "Distributed caching layer")
        Component(tracing, "Tracing", "OpenTelemetry", "Distributed tracing instrumentation")
        Component(metrics, "Metrics", "Prometheus Client", "Application metrics collection")
        Component(logging, "Logging", "Structured Logger", "JSON structured logging")
    }

    ContainerDb(redis, "Redis", "Cache", "Distributed cache")
    Container(jaeger, "Jaeger", "Tracing", "Trace collector")
    Container(prometheus, "Prometheus", "Metrics", "Metrics collector")

    Rel(auth, cache_mgr, "Stores sessions", "")
    Rel(fraud_detection, cache_mgr, "Caches predictions", "")
    Rel(fraud_detection, explainer, "Requests explanation", "")
    Rel(cache_mgr, redis, "Reads/Writes", "Redis Protocol")
    Rel(tracing, jaeger, "Sends spans", "UDP")
    Rel(metrics, prometheus, "Exposes metrics", "HTTP")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

### Key Components
1. **Authentication**: JWT-based auth with token refresh and blacklisting
2. **Fraud Detection**: R-GCN model for graph-based fraud detection
3. **GraphRAG Explainer**: LangChain + Ollama for explainable AI
4. **Cache Manager**: Redis with automatic fallback to in-memory
5. **Tracing**: OpenTelemetry for distributed tracing
6. **Metrics**: Prometheus instrumentation for monitoring
7. **Logging**: Structured JSON logging with trace correlation

---

## Deployment Diagram

### Production Deployment Architecture

```mermaid
graph TB
    subgraph "External"
        Users[Users/Clients]
        PagerDuty[PagerDuty]
        Slack[Slack]
    end

    subgraph "Edge Layer"
        LB[NGINX Load Balancer<br/>SSL Termination<br/>Rate Limiting]
    end

    subgraph "Application Layer"
        API1[API Instance 1<br/>FastAPI + GNN]
        API2[API Instance 2<br/>FastAPI + GNN]
        API3[API Instance 3<br/>FastAPI + GNN]
        Frontend[React Frontend<br/>Static Files]
    end

    subgraph "Data Layer"
        RedisMaster[Redis Master<br/>Primary Cache]
        RedisReplica1[Redis Replica 1]
        RedisReplica2[Redis Replica 2]
        Sentinel1[Sentinel 1]
        Sentinel2[Sentinel 2]
        Sentinel3[Sentinel 3]
    end

    subgraph "Monitoring Layer"
        Prometheus[Prometheus<br/>Metrics DB]
        Grafana[Grafana<br/>Dashboards]
        Jaeger[Jaeger<br/>Distributed Tracing]
        AlertManager[AlertManager<br/>Alert Routing]
    end

    Users -->|HTTPS| LB
    LB -->|HTTP| API1
    LB -->|HTTP| API2
    LB -->|HTTP| API3
    LB -->|HTTP| Frontend

    API1 -->|Redis Protocol| RedisMaster
    API2 -->|Redis Protocol| RedisMaster
    API3 -->|Redis Protocol| RedisMaster

    RedisMaster -->|Replication| RedisReplica1
    RedisMaster -->|Replication| RedisReplica2

    Sentinel1 -.->|Monitor| RedisMaster
    Sentinel1 -.->|Monitor| RedisReplica1
    Sentinel1 -.->|Monitor| RedisReplica2
    Sentinel2 -.->|Monitor| RedisMaster
    Sentinel3 -.->|Monitor| RedisMaster

    API1 -->|Traces| Jaeger
    API2 -->|Traces| Jaeger
    API3 -->|Traces| Jaeger

    Prometheus -->|Scrape| API1
    Prometheus -->|Scrape| API2
    Prometheus -->|Scrape| API3
    Prometheus -->|Scrape| RedisMaster

    Prometheus -->|Alerts| AlertManager
    AlertManager -->|Critical| PagerDuty
    AlertManager -->|Warnings| Slack

    Grafana -->|Query| Prometheus
    Grafana -->|Query| Jaeger

    style LB fill:#f9f,stroke:#333,stroke-width:4px
    style RedisMaster fill:#ff9,stroke:#333,stroke-width:2px
    style Prometheus fill:#9f9,stroke:#333,stroke-width:2px
```

### Infrastructure Requirements
- **Compute**: 3 API instances (2 CPU, 4GB RAM each)
- **Cache**: 1 Redis master + 2 replicas (1 CPU, 2GB RAM each)
- **Monitoring**: Prometheus (2 CPU, 4GB RAM), Grafana (1 CPU, 2GB RAM), Jaeger (2 CPU, 4GB RAM)
- **Load Balancer**: NGINX (1 CPU, 1GB RAM)
- **Total**: ~11 CPU cores, ~25GB RAM

---

## Data Flow Diagrams

### Fraud Detection Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant NGINX
    participant API
    participant Cache
    participant GNN
    participant Explainer
    participant Jaeger
    participant Prometheus

    Client->>NGINX: POST /api/analyze/{user_id}
    NGINX->>NGINX: Rate limit check
    NGINX->>NGINX: SSL termination
    NGINX->>API: Forward request
    
    API->>Jaeger: Start trace span
    API->>Prometheus: Increment request counter
    
    API->>Cache: Check cache for user_id
    alt Cache hit
        Cache-->>API: Return cached result
        API->>Prometheus: Increment cache hit
    else Cache miss
        Cache-->>API: Cache miss
        API->>Prometheus: Increment cache miss
        API->>GNN: Run fraud detection
        GNN-->>API: Fraud probability
        API->>Explainer: Generate explanation
        Explainer-->>API: AI explanation
        API->>Cache: Store result (TTL: 5min)
    end
    
    API->>Jaeger: End trace span
    API->>Prometheus: Record latency
    API-->>NGINX: Return response
    NGINX-->>Client: JSON response
```

### Redis Failover Flow

```mermaid
sequenceDiagram
    participant API
    participant Sentinel
    participant Master
    participant Replica1
    participant Replica2

    API->>Master: Write request
    Master--xAPI: Connection failed
    
    Sentinel->>Master: Health check failed
    Sentinel->>Sentinel: Quorum reached (2/3)
    Sentinel->>Replica1: Promote to master
    Replica1->>Replica1: Become master
    
    Sentinel->>API: Notify new master
    API->>Replica1: Retry write request
    Replica1-->>API: Success
    
    Replica1->>Replica2: Start replication
```

---

## Scalability Patterns

### Horizontal Scaling
- **API Instances**: Scale from 3 to N instances based on load
- **Load Balancing**: Least connections algorithm
- **Session Affinity**: Not required (stateless API)
- **Auto-scaling**: Based on CPU (>70%) or request rate (>1000 req/s)

### Caching Strategy
- **L1 Cache**: In-memory LRU (per instance, 100MB)
- **L2 Cache**: Redis (shared, 256MB)
- **TTL**: 5 minutes for fraud predictions
- **Invalidation**: Manual via API endpoint

### High Availability
- **API**: 3 instances minimum, survives 1 instance failure
- **Redis**: 1 master + 2 replicas, automatic failover via Sentinel
- **Load Balancer**: Active health checks, 30s interval
- **Target SLA**: 99.9% uptime (43 minutes downtime/month)

---

## Security Architecture

### Defense in Depth
1. **Edge**: NGINX rate limiting, SSL/TLS termination
2. **Application**: JWT authentication, input validation
3. **Data**: Redis password auth, encrypted connections
4. **Monitoring**: Security alerts, brute force detection

### Authentication Flow
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Cache

    Client->>API: POST /api/auth/login
    API->>API: Verify credentials (bcrypt)
    API->>API: Generate JWT (access + refresh)
    API->>Cache: Store refresh token
    API-->>Client: Return tokens

    Client->>API: GET /api/analyze (with JWT)
    API->>API: Verify JWT signature
    API->>API: Check token not blacklisted
    API->>API: Process request
    API-->>Client: Return response
```

---

## Monitoring Strategy

### Golden Signals
1. **Latency**: P50, P95, P99 response times
2. **Traffic**: Requests per second
3. **Errors**: Error rate (5xx responses)
4. **Saturation**: CPU, memory, Redis memory

### Alert Severity Levels
- **Critical**: PagerDuty page (API down, all backends down)
- **Warning**: Slack notification (high latency, high error rate)
- **Info**: Slack monitoring channel (low cache hit rate)

### SLOs (Service Level Objectives)
- **Availability**: 99.9% uptime
- **Latency**: P95 < 200ms
- **Error Rate**: < 1%
- **Cache Hit Rate**: > 80%

---

## Technology Decisions

### Why NGINX over Traefik?
- **Maturity**: Battle-tested in production
- **Performance**: Lower latency, higher throughput
- **Features**: Built-in rate limiting, SSL termination
- **Simplicity**: Easier configuration for our use case

### Why Redis Sentinel over Redis Cluster?
- **Simplicity**: Easier to operate and debug
- **Scale**: Sufficient for our current needs (< 1M req/day)
- **Failover**: Automatic with minimal configuration
- **Cost**: Lower resource requirements

### Why Jaeger over Zipkin?
- **Features**: Better UI, more query options
- **Performance**: Better for high-throughput scenarios
- **Ecosystem**: Better OpenTelemetry integration
- **Community**: More active development

---

## Future Enhancements

### Phase 3 (Future)
- **TorchServe**: Separate model serving for better scalability
- **Kubernetes**: Container orchestration for auto-scaling
- **ELK Stack**: Centralized logging with Elasticsearch
- **Multi-region**: Geographic distribution for lower latency
- **A/B Testing**: Model version comparison framework
