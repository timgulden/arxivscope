DocTrove Functional Specification
A Modular Back-End Platform for Document Ingestion, Enrichment, Embedding, and
Semantic Search
1. Overview and Purpose
DocTrove is a scalable, service-oriented back-end platform for managing large collections of
structured research documents. It supports ingestion from multiple sources (e.g., ArXiv,
RAND publications, PubMed), semantic embedding for similarity search, and a highly
flexible enrichment model that allows metadata to be added, queried, and combined in
project-specific or reusable ways.
DocTrove provides a general-purpose API for retrieving and filtering documents by
keyword, metadata, and semantic similarity. It is designed to support a variety of front-end
applications, such as DocScope (which is in development) or RANDLens (which is a
hypothetical other app that would use the same API) and enrichment modules, such as
docscope (supporting DocScope) or randstructure (providing needed enrichment for the
hypothetical RANDLens) that extend the core dataset in modular ways.
2. Key Goals
- Ingest structured metadata from diverse document repositories
- Store and serve semantic embeddings for similarity-based queries
- Allow for project-defined enrichment metadata, isolated by namespace
- Support composable queries across multiple enrichment modules
- Enable reuse of enrichment logic across applications
- Provide batch and paginated access to metadata for visualization and analysis tools
3. System Architecture Overview
DocTrove is designed as a modular, service-oriented system centered around a shared
PostgreSQL database with pgvector extensions. Its core components include:
doc-ingestor – Translates source-specific formats into normalized internal records and
inserts them into the database.
enrichment-service – Identifies documents missing enriched metadata, performs the
necessary operations (e.g., geolocation, classification), and stores results in separate
namespace-specific metadata tables.
doctrovequery-api – Provides an API interface for querying documents by keyword,
metadata, and semantic similarity. It filters, ranks, and returns results in JSON format.
doc-embedder – A stateless utility service used by both the doctrovequery-api and
enrichment-service to generate vector embeddings from text. It does not interact directly
with the database.
PostgreSQL + pgvector – The central data store. It holds the core doctrove_papers
table, namespace-specific metadata tables (e.g., arxivscope_metadata), and vector
representations used for similarity search.
4. Core Data Model
doctrove_papers (Main Table):
Front-end (DocScope)
[REST API Layer]
DocTroveQuery-api
PostgreSQL + PG Vector
DocTrove_papers
DocScope_metadata
RandStrucure_metadata
...
Enrichment_registry
Enrichment_service
Embedding-serviceIngestion-service
- doctrove_paper_id (UUID): Internal document ID
- doctrove_source (TEXT): Source name (e.g., 'arxiv', 'rand', 'pubmed')
- doctrove_source_id (TEXT): Source-specific identifier
- doctrove_title (TEXT): Document title
- doctrove_abstract (TEXT): Document abstract
- doctrove_authors (TEXT[]): List of author names
- doctrove_date_posted (DATE): Date of release or posting
- doctrove_date_published (DATE): Formal publication date
- doctrove_embedding (VECTOR): Semantic embedding (pgvector)
- created_at (TIMESTAMP): System ingest timestamp
Enrichment Tables:
Each enrichment module defines its own metadata table, named
{enrichment_name}_metadata. These tables are owned and managed independently,
contain a doctrove_paper_id field as a foreign key, and all other fields are prefixed with
the enrichment name.
5. Functional Requirements
5.1 Document Ingestion (doc-ingestor)
- Scheduled or ad hoc import from sources like ArXiv API, RAND metadata CSVs, and
PubMed XML files
- Deduplicate based on doctrove_source + doctrove_source_id
- Store results in doctrove_papers and source-specific auxiliary tables
5.2 Embedding Pipeline (doc-embedder)
- Generate semantic embedding for each document using abstract/title
- Use external embedding models (OpenAI, HuggingFace, etc.)
- Called by other services; does not write to the database
5.3 Metadata Enrichment (enrichment-service)
- Enrichment modules are independent (e.g., arxivscope, randstructure)
- Each writes to its own {enrichment}_metadata table
- Can be scoped to subsets of the corpus (e.g., RAND reports before 2020)
- Enrichments may be derived via pattern matching, LLMs, or external APIs
- Calls doc-embedder for vector generation if needed
5.4 Enrichment Registry
A Postgres table that tracks known enrichment modules. Includes fields:
- enrichment_name
- table_name
- description
- fields
- created_at
6. API and Query Interface
6.1 Query API (doctrovequery-api)
This unified query interface supports filtering by metadata fields, enrichment values, and
semantic similarity. Clients may query using keyword filters, text content, or a document ID.
Results are filtered using SQL joins across metadata tables and ranked using cosine
similarity where applicable.
Examples:
GET
/api/query?arxivscope_country=CN&randstructure_division=Defense&k=100
POST /api/query { "text": "...", "filters": { "source": "arxiv" }, "k":
50 }
6.2 Embedding and Enrichment Execution
Manual triggering (optional):
POST /api/embed/{paper_id}
POST /api/enrich/{enrichment_name}?source=rand&before=2020-01-01
7. Deployment and Infrastructure
- Dockerized microservices with Docker Compose or Azure Container Apps
- PostgreSQL with pgvector for semantic search
- FastAPI for service interfaces
- Logging to stdout or Azure Monitor
8. Security and Access Control
- Internal use only (initially)
- Optional token or SSO authentication
- Enrichment-level write permissions may be implemented
9. Future Extensions
- Citation graph integration
- Visual/PDF similarity embeddings
- Embedding versioning and reprocessing
- Metadata editing and user-saved queries
10. Glossary
- doctrove_paper_id: Internal unique ID for each paper
- doctrove_*: Prefix for fields in the main document table
- {enrichment}_metadata: Per-module table for metadata enrichment
- {enrichment}_*: Prefix for enrichment-specific fields
- enrichment module: A process that derives metadata from documents
- front-end project: UI tool that consumes DocTrove data
- enrichment registry: System table tracking enrichment definitions