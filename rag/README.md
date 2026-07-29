# RAG — Ollama (Slice 0)

Local LLM server for the FlightAdvisor travel advisor. This folder only starts Ollama and verifies it responds.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

## 1. Start the container

From this directory (`rag/`):

```bash
docker compose up -d
```

Check that the container is running:

```bash
docker compose ps
```

You should see `flight-advisor-ollama` with state **running**.

## 2. Pull a small model

Choose a lightweight model (good for local testing):

- `llama3.2:1b` — very small, fast
- `phi3` — slightly larger, still reasonable on modest hardware

Pull it inside the running container:

```bash
docker exec -it flight-advisor-ollama ollama pull llama3.2:1b
```

Or:

```bash
docker exec -it flight-advisor-ollama ollama pull phi3
```

The first pull downloads weights into the `ollama_models` Docker volume and may take a few minutes.

## 3. Test the model with curl

Send a generation request to the Ollama HTTP API:

```bash
curl http://localhost:11434/api/generate -d "{\"model\": \"llama3.2:1b\", \"prompt\": \"Say hello in one sentence.\", \"stream\": false}"
```

If you pulled `phi3`, replace the model name in the JSON:

```bash
curl http://localhost:11434/api/generate -d "{\"model\": \"phi3\", \"prompt\": \"Say hello in one sentence.\", \"stream\": false}"
```

A successful response is JSON containing a `"response"` field with generated text.

## Stop the container

```bash
docker compose down
```

To stop and remove the persisted models volume as well:

```bash
docker compose down -v
```
