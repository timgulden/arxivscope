Key Questions for a Complete Technical Specification
1. Deployment & Infrastructure
•	Do you have a preferred cloud provider (Azure, AWS, GCP, on-prem)?
o	We should use the Azure platform to the extent that it makes sense.
•	Will all services run in Docker containers? Any orchestration (Docker Compose, Kubernetes, Azure Container Apps)?
o	I am not deeply familiar with these.  My guess is that Azure Container Apps make sense here – but I a not sure how to judge that.
•	Any requirements for CI/CD or automated testing?
o	I would very much like to take a functional programming approach and have tests for everything for which it makes sense.  This is not something I am accustomed to doing, but I am told that it is good practice.
2. Authentication & Security
•	Should the MVP include authentication (e.g., JWT, SSO), or is it internal/trusted use only at first?
o	Trusted only at first.  Later, it will be SSO.
•	Any data privacy or compliance requirements (PII, GDPR, etc.)?
o	At this point, there are no privacy or compliance concerns.  Some of the contents will be not for public release, but the MVP will be internal only.  Later it may become important to separate public from non-public.
3. Service Communication
•	Should services communicate only via REST APIs, or do you want to use message queues (e.g., RabbitMQ, Azure Service Bus) for ingestion/enrichment jobs?
o	I am inclined to use REST API because I understand it better.  I am open to Azure Service Bus if it offers significant advantages.
•	Any preference for synchronous vs. asynchronous processing for enrichment and embedding?
o	I would like things to be asynchronous if that can be done without too much complication.  Each service should be as independent as possible.
4. Embedding Model
•	Is OpenAI/Azure OpenAI the only embedding provider, or should we support local/HuggingFace models as well?
o	Eventually, we will want to support arbitrary embeddings.  This means that each embedding vector needs to be somehow tagged with the model that created it.
•	What embedding dimension(s) do you want to support (e.g., 1536 for OpenAI Ada)?
o	I think that we should base things on the text-embedding-3-small model, which also has 1536 dimentions.
5. Enrichment Modules
•	Will enrichment modules always be Python code, or do you want to support other languages/runtimes?
o	Lets assume that the enrichment modules always use Python code.
•	Should enrichment modules be loaded dynamically (plug-in style), or is static deployment sufficient for now?
o	Static deployment is fine.
6. API Design
•	Any requirements for OpenAPI/Swagger documentation?
o	I am not sure what this means.  We need to document things, but only for internal use.
•	Should the API be versioned from the start (e.g., /api/v1/)?
o	Yes.
•	Any rate limiting or usage tracking needed?
o	It would be useful to do usage tracking. We will not need rate limiting.
7. Data Volume & Performance
•	What is the expected initial and future scale (number of documents, queries per second)?
o	Eventual scale is planned to be tens of millions of documents.  I would like an API call to be able to find and return up to 10,000 metadata records. 
•	Any hard requirements for query latency or batch processing throughput?
o	The 10,000 record API call should return results in under a minute if possible.
8. Monitoring & Logging
•	Any preferred logging/monitoring stack (e.g., ELK, Azure Monitor, Prometheus/Grafana)?
o	Azure Monitor is probably good.
•	Should logs be centralized or is stdout/stderr sufficient for now?
o	For now, stdout/stderr is fine.
9. Front-End Integration
•	Will DocScope be the only front-end initially, or should we plan for multiple clients?
o	DocScope will be first, but the hope is to support a wide range of applications.
•	Any requirements for CORS or cross-origin API access?
o	I am not sure what that means – but probably not.
