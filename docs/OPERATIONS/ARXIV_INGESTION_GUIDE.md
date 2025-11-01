# General Ingestion & Enrichment Guide

> **Note:** For ArXiv and large-scale ingestion, use `main_ingestor.py` (not `main.py`). The `main.py` script is primarily for legacy or AiPickle ingestion. All examples below use `main_ingestor.py` unless otherwise noted.

## 1. Introduction
This guide explains how to ingest and enrich large-scale datasets (e.g., ArXiv, AiPickle) using the DocScope/DocTrove pipeline. It covers supported formats, configuration, running ingestion, monitoring, enrichment, and troubleshooting.

---

## 2. System Architecture

**Data Flow:**
```
Data File (JSON/Pickle) → DataFrame → Transformers → Database → Enrichment (Embeddings, 2D Projections)
```

**Key Components:**
- `main_ingestor.py`: Main entry point for ArXiv and large-scale ingestion
- `ingestor.py` / `json_ingestor.py`: Loads data from file
- `transformers.py` / `generic_transformers.py`: Transforms data to canonical format
- `db.py`: Handles database operations
- `source_configs.py`: Field mapping/configuration for each source
- `event_listener.py` (enrichment): Listens for new papers, triggers embedding & 2D projection

---

## 3. Preparing Your Data

### Supported Formats
- **JSON** (array or lines format)
- **Pickle** (legacy, for AiPickle)

### Example Structures
**ArXiv JSON:**
```json
{
  "id": "2401.00001",
  "title": "Paper Title",
  "abstract": "Paper abstract...",
  "authors": ["Author 1", "Author 2"],
  "categories": ["cs.AI", "cs.LG"],
  "created": "2024-01-01"
}
```
**AiPickle:**
```python
{
  'Link': 'unique_id',
  'Title': 'Paper Title',
  'Summary': 'Abstract',
  'Authors': ['Author 1', 'Author 2'],
  'Date': '2024-01-01',
  ...
}
```

### Field Mapping & Source Config
- See `doc-ingestor/source_configs.py` for all supported fields and mappings.
- Add new configs for new sources as needed.

---

## 4. Running Ingestion

### Command-Line Usage
- **Standard (small files):**
  ```bash
  python doc-ingestor/main_ingestor.py arxiv_data.json --source arxiv --limit 1000
  ```
- **Large files (streaming mode):**
  ```bash
  python doc-ingestor/main_ingestor.py arxiv_data.json --source arxiv --streaming
  # Optional: --batch-size 5000 --limit 10000
  ```
- **AiPickle (legacy):**
  ```bash
  python doc-ingestor/main.py --source aipickle --file-path aipickle_data.pkl
  ```

### Key Flags
- `--source`: Data source (arxiv, aipickle, etc.)
- `--streaming`: Enable memory-efficient streaming for large files
- `--limit`: Ingest only N records (for testing)
- `--batch-size`: Set custom batch size (default is auto)

---

## 5. Monitoring Progress
- Progress is logged to the console and log files (see `ingestion.log`)
- Check database counts:
  ```bash
  psql -d doctrove -c "SELECT COUNT(*) FROM doctrove_papers;"
  ```
- For large ingestions, use `tail -f ingestion.log` to monitor live progress

---

## 6. Enrichment Pipeline (Embeddings & 2D Projections)

### Overview
- **Event-driven:** New papers trigger enrichment automatically
- **Embeddings:** Generated in batches using Azure OpenAI API (fast, efficient)
- **2D Projections:** Generated locally using UMAP (very fast)

### Running the Enrichment Service
- Start the event listener (recommended: in a new terminal tab):
  ```bash
  cd embedding-enrichment
  source ../arxivscope/bin/activate
  python event_listener.py
  ```
- The service will automatically process all papers missing embeddings or 2D projections.
- Progress and status are logged to the console and `enrichment.log`.

---

## 7. Performance & Troubleshooting

### Performance Tips
- Always use `--streaming` for files >100K records
- Monitor memory and CPU usage (`htop`, `ps aux | grep python`)
- Use incremental enrichment (default) for large datasets
- Adjust batch size if needed for your hardware/API limits

### Common Issues
- **Out of Memory:** Use `--streaming`
- **Slow Processing:** Increase `--batch-size` or run on a faster machine
- **Database Connection Issues:** Check `max_connections` in PostgreSQL
- **API Rate Limits:** Reduce batch size or add delay between batches

---

## 8. Performance and Cost Estimates

### Embedding Generation (Batch Processing)
- **Speed:** ~50,000 papers per hour (title + abstract) using Azure OpenAI API
- **Cost:** $10 per million papers (conservative estimate)
- **Examples:**
  - 1M papers: ~20 hours, $10
  - 5M papers: ~100 hours, $50
  - 10M papers: ~200 hours, $100

These estimates assume typical scientific metadata lengths and continuous operation. Actual performance may vary with text length, API rate limits, or infrastructure changes.

---

## 9. Quick Start Checklist
1. Prepare your data file (JSON or pickle)
2. Choose the correct source config (see `source_configs.py`)
3. Run ingestion with appropriate flags (use `main_ingestor.py` for ArXiv/large-scale)
4. Start the enrichment event listener
5. Monitor progress in logs and database
6. Validate results (check for embeddings and 2D projections)

---

## 10. Best Practices
- Test with a small batch before full ingestion
- Always monitor logs for errors or warnings
- Backup your database before large ingestions
- Use dedicated hardware or a cloud VM for very large datasets
- Keep your source configs up to date for new data formats

---

## 10. Support
For help, contact the DocScope/DocTrove maintainers or check the project documentation. 