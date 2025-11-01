
NOT CLEARED FOR PUBLIC RELEASE . DO NOT CITE .
2
Team
Following the RACI model to ensure clear roles and responsibilities of a team to ensure the
execution of this effort:
• Responsible: The team that performs the work. Some specific roles to ensure are a part of
the effort:
o Subject Matter Expert (PI): Tim Gulden
o Software Engineer Lead: Lukas Standaert
§ Engineering Team: Mohammad Amadi
• Accountable: The person responsible for ensuring the execution of the effort. (Often the
product owner, the subject matter expert, or lead engineer.)
o Tim Gulden
• Consulted: Provides input and expertise.
o System Engineer (To sustain and create reusable components):
§ JC Bartel, Teresa Ko
o Subject Matter Experts (Often drawn from our target users):
§ Bill Marcellino, Sean Mann
• Informed: Individuals are kept in the loop but don’t actively participate.
o TBD
Problem Statement
What’s the problem you’re solving and why does it matter?
Questions to answer:
• What specific problem are users facing today?
• At RAND, research teams working with large corpora of documents—such as
internal publications, external literature, or data from partners—often need to enrich
these documents with customized metadata and enable sophisticated search and
retrieval capabilities. However, each project typically builds its own bespoke
ingestion, enrichment, and retrieval pipeline, resulting in duplication and
inconsistency.
• How are people solving this today?
• Most teams either hand-code one-off solutions or rely on ad hoc tools that aren’t
designed for reuse. These approaches lack standard interfaces, often involve manual
effort to manage metadata, and rarely support modern features like semantic search or
flexible query composition.
• How much does it cost (e.g., time and money)?
• This fragmented approach leads to significant redundant engineering effort, delays in
project timelines, and underutilization of prior work. It also increases technical debt
NOT CLEARED FOR PUBLIC RELEASE . DO NOT CITE .
5
• How they work now: Manually assemble RAG inputs from disparate sources or rely on
brittle scraping/downloading pipelines
• User flow with DocTrove: Use the API to retrieve filtered, semantically ranked
document sets for context injection; combine with embeddings for hybrid RAG systems
Goals & Success Metrics
Define what success looks like: qualitatively and quantitatively.
Questions to answer:
• What’s the business goal (i.e., how does this improve the efficiency or the effectiveness of
RAND research and analysis)?
• DocTrove aims to increase the efficiency, consistency, and scalability of research
infrastructure at RAND by centralizing document ingestion, enrichment, and
semantic search. By offering a shared back-end platform, it reduces redundant
engineering effort across projects, accelerates development of literature-driven tools,
and improves access to the full corpus of RAND and external research.
• What’s the user experience goal?
• For developers and technical contributors, DocTrove should be a reliable, well-
documented API that supports seamless integration into front-end tools and research
pipelines. Users should be able to query semantically enriched corpora, reuse
enrichment logic across projects, and rapidly prototype new applications without
rebuilding ingestion or indexing workflows.
• How will the solution’s success be measured (i.e., KPIs)? Note: we ask for a more detailed
description of user metrics to be collected below.
• Adoption Metrics:
§ Number of projects or applications actively using DocTrove APIs
§ Number of enrichment modules created or reused across projects
§ Growth in total documents ingested and enriched
• Efficiency Metrics:
§ Reduction in development time for new literature tools (baseline vs.
DocTrove-supported)
§ Number of duplicated ingestion/enrichment efforts avoided
§ Mean time to deploy new enrichment logic using namespace isolation
• Usage Metrics:
§ Monthly API calls by user type (developer, data scientist, LLM tool)
§ Number of semantic queries and enrichment executions
§ Frequency of updates to core corpora (e.g., ArXiv, PubMed)
• What is the timeline for development?
• Phase 1 (0–3 months): Core architecture, ingestion of ArXiv, PubMed, and RAND
metadata; initial deployment of doc-ingestor, doc-embedder, and query API
NOT CLEARED FOR PUBLIC RELEASE . DO NOT CITE .
6
• Phase 2 (3–6 months): Enrichment service with namespace support; first enrichment
modules (e.g., topic classifier, geographic tagger); integration with pilot front end
(DocScope)
• Phase 3 (6–12 months): Integration into internal tools (AskRAND, RANDChat);
expansion of enrichment registry; API stabilization and documentation for broader
adoption
Requirements
Functional
Provide a list of “must-have” and “nice-to-have” features for the MVP of your solution.
For each feature:
• Design/Layout: Provide a sketch of how you want this to look or flow
• Behavior: Describe what this feature should accomplish in the common user flows.
• Corner cases: Describe error states, how it is affected by other components, etc..
Example Features
Must Haves
• RAND authentication
• LLM-generated tags
• User editing for AI-generated tags
Nice to Haves
• Batch document editing
• Detection of tag duplication
• LLM fine-tuning based on user inputs
• Accessibility tiering (i.e., public vs. Private, accessibility based on user qualifications, etc..)
• AI Chatbot
Example Feature Description
• Tag editing (Must-have)
• Design/Layout: < Imaginary Sketch >
• Behavior: Users should be able to remove any AI-generated tags, add any tags they
like, and batch edit documents to add or remove tags across multiple documents.
• Corner cases:
§ If they add a duplicate tag, it should throw an error and ask users to clarify
their intent.
§ If the model is rerun, it should not regenerate removed tags.
NOT CLEARED FOR PUBLIC RELEASE . DO NOT CITE .
7
Must-Have Features (Back-End MVP)
1. Central Document Store with Ingestion from RAND Publications
• Design/Layout: doctrove_papers table stores normalized records; source-specific
metadata tables like rand_metadata hold auxiliary fields. Documents are deduplicated
using DOIs where available.
• Behavior: Ingestion pipeline ( doc-ingestor) loads documents from RAND metadata
sources. If a document appears in multiple sources, the first appearance populates
doctrove_papers, and all source-specific metadata is retained in respective tables.
• Corner cases:
o If a DOI is missing, fallback deduplication uses (source + source_id)
o Documents may have metadata in multiple auxiliary tables but a single core entry
o Malformed records or missing required fields are logged and skipped
2. Embedding Service via Azure OpenAI
• Design/Layout: doc-embedder service generates two embeddings per document using
Azure OpenAI API: one for title only, and one for title + abstract; embeddings are stored
in pgvector-compatible format
• Behavior: Other services call doc-embedder to embed documents; embeddings are
written into doctrove_papers as doctrove_title_embedding and
doctrove_abstract_embedding
• Corner cases:
o API rate limit or quota errors should be caught and reported to calling service
o Title-only and full embeddings should be independently retryable
o Embedding failure should not block ingestion or enrichment
3. Enrichment Service with Namespace Isolation and Overwrite-on-Update
• Design/Layout: Each enrichment module writes to a separate {enrichment}_metadata
table, linked by doctrove_paper_id. Enrichment definitions tracked in
enrichment_registry.
• Behavior: Enrichment logic (e.g., classification, tagging, geographic tagging) is scoped
to specific corpora and updates the namespace-specific table. If re-enriched, values are
overwritten.
• Corner cases:
o Missing enrichment definitions return 404 errors
NOT CLEARED FOR PUBLIC RELEASE . DO NOT CITE .
8
o Existing entries are cleanly overwritten on re-enrichment
o Errors in enrichment logic should not block unrelated documents or namespaces
4. Unified Query API (FastAPI)
• Design/Layout: REST API with endpoints for keyword search, metadata filters, and
semantic similarity search using either stored embeddings (title or full) or live text input
• Behavior: Clients can filter by source, date, enrichment fields, and semantic similarity;
results returned as ranked, paginated JSON
• Corner cases:
o Conflicting or unresolvable filter combinations return 400 with clear messages
o Unknown enrichment namespaces or fields return validation errors
o Cosine similarity queries should gracefully handle documents missing
embeddings
Nice-to-Have Features
1. Manual Triggering of Embedding and Enrichment Jobs
• Design/Layout: POST endpoints:
/api/embed/{paper_id} and
/api/enrich/{enrichment_name}?source=rand&after=2020-01-01
• Behavior: Allows selective recomputation of embeddings or enrichment for a subset of
documents
• Corner cases:
o Nonexistent paper_id or enrichment returns 404
o Multiple enrichment jobs on the same table are run sequentially
2. Embedding Model Version Metadata (Optional Tagging)
• Design/Layout: embedding_model_version stored alongside each vector (defaulted to
Azure OpenAI model ID)
• Behavior: Supports transparency and traceability of embeddings; allows for model
upgrades and reprocessing in future
• Corner cases:
o Not required for MVP behavior but logged where available
o Clients can choose which version to use if more than one exists in future
NOT CLEARED FOR PUBLIC RELEASE . DO NOT CITE .
9
3. Access Control via Token or SSO (Optional)
• Design/Layout: Token-based authentication (e.g., JWT) for internal service access;
future integration with RANDAuth or Azure SSO
• Behavior: Read-only and write privileges scoped by token permissions; enrichment
updates may be limited to authorized namespaces
• Corner cases:
o Unauthorized requests return 401 or 403 with reason
o Tokens can be configured for front-end apps with limited scopes
System
• Latency (i.e., how long should tasks take):
• Common metadata or keyword-based queries should return in under 2 seconds.
• High-volume semantic queries (e.g., 10,000 document results with filtering and
ranking) should return in under 30 seconds, assuming appropriate indexing and
hardware.
• Embedding and enrichment tasks may run asynchronously and need not be real-time;
jobs are logged and monitored for completion.
• Scale (i.e., how big are the inputs, outputs, and user base):
• MVP Scale: ~10,000 RAND publications
• Target Scale: Tens of millions of documents across sources like ArXiv, PubMed,
and RAND
• API Query Parameters:
§ batch_size (default: 1,000; max: 10,000)
§ total_results (default: 10,000; max: 100,000)
§ These allow efficient data retrieval to support front-end applications like
DocScope without repeated calls
• Designed for efficient paging and result slicing across very large document sets
• Security & Privacy & Compliance (i.e., level of classification of data):
• Comparable to the current RAND Knowledge Services (KS) infrastructure
• Supports documents that are:
§ Publicly available
§ Internal use only
§ Controlled Unclassified Information (CUI)
• Sensitive content is tagged via enrichment metadata (e.g., access_level:
internal_only or cui: true)
• Filtering by access level is available to downstream applications (e.g., front ends for
public users)
• Token-based access control is not included in the MVP, but is planned for future
development
NOT CLEARED FOR PUBLIC RELEASE . DO NOT CITE .
10
• Reliability & Availability (i.e., guarantees on uptime of the system):
• Services should be robust and recoverable, but continuous uptime is not critical
• Acceptable to schedule downtime for upgrades or reprocessing
• Designed for deployment via Docker with container-level restart and monitoring
tools (e.g., Docker Compose or Azure Container Apps)
• Platforms/Devices supported (e.g., Windows, Macs, browsers, mobile/desktop):
• DocTrove runs on Linux or Windows servers with Docker support
• Accessed via HTTP REST API, usable from:
§ Python (e.g., Jupyter notebooks)
§ Web front ends (e.g., DocScope, AskRAND)
§ CLI or scripting environments
• No direct UI; DocTrove is infrastructure for developer-facing integration
• Monitoring: Usage metrics (e.g., sign-ups per quarter, compute used per month, storage
space utilized, number of published articles mentioning solution in their methodology, etc..)
• API Usage Logs: Endpoint, timestamp, user token (if present), response time
• Database Metrics: Document count by source, embedding coverage, enrichment
status
• Storage Monitoring: Track growth of core and auxiliary tables and pgvector usage
• Standard database admin dashboards and logging tools will be used to monitor
performance and health
• A/B Testing: Experiments you plan to run.
• API performance will be tested using automated scripts designed to:
§ Retrieve the maximum number of records
§ Chain and combine filters
§ Stress test semantic similarity ranking
§ Simulate enrichment workloads
• Testing will verify system behavior under both typical and maximum load conditions
NOT CLEARED FOR PUBLIC RELEASE . DO NOT CITE .
11
Technical Overview
Provide a rough system diagram of components. If known, share potential areas of reuse of
existing code or systems. Add any principles on how updates to the product would be managed.
System Diagram:
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
NOT CLEARED FOR PUBLIC RELEASE . DO NOT CITE .
12
Competitive Analysis
Understand the competitive landscape and differentiation.
Questions to answer:
• Who are the main competitors in this space?
• How are they approaching the problem? Pros and cons of this approach?
• Similar external tools?
§ Semantic Scholar API / S2AG – Provides access to large-scale metadata and
citation graphs with embedding capabilities.
• Pros: Maintains massive, high-quality dataset and embeddings; good
for public research queries.
• Cons: Not customizable; no enrichment namespace support; limited
control over embedding logic or updates.
§ Lens.org – A powerful, structured patent and scholarly search tool.
• Pros: Rich metadata; user-friendly interface; integrated citation
network.
• Cons: Black-box enrichment; not designed for internal logic reuse or
custom application development.
§ OpenAlex – Open metadata platform replacing Microsoft Academic Graph.
• Pros: Free, well-maintained, and rich metadata.
• Cons: Does not provide embedding or enrichment services; little query
composability.
• Similar RAND internal tools?
§ RAND Knowledge Services / SharePoint Search Tools
• Pros: Integrated into internal workflows; includes controlled
vocabularies and search by metadata.
• Cons: Lacks semantic search, vector embeddings, or customizable
enrichment logic; not designed for API-level integration into modern
tools.
§ AskRAND / RANDChat Prototypes
• Pros: Provide useful semantic access to documents via LLMs.
• Cons: Typically rely on ad hoc document retrieval and are not backed
by reusable, structured document services.
• How is our approach different?
• DocTrove addresses the document ingestion and semantic infrastructure gap by
building a modular, reusable back-end service with:
§ Centralized ingestion and deduplication
§ Embedding support for semantic similarity
§ Per-project enrichment logic (via isolated metadata namespaces)
§ Composable query interface for front-end applications
• This allows DocTrove to serve as a platform for internal tool builders rather than just
another search interface.
NOT CLEARED FOR PUBLIC RELEASE . DO NOT CITE .
13
• What is our unique value proposition?
• Modular enrichment system allows project teams to define their own logic and
metadata schemas
• Centralized, deduplicated corpus avoids redundant ingestion work across teams
• Support for scalable semantic search using Azure OpenAI embeddings and
pgvector
• Designed for integration into internal tools (like DocScope, AskRAND, or AI-
enhanced research workflows)
• What are the potential disadvantages of the proposed solution concerning competitors?
• Initial corpus size and coverage may be smaller than Semantic Scholar or OpenAlex
(though can be expanded)
• Requires developer involvement to be useful — no end-user UI by default
• Limited out-of-the-box analytics or visualizations without front-end support
(DocScope, etc.)
• Requires ongoing effort to maintain ingestion pipelines and model versioning
Appendix
Since many projects are in flight, please add details on:
- Progress toward goals.
- Progress toward user journeys.
- Current users
- Distribution model
- Code repository link
- Project Page:
We do have an evolving prototype of the front end DocScope (formerly ArXivScope) which
would be the first user of DocTrove. DocTrove, however, it still just a concept.