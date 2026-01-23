# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Docker Development (Recommended)
```bash
make dcdev          # Start all services with watch mode
make up             # Start services in background
make down           # Stop services
make logs           # View logs
make build          # Rebuild Docker images
```

### Backend (Python/uv)
```bash
cd backend
make dev            # Start dev server (port 8010, hot reload)
make test           # Run tests with coverage
make format         # Format with ruff
make lint           # Lint with ruff + mypy
make db-migrate     # Generate Alembic migration (autogenerate)
make db-upgrade     # Apply migrations
make celery         # Start Celery worker
```

### Frontend (pnpm)
```bash
cd frontend
pnpm dev            # Vite dev server (port 5173)
pnpm build          # TypeScript compile + Vite build
pnpm lint           # Biome check with auto-fix
pnpm generate-client  # Regenerate OpenAPI TypeScript client
npx playwright test   # Run E2E tests
```

### Regenerating Frontend API Client
When backend API changes:
```bash
cd backend && make dev   # Ensure backend running
cd frontend && pnpm generate-client
```

## Architecture

TraceWeaver is a personal data management platform using **Hexagonal Architecture**:

```
Data Sources (Git, Dayflow, SiYuan)
↓
Connectors (adapters implementing BaseConnector)
↓
Activity (unified data model)
↓
Services (SyncService, EmbeddingService)
↓
PostgreSQL + pgvector (storage + vector search)
↓
RAG → LLM (semantic search, report generation)
```

### Key Abstractions

- **BaseConnector** (`backend/app/connectors/base.py`): Interface for data source adapters. Implement `validate_config()` and `fetch_activities()`.
- **ConnectorRegistry** (`backend/app/connectors/registry.py`): Factory for connector instantiation.
- **Activity** (`backend/app/models/activity.py`): Unified model for all data sources. Uses `fingerprint` for deduplication, `extra_data` (JSONB) for source-specific
fields.
- **ActivityEmbedding**: Vector storage with pgvector for semantic search.
- **CRUDBase** (`backend/app/crud/base.py`): Generic CRUD operations. Extend for custom queries.

### Layer Structure

- `api/routes/` → Route handlers (use CRUD objects, not raw SQL)
- `services/` → Business logic (SyncService, EmbeddingService)
- `connectors/` → Data source adapters
- `crud/` → Database operations
- `models/` → SQLModel ORM models
- `schemas/` → Pydantic DTOs

## Critical Conventions

### Python Type Annotations
```python
# ✅ Correct
from typing import Optional
def foo(x: Optional[int] = None) -> Optional[str]:

# ❌ Wrong - do not use union syntax
def foo(x: int | None = None) -> str | None:
```

### Database: No Foreign Key Constraints
```python
# ✅ Virtual FK with index only
user_id: str = Field(index=True)

# ❌ Never use actual FK constraints
user_id: str = Field(foreign_key="user.id")
```

### Alembic Migrations
**Never auto-generate migration scripts.** When models change, remind user to run:
```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### ORM: Sync Sessions
Use synchronous `Session`, not `AsyncSession`:
```python
from sqlmodel import Session, select
with Session(engine) as session:
result = session.exec(select(Activity).where(...)).all()
```

### Logging
Use loguru:
```python
from loguru import logger
logger.info("User {user_id=} synced")
logger.exception(f"{e=}")
```

### Frontend: Generated Client Only
```typescript
// ✅ Use generated types and services
import type { Activity } from '@/client/types.gen'
import { ActivitiesService } from '@/client'

// ❌ Never manually define API types or use raw fetch
interface Activity { ... }  // forbidden
fetch('/api/v1/...')        // forbidden
```

### CRUD Pattern
```python
# ✅ Use CRUD objects in routes
from app.crud.activity import activity_crud
activities = activity_crud.get_multi(session, skip=0, limit=20)

# ❌ Avoid raw queries in route handlers
session.exec(select(Activity).offset(0).limit(20))
```

## Adding a New Data Source

1. Create connector in `backend/app/connectors/impl/`
2. Implement `BaseConnector` interface (`source_type`, `validate_config()`, `fetch_activities()`)
3. Register in `backend/app/connectors/registry.py`
4. Add Pydantic config schema in `backend/app/schemas/`

## Vector Embeddings (Agno Framework)

- Embedder abstraction supports OpenAI, Ollama, HuggingFace
- Text chunking → batch embedding → ActivityEmbedding storage
- Similarity search: `1 - (embedding <=> query_embedding)` via pgvector
- Switching embedder models requires re-vectorizing all data