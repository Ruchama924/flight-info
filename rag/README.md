# RAG — Ollama + knowledge ingest (Slice 0 + Slice 4)

Local LLM server and knowledge base for the FlightAdvisor travel advisor.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

## 1. Start Ollama

From this directory (`rag/`):

```powershell
docker compose up -d
docker compose ps
```

You should see `flight-advisor-ollama` with state **running**.

## 2. Pull models

Pull the small chat model (generation):

```powershell
docker exec -it flight-advisor-ollama ollama pull llama3.2:1b
```

Pull the embedding model (required for RAG ingest + retrieval):

```powershell
docker exec -it flight-advisor-ollama ollama pull nomic-embed-text
```

Optional larger chat model:

```powershell
docker exec -it flight-advisor-ollama ollama pull phi3
```

## 3. Smoke-test chat generation

```powershell
curl http://localhost:11434/api/generate -d "{\"model\": \"llama3.2:1b\", \"prompt\": \"Say hello in one sentence.\", \"stream\": false}"
```

## 4. One-time knowledge ingest (Slice 4)

Embeds every file in `knowledge/` into a local ChromaDB store at `chroma_db/`.

```powershell
cd rag
py -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\python.exe ingest.py
```

Re-run `ingest.py` whenever you edit knowledge files.

## Knowledge topics

- Economy vs Premium Economy vs Business
- Layover and connection risk
- Baggage allowance basics
- Airport check-in and security timing
- What is a Codeshare flight
- Flight delay and cancellation basics

## Stop the container

```powershell
docker compose down
```

To also wipe downloaded models:

```powershell
docker compose down -v
```
