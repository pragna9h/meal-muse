# MealMuse Deployment

This document describes the production deployment architecture and delivery model for MealMuse V1 on Google Cloud Platform.

## Production Architecture

MealMuse is deployed using separate frontend and backend Cloud Run services.

```text
Browser
   |
   v
Cloud Run
React + Nginx Frontend
   |
   | /api/*
   v
Cloud Run
FastAPI Backend
   |              |
   |              +--> OpenAI API
   |
   v
Cloud SQL
PostgreSQL + pgvector
```

The frontend and backend are independently deployable services.

Production Docker images are built with Google Cloud Build and stored in Artifact Registry.

---

## GCP Resources

**Region:** `us-west1`

### Cloud Run

- `mealmuse-frontend`
- `mealmuse-backend`

### Cloud SQL

- PostgreSQL 16
- pgvector enabled
- 50,514 recipes
- 50,514 precomputed embeddings
- 1536-dimensional embedding vectors

### Artifact Registry

- repository: `mealmuse`
- backend Docker image
- frontend Docker image

### Secret Manager

- database password
- OpenAI API key

### IAM

The backend runs under a dedicated service account with least-privilege access to the Cloud SQL instance and required Secret Manager secrets.

---

## Backend Deployment

The backend runs FastAPI/Uvicorn on Cloud Run port `8080`.

Production database connectivity uses the Cloud SQL Unix socket exposed to the Cloud Run container. Local development continues to use standard PostgreSQL host and port configuration.

Runtime credentials are injected from Secret Manager rather than stored in source code or Docker images.

Deployment flow:

```text
Source
  ↓
Cloud Build
  ↓
Backend Docker Image
  ↓
Artifact Registry
  ↓
Cloud Run
```

### Health and Readiness

The backend exposes separate health and readiness endpoints:

```text
/health
   ↓
API process health

/ready
   ↓
PostgreSQL connectivity
```

This distinction allows the application process to remain healthy while separately reporting a database dependency failure.

---

## Frontend Deployment

The production frontend is built with React, TypeScript, and Vite and served by Nginx on Cloud Run.

Nginx performs two responsibilities:

- serves the compiled React application
- proxies `/api/*` requests to the backend Cloud Run service

The backend service URL is supplied as a Docker build argument when the production frontend image is built.

Deployment flow:

```text
React + TypeScript
  ↓
Vite Production Build
  ↓
Nginx Docker Image
  ↓
Artifact Registry
  ↓
Cloud Run
```

This keeps the browser-facing application independent from the backend deployment while allowing frontend requests to use the `/api` route.

---

## Database Migration

The existing PostgreSQL database was migrated to Cloud SQL rather than rebuilding the recipe corpus or regenerating embeddings.

The migration preserved:

- 50,514 recipes
- 50,514 existing embeddings
- 1536-dimensional vector data
- pgvector-backed retrieval data
- recipe indexes

The production Cloud SQL instance runs PostgreSQL 16 with pgvector enabled.

Reusing the existing corpus avoided unnecessary embedding regeneration and preserved the already validated retrieval dataset.

---

## Secrets and Production Access

Production secrets are not stored in the Git repository or baked into container images.

Secret Manager stores:

- the PostgreSQL database password
- the OpenAI API key

The backend Cloud Run service receives the required secrets at runtime.

A dedicated backend service account provides access to required GCP resources through IAM rather than embedding cloud credentials in application code.

---

## Continuous Integration

GitHub Actions provides continuous integration for pushes and pull requests targeting `main`.

The pipeline validates:

- backend CI-safe regression tests
- frontend ESLint checks
- frontend production build

Integration tests that depend on PostgreSQL, pgvector, or live external services remain separate from the CI-safe suite.

---

## Deployment Strategy

Production deployment remains manual for MealMuse V1.

The production delivery path is:

```text
GitHub
   ↓
Validated Source
   ↓
Cloud Build
   ↓
Artifact Registry
   ↓
Manual Cloud Run Deployment
```

Automated continuous deployment is intentionally deferred.

MealMuse is currently a single-developer project with infrequent production deployments. Adding deployment triggers and additional deployment credentials would introduce operational complexity without solving a current product requirement.

Automated CD can be introduced if deployment frequency or team requirements increase.

---

## Production Validation

The deployed system has been validated across the complete production request path.

### Infrastructure

Validated:

- Cloud Run frontend availability
- Cloud Run backend availability
- `/health`
- `/ready`
- Cloud Run-to-Cloud SQL connectivity
- runtime secret injection
- frontend-to-backend Nginx proxying

### Application Workflows

Validated:

- meal recommendation
- direct recipe search
- deterministic recipe-detail retrieval
- clarification handling
- no-result handling

### AI and Retrieval

Validated:

- OpenAI tool selection
- structured tool arguments
- query embedding generation
- PostgreSQL structured retrieval
- pgvector semantic retrieval
- hybrid candidate retrieval
- deterministic hard filtering
- deterministic ranking

### Reliability and Debugging

Validated:

- request IDs
- request latency logging
- production log inspection
- controlled dependency-failure behavior
- database readiness failure behavior
- dependency recovery

### Performance

The deployed backend was exercised under load to establish production behavior and identify potential bottlenecks.

Performance work followed an evidence-based approach:

```text
Measure
   ↓
Observe
   ↓
Identify Bottleneck
   ↓
Optimize Only If Justified
```

Additional caching or infrastructure was not introduced solely for technology breadth.

### Final Regression

A final production regression validated:

```text
Browser
   ↓
Cloud Run Frontend
   ↓
Nginx /api Proxy
   ↓
Cloud Run Backend
   ↓
OpenAI + Application Orchestration
   ↓
PostgreSQL + pgvector
   ↓
Filtering / Ranking
   ↓
Response
   ↓
React UI
```

Health/readiness, recommendation, recipe search, recipe-detail retrieval, clarification behavior, frontend rendering, and production logs were successfully revalidated after the final frontend deployment.

Detailed test and validation evidence is maintained in [`testing.md`](testing.md).

---

## V1 Deployment Status

MealMuse V1 is deployed and production-validated.

The current deployment includes:

- independently deployed frontend and backend services
- managed PostgreSQL + pgvector
- migrated production recipe and embedding corpus
- containerized application builds
- managed runtime secrets
- least-privilege backend service identity
- health and readiness endpoints
- continuous integration
- production logging
- load and performance validation
- final end-to-end production regression

Continuous deployment remains a documented future improvement rather than a requirement for the current single-developer V1.