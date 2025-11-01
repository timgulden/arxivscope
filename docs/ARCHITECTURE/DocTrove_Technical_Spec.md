# DocTrove Technical Specification

## 1. Overview
DocTrove is a modular, service-oriented backend platform for ingesting, enriching, embedding, and semantically searching large document corpora. It is designed to support multiple front-end applications (starting with DocScope) and to enable extensible enrichment and search capabilities over tens of millions of documents.

## 2. System Architecture
- **Cloud Platform:** Azure (preferred)
- **Containerization:** Docker for all services
- **Orchestration:** Azure Container Apps (initially; future migration to Kubernetes possible)
- **Database:** PostgreSQL with pgvector extension for vector search
- **Programming Language:** Python (all services and enrichment modules)
- **Pattern:** Interceptor stack for service logic and error handling

### 2.1. Core Services
- **doc-ingestor:** Ingests documents from sources (ArXiv, RAND, PubMed, etc.) and normalizes metadata.
- **doc-embedder:** Stateless service for generating semantic embeddings (OpenAI/Azure OpenAI, future: arbitrary models).
- **enrichment-service:** Applies enrichment modules (Python) to documents, writing results to namespace-specific tables.
- **doctrovequery-api:** FastAPI-based REST API for querying documents by metadata, enrichment, and semantic similarity.
- **PostgreSQL + pgvector:** Central data store for documents, embeddings, and enrichment metadata.

## 3. Data Model
### 3.1. Main Table: `doctrove_papers`
- `doctrove_paper_id` (UUID, PK)
- `doctrove_source` (TEXT)
- `doctrove_source_id` (TEXT)
- `doctrove_title` (TEXT)
- `doctrove_abstract` (TEXT)
- `doctrove_authors` (TEXT[])
- `doctrove_date_posted` (DATE)
- `doctrove_date_published` (DATE)
- `doctrove_title_embedding` (VECTOR(1536))
- `doctrove_abstract_embedding` (VECTOR(1536))
- `embedding_model_version` (TEXT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)
- **Unique:** (`doctrove_source`, `doctrove_source_id`)

### 3.2. Enrichment Metadata Tables
- One table per enrichment module (e.g., `arxivscope_metadata`)
- All have `doctrove_paper_id` (FK) and enrichment-prefixed fields

### 3.3. Enrichment Registry
- `enrichment_name` (TEXT, PK)
- `table_name` (TEXT)
- `description` (TEXT)
- `fields` (JSONB)
- `created_at`, `updated_at` (TIMESTAMP)

## 4. API Design
- **Framework:** Flask (DocTrove API) with interceptor stack
- **Versioning:** All endpoints under `/api/v1/`; additive changes preferred, deprecations documented
- **Documentation:** Source of truth in `doctrove-api/API_DOCUMENTATION.md`
- **Endpoints (representative):**
  - `GET /api/v1/query` — filter by metadata, enrichment, semantic similarity
  - `POST /api/v1/query` — text/embedding search with filters
  - `GET /api/v1/health` and `/api/v1/health/system`
- **Usage Tracking:** Log API calls for future analytics
- **Rate limiting:** None (internal use); performance interceptors log and enforce SLOs

## 5. Embedding & Enrichment
- **Embedding:**
  - Default: Azure OpenAI `text-embedding-3-small` (1536 dims)
  - All embeddings tagged with model version
  - Future: Support for arbitrary embedding models
- **Enrichment:**
  - Python modules, statically deployed
  - Each writes to its own metadata table
  - Registry tracks available enrichments

## 6. Service Communication
- **Primary:** REST APIs between services
- **Async Processing:**
  - Prefer asynchronous enrichment/embedding
  - REST-triggered jobs, with future option for Azure Service Bus if needed

## 7. Deployment & Infrastructure
- **Azure Container Apps** for service orchestration
- **Docker Compose** for local development
- **PostgreSQL with pgvector** (Azure Database for PostgreSQL)
- **Logging:** stdout/stderr (MVP), Azure Monitor (future)
- **Monitoring:** Azure Monitor (future)

## 8. Authentication & Security
- **MVP:** Internal/trusted use only
- **Future:** Azure SSO integration
- **Access Control:** Enrichment-level write permissions (future)
- **Data Privacy:** No PII/compliance requirements for MVP; future separation of public/non-public data

## 9. Testing & CI/CD
- **Approach:** Functional programming style, unit and integration tests for all logic
- **CI/CD:** To be established (recommend GitHub Actions or Azure Pipelines)

## 10. Scalability & Performance
- **Initial Scale:** 10,000+ documents
- **Target Scale:** Tens of millions of documents
- **API Performance (current SLOs):**
  - Typical response times: 50–200 ms for common queries
  - Batch endpoints and indexes ensure sub-second latency under normal load
  - Large aggregations may be paginated; prefer streaming where applicable
- **Async jobs:** Embedding/enrichment can be batched and run independently

## 11. Front-End Integration
- **First Client:** DocScope
- **Future:** Support for multiple front-ends
- **CORS:** Not required for MVP

## 12. Glossary
- **Interceptor:** Data structure with enter/leave/error functions for composable service logic
- **Enrichment Module:** Python code that adds metadata to documents
- **Embedding:** Vector representation of document text for semantic search
- **Namespace:** Isolated enrichment context (e.g., arxivscope, randstructure)

---

*This document is a living specification and should be updated as requirements evolve or implementation details are refined.* 