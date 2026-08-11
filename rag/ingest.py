#!/usr/bin/env python3
"""One-time RAG ingest: knowledge/*.md -> Ollama embeddings -> ChromaDB.

Run from the rag/ folder (after Ollama is up and models are pulled):

  py -m venv .venv
  .\\.venv\\Scripts\\pip.exe install -r requirements.txt
  .\\.venv\\Scripts\\python.exe ingest.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import chromadb
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("ingest")

OLLAMA_URL = "http://127.0.0.1:11434"
EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "flight_knowledge"

RAG_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = RAG_DIR / "knowledge"
CHROMA_DIR = RAG_DIR / "chroma_db"

# Human-readable topic labels used later by the advisor for transparency.
TOPIC_LABELS = {
    "economy_vs_premium_vs_business.md": "Economy vs Premium Economy vs Business",
    "layover_and_connection_risk.md": "Layover and connection risk",
    "baggage_allowance_basics.md": "Baggage allowance basics",
    "airport_checkin_and_security_timing.md": "Airport check-in and security timing",
    "what_is_a_codeshare_flight.md": "What is a Codeshare flight",
    "flight_delay_and_cancellation_basics.md": "Flight delay and cancellation basics",
}


def embed_text(text: str) -> list[float]:
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    embedding = payload.get("embedding")
    if not embedding:
        raise RuntimeError(f"No embedding in Ollama response: {payload!r}")
    return embedding


def main() -> int:
    if not KNOWLEDGE_DIR.is_dir():
        logger.error("Knowledge folder missing: %s", KNOWLEDGE_DIR)
        return 1

    files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    if not files:
        logger.error("No markdown files found in %s", KNOWLEDGE_DIR)
        return 1

    logger.info("Ingesting %d knowledge file(s) into %s", len(files), CHROMA_DIR)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # Recreate so re-running ingest replaces stale chunks cleanly.
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info("Deleted existing collection %s", COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    ids: list[str] = []
    documents: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict] = []

    for path in files:
        text = path.read_text(encoding="utf-8").strip()
        topic = TOPIC_LABELS.get(path.name, path.stem.replace("_", " ").title())
        logger.info("Embedding %s (%d chars) as topic=%s", path.name, len(text), topic)
        try:
            vector = embed_text(text)
        except requests.RequestException as exc:
            logger.error(
                "Ollama embedding failed for %s. Is Ollama running and "
                "nomic-embed-text pulled? Error: %s",
                path.name,
                exc,
            )
            return 1

        ids.append(path.stem)
        documents.append(text)
        embeddings.append(vector)
        metadatas.append({"topic": topic, "source": path.name})

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    logger.info(
        "Done. Stored %d chunk(s) in collection '%s' at %s",
        len(ids),
        COLLECTION_NAME,
        CHROMA_DIR,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
