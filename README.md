# MealMuse

MealMuse is an ingredient-aware meal recommendation system that helps users decide what to cook based on the ingredients they already have, along with their preferences and constraints.

The project is being built as an end-to-end **Agentic AI system**, combining LLM-based intent understanding with deterministic retrieval, filtering, and ranking.

## Current Features

- Natural-language meal requests
- Structured intent extraction using an LLM
- Ingredient-aware recipe retrieval
- Hard-constraint filtering
  - Required ingredients
  - Excluded ingredients
  - Time constraints
- Deterministic recipe ranking
- Top-5 meal recommendations
- Nutrition and recipe metadata
- Clarification handling for underspecified requests
- FastAPI backend with structured request/response models
- Automated unit and API tests
- Recipe processing pipeline for 50K+ recipes

## Current Recommendation Pipeline

```text
User Request
     ↓
FastAPI
     ↓
LLM Intent Extraction
     ↓
Structured Parsed Intent
     ↓
Candidate Recipe Retrieval
     ↓
Hard-Constraint Filtering
     ↓
Deterministic Ranking
     ↓
Top 5 Recommendations
```

## Tech Stack

**Current**
- Python 3.12
- FastAPI
- Pydantic
- OpenAI API
- Pytest

**Planned**
- React + TypeScript
- PostgreSQL + pgvector
- Redis
- Agent orchestration
- Docker + Kubernetes
- GCP
- CI/CD
- OpenTelemetry
- Prometheus + Grafana

## Project Status

🚧 **Active development**

The initial end-to-end recommendation pipeline is complete. Upcoming work includes hybrid vector retrieval, PostgreSQL/pgvector integration, agent orchestration, frontend development, caching, observability, CI/CD, and cloud deployment.

## Goal

Build MealMuse into a production-grade Agentic AI application while exploring the engineering required to take an AI system from prototype to a reliable, observable, tested, and deployed product.
