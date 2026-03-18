# Architecture Justification Report

## Bookstore Microservices – Assignment 06 (Industry Level)

---

## 1. JWT Authentication Service

### Design Decision
Centralized `auth-service` handles all authentication, issuing JWT access tokens (30 min) and refresh tokens (7 days). The API Gateway validates tokens via middleware, eliminating the need for each service to implement its own authentication.

### Justification
- **Single Responsibility**: Auth logic is isolated in one service, simplifying maintenance and security audits
- **Stateless Tokens**: JWT tokens are self-contained, enabling horizontal scaling without shared session state
- **Role-Based Access Control**: Token payload includes `role` claim, enabling fine-grained authorization at the gateway level
- **Password Security**: Uses Django's built-in `make_password`/`check_password` with PBKDF2 hashing

### Trade-offs
- JWT tokens cannot be revoked before expiry (mitigated by short 30-min access tokens)
- JWT secret must be shared between auth-service and API gateway (managed via environment variables)

---

## 2. Saga Pattern for Distributed Transactions

### Design Decision
Order creation uses **Saga Orchestration** pattern. The order-service acts as the orchestrator, sequentially calling pay-service and ship-service with compensating transactions on failure.

### Saga Steps
1. **Create Order** (PENDING) → Local operation
2. **Reserve Payment** → `POST pay-service/reserve/`
3. **Reserve Shipping** → `POST ship-service/reserve/`
4. **Confirm Order** (CONFIRMED)
5. **On failure**: Cancel shipping → Cancel payment → Mark order FAILED

### Justification
- **Orchestration over Choreography**: Chosen because order flow has a clear linear sequence. Orchestration provides centralized control and easier debugging via `SagaLog` model
- **Reserve/Confirm Pattern**: Two-phase approach prevents partial commits. Payment is reserved (not charged) until shipping is confirmed
- **Compensation Logging**: Every saga step is recorded in `SagaLog`, enabling audit trails and debugging

### Trade-offs
- Orchestrator is a single point of failure (acceptable for academic project; production would use message-based orchestration)
- Synchronous HTTP calls between services (mitigated by event publishing for async processing)

---

## 3. Event Bus (RabbitMQ)

### Design Decision
RabbitMQ with **Topic Exchange** for asynchronous event publishing. Services publish domain events (`order.created`, `payment.reserved`, etc.) that other services can consume independently.

### Justification
- **Loose Coupling**: Services publish events without knowing who consumes them
- **Topic Exchange**: Flexible routing with pattern matching (e.g., `order.*` matches all order events)
- **Persistent Messages**: `delivery_mode=2` ensures messages survive broker restarts
- **RabbitMQ over Kafka**: RabbitMQ better suits this use case (low volume, simple routing, acknowledgment-based consumption)

### Trade-offs
- Current implementation uses both synchronous HTTP (saga steps) and async events (notifications). Production would fully transition to event-driven
- In-memory consumer state means restarting consumers may lose processing context

---

## 4. API Gateway

### Design Decision
Django-based API Gateway with three middleware layers applied in order:

1. **RateLimitMiddleware** → Applied first to reject excess traffic early
2. **JWTAuthenticationMiddleware** → Validates tokens on protected routes
3. **RequestLoggingMiddleware** → Logs all requests with timing data

### Justification
- **Middleware Order Matters**: Rate limiting before auth prevents DoS attacks from exhausting auth processing
- **Public Route Whitelisting**: Auth endpoints (`/auth/`), health/metrics, and home page are accessible without tokens
- **User Identity Forwarding**: Gateway injects `X-User-Id`, `X-User-Email`, `X-User-Role` headers for downstream services
- **Aggregated Health Check**: Single `/health/` endpoint checks all 12 downstream services

### Rate Limiting
- Token bucket algorithm: 100 requests/minute per IP
- In-memory storage (would use Redis in production for multi-instance gateways)

---

## 5. Observability

### Components
| Component | Implementation |
|-----------|---------------|
| **Health Checks** | `/health/` on all 13 services + aggregated at gateway |
| **Metrics** | Request count, error count, avg response time at `/metrics/` |
| **Logging** | Structured JSON logs with service name, timestamp, level |
| **Request Logging** | Method, path, status code, duration, IP, user_id |

### Justification
- **Structured JSON Logging**: Machine-parseable format enables log aggregation tools (ELK, Loki)
- **Health Endpoints**: Kubernetes-ready liveness/readiness probes
- **Gateway Metrics**: Centralizes monitoring at the entry point

---

## 6. Fault Simulation

### Design Decision
Pay-service and ship-service include fault injection endpoints (`/fault/enable/`, `/fault/disable/`) that force the next N requests to fail. This enables testing the Saga pattern's compensation logic.

### Justification
- **Chaos Engineering Lite**: Validates system resilience without external tools
- **Controlled Failures**: Configurable failure count prevents permanent damage
- **In-Memory State**: Fault config resets on service restart (safe by design)

---

## Architecture Diagram

```
                         ┌──────────────────┐
                         │    Frontend       │
                         │    (port 3000)    │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │   API Gateway     │
                         │   (port 4000)     │
                         │ ┌───────────────┐ │
                         │ │ Rate Limiter  │ │
                         │ │ JWT Validator │ │
                         │ │ Logger        │ │
                         │ └───────────────┘ │
                         └───┬───┬───┬───┬───┘
            ┌────────────────┤   │   │   ├────────────────┐
            │                │   │   │   │                │
    ┌───────▼──┐  ┌──────▼──┐│   │┌──▼────┐  ┌──────────▼──┐
    │auth-svc  │  │book-svc ││   ││cart-svc│  │customer-svc │
    │(JWT+RBAC)│  │         ││   ││       │  │             │
    └──────────┘  └─────────┘│   │└───────┘  └─────────────┘
                             │   │
              ┌──────────────┤   ├──────────────┐
              │              │   │              │
      ┌───────▼──┐   ┌──────▼──┐   ┌───────▼──┐
      │order-svc │   │pay-svc  │   │ship-svc  │
      │(Saga     │◄──│(Reserve/│   │(Reserve/ │
      │Orchestr.)│──►│ Cancel) │   │ Cancel)  │
      └────┬─────┘   └─────────┘   └──────────┘
           │
    ┌──────▼──────┐
    │  RabbitMQ   │
    │ (Event Bus) │
    └─────────────┘
```

---

## Summary

This architecture upgrade transforms the bookstore from a simple request-forwarding system to a production-ready microservices platform with:
- **Security**: JWT-based authentication with RBAC
- **Reliability**: Saga pattern with compensation for distributed transactions
- **Scalability**: Async messaging via RabbitMQ
- **Operability**: Health checks, metrics, structured logging
- **Resilience**: Fault simulation for chaos testing
