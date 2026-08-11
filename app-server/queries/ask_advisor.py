from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import chromadb
import httpx

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:1b")
COLLECTION_NAME = "flight_knowledge"
TOP_K = 2
OLLAMA_TIMEOUT_SECONDS = 30.0

# app-server/queries -> app-server -> flight-info/rag/chroma_db
CHROMA_DIR = Path(__file__).resolve().parents[2] / "rag" / "chroma_db"


@dataclass(frozen=True)
class AskAdvisorQuery:
    question: str


@dataclass(frozen=True)
class AskAdvisorResult:
    answer: str
    topics_used: list[str]


class AdvisorError(Exception):
    pass


class AskAdvisorHandler:
    def handle(self, query: AskAdvisorQuery) -> AskAdvisorResult:
        question = query.question.strip()
        if not question:
            raise AdvisorError("Question must not be empty.")

        logger.info("AskAdvisor question=%r", question[:120])

        if not CHROMA_DIR.exists():
            raise AdvisorError(
                f"Knowledge base not found at {CHROMA_DIR}. "
                "Run rag/ingest.py first (with Ollama running)."
            )

        try:
            question_embedding = self._embed(question)
            chunks = self._retrieve(question_embedding)
            answer = self._generate(question, chunks)
        except AdvisorError:
            raise
        except httpx.TimeoutException as exc:
            raise AdvisorError(
                "Ollama timed out after 30s. Is the model loaded and the "
                "container running? Try again in a moment."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise AdvisorError(
                f"Ollama HTTP {exc.response.status_code}: {exc.response.text[:300]}. "
                "Ensure llama3.2:1b and nomic-embed-text are pulled."
            ) from exc
        except httpx.RequestError as exc:
            raise AdvisorError(
                f"Ollama is unavailable at {OLLAMA_URL}: {exc}. "
                "Start it with: cd rag && docker compose up -d"
            ) from exc
        except Exception as exc:
            raise AdvisorError(f"Advisor failed: {exc}") from exc

        topics = [c["topic"] for c in chunks if c.get("topic")]
        # Preserve order, drop duplicates
        seen: set[str] = set()
        topics_used: list[str] = []
        for topic in topics:
            if topic not in seen:
                seen.add(topic)
                topics_used.append(topic)

        logger.info("AskAdvisor topics_used=%s", topics_used)
        return AskAdvisorResult(answer=answer, topics_used=topics_used)

    def _embed(self, text: str) -> list[float]:
        response = httpx.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        embedding = response.json().get("embedding")
        if not embedding:
            raise AdvisorError("Ollama returned an empty embedding.")
        return embedding

    def _retrieve(self, embedding: list[float]) -> list[dict]:
        try:
            client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            collection = client.get_collection(name=COLLECTION_NAME)
        except Exception as exc:
            raise AdvisorError(
                f"Could not open ChromaDB collection '{COLLECTION_NAME}'. "
                f"Run rag/ingest.py first. Details: {exc}"
            ) from exc

        result = collection.query(
            query_embeddings=[embedding],
            n_results=TOP_K,
            include=["documents", "metadatas"],
        )
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]

        chunks: list[dict] = []
        for doc, meta in zip(documents, metadatas):
            meta = meta or {}
            chunks.append(
                {
                    "document": doc or "",
                    "topic": meta.get("topic") or meta.get("source") or "Unknown",
                }
            )

        if not chunks:
            raise AdvisorError(
                "No knowledge chunks retrieved. Re-run rag/ingest.py."
            )
        return chunks

    def _generate(self, question: str, chunks: list[dict]) -> str:
        context_blocks = []
        for i, chunk in enumerate(chunks, start=1):
            context_blocks.append(
                f"[Source {i}: {chunk['topic']}]\n{chunk['document']}"
            )
        context = "\n\n".join(context_blocks)

        prompt = (
            "You are FlightAdvisor, a helpful flight travel assistant.\n"
            "Answer the user's question using ONLY the context below when possible.\n"
            "If the context is incomplete, say what you can and note the gap briefly.\n"
            "Keep the answer concise (a short paragraph or a few bullet points).\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION: {question}\n\n"
            "ANSWER:"
        )

        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": CHAT_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        answer = (response.json().get("response") or "").strip()
        if not answer:
            raise AdvisorError("Ollama returned an empty answer.")
        return answer
