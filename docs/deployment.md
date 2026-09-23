# MealMuse Deployment

## Production Architecture

MealMuse is deployed on Google Cloud Platform using separate frontend and backend Cloud Run services.

```text
Browser
   |
   v
Cloud Run - React/Nginx Frontend
   |
   | /api/*
   v
Cloud Run - FastAPI Backend
   |              |
   |              +--> OpenAI API
   |
   v
Cloud SQL - PostgreSQL + pgvector
```

Docker images are built with Google Cloud Build and stored in Artifact Registry.

## GCP Resources
- Region: us-west1
- Cloud Run:
   - mealmuse-frontend
   - mealmuse-backend
- Cloud SQL:
   - PostgreSQL 16
   - pgvector enabled
   - 50,514 recipes and embeddings
- Artifact Registry:
   - mealmuse
   - backend and frontend Docker images
- Secret Manager:
   - database password
   - OpenAI API key
- Dedicated backend service account with least-privilege Cloud SQL and Secret Manager access

## Backend Deployment

The backend runs FastAPI/Uvicorn on Cloud Run port 8080.

Production database connectivity uses the Cloud SQL Unix socket exposed to the Cloud Run container. Local development continues to use the standard PostgreSQL host and port configuration.

Runtime secrets are injected from Secret Manager rather than stored in source code or Docker images.

Deployment flow:
```text
Source
  -> Cloud Build
  -> Backend Docker image
  -> Artifact Registry
  -> Cloud Run
```

Production readiness endpoints:
- /health verifies that the API process is healthy.
- /ready verifies that the API can connect to PostgreSQL.

## Frontend Deployment

The production frontend is built as a React/Vite application and served by Nginx on Cloud Run.

Nginx serves the static frontend and proxies /api/* requests to the backend Cloud Run service.

The backend service URL is supplied as a Docker build argument when building the production frontend image.

Deployment flow:
```text
React/Vite
  -> production build
  -> Nginx Docker image
  -> Artifact Registry
  -> Cloud Run
  ```

## Database Migration

The existing PostgreSQL database was migrated rather than rebuilding the recipe corpus or regenerating embeddings.

The migration preserved:
- 50,514 recipes
- existing 1536-dimensional embeddings
- pgvector-backed retrieval data
- recipe indexes

The Cloud SQL instance uses PostgreSQL 16 with pgvector.

## Production Validation

Production deployment was validated through:
- backend health check
- database readiness check
- recommendation workflow
- direct recipe-search workflow
- recipe-detail retrieval
- clarification handling
- no-result handling
- OpenAI tool selection
- embedding generation
- pgvector retrieval
- deterministic filtering and ranking

## CI/CD decision

GitHub Actions provides continuous integration for backend tests and frontend lint/build validation.

Production deployment remains manual for V1.

Automated continuous deployment is intentionally deferred because MealMuse is currently a single-developer project with infrequent production deployments. Adding deployment triggers and additional deployment credentials would introduce complexity without solving a current product need.

Automated CD can be added as a future improvement if deployment frequency increases.