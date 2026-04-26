# PollMaster System Architecture

## Overview

PollMaster is a real-time polling and survey REST API platform built with a modern, scalable architecture on Microsoft Azure.

## Architecture Documents

| Document | Description |
|----------|-------------|
| [System Architecture](./system-architecture.md) | High-level system design, container diagrams, and architecture decisions |
| [Technology Stack](./tech-stack.md) | Complete technology selection with rationale |
| [Deployment Architecture](./deployment.md) | CI/CD pipelines, Azure infrastructure, and deployment procedures |
| [Data Flow](./data-flow.md) | Vote submission, real-time updates, and result aggregation flows |
| [Security Architecture](./security.md) | Security layers, threat mitigation, and compliance |

## Quick Reference

### Technology Stack
- **Runtime:** Node.js 20 LTS
- **Framework:** Express.js 4.18
- **Database:** Azure SQL Database
- **Cache:** Azure Redis Cache
- **Real-Time:** Socket.io
- **Frontend:** Vanilla JS + TailwindCSS
- **Hosting:** Azure App Service

### Key Architecture Decisions
- **Pattern:** Modular Monolith with clear service boundaries
- **Scaling:** Horizontal auto-scaling (2-10 instances)
- **Session Management:** Redis-backed sessions for voter tracking
- **Real-Time:** WebSocket with Socket.io for live vote updates
- **Security:** Defense in depth with WAF, input validation, and encryption

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SYSTEMS                                │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│   Web Clients   │  Mobile Clients │   Third-Party   │    Email Service      │
│   (Browsers)    │   (Future)      │   Analytics     │    (SendGrid)         │
└────────┬────────┴────────┬────────┴────────┬────────┴───────────┬───────────┘
         │                 │                 │                    │
         └─────────────────┴─────────────────┴────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           POLLMASTER PLATFORM                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Azure Application Gateway                        │    │
│  │                    (SSL Termination, Load Balancing)                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Azure App Service (Node.js)                        │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │    │
│  │  │   API Layer │  │  WebSocket  │  │   Static    │  │  Health    │  │    │
│  │  │  (Express)  │  │   Server    │  │   Assets    │  │   Checks   │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Data Layer                                    │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │    │
│  │  │  Azure SQL  │  │ Azure Redis │  │ Azure Blob  │  │ Azure Queue│  │    │
│  │  │  Database   │  │   Cache     │  │   Storage   │  │  Storage   │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Performance Targets

| Metric | Target |
|--------|--------|
| API Response Time (p95) | < 200ms |
| WebSocket Latency | < 50ms |
| Database Query Time | < 50ms |
| Page Load Time | < 2s |
| Concurrent Users | 10,000 |
| Vote Throughput | 1000/min |

## Getting Started

See the [Deployment Guide](./deployment.md) for infrastructure setup and deployment procedures.

---

*Last Updated: 2024*
