import os
import logging
from typing import List
from document_manager.models import SiteSetting
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

MAX_CHARS = 32000

def _normalize_text_input(text: str) -> list[str]:
    """
    Ensure we return a list of clean strings suitable for OpenAI embeddings.
    Raises ValueError for invalid inputs.
    """
    if text is None:
        raise ValueError("Embedding input is None")

    if not isinstance(text, str):
        # try to coerce bytes -> str
        if isinstance(text, (bytes, bytearray)):
            try:
                text = text.decode("utf-8", errors="ignore")
            except Exception:
                raise ValueError(f"Item is not a string and cannot be decoded.")
        else:
            print(text)
            raise ValueError(f"Item is not a string (type={type(text)}).")

    # strip nulls and trim
    text = text.replace("\x00", " ").strip()
    if not text:
        raise ValueError(f"Item is empty after stripping.")
    # truncate to MAX_CHARS (prefer token-aware truncation later)
    if len(text) > MAX_CHARS:
        logger.warning("Truncating input to %d chars for embeddings", MAX_CHARS)
        item = item[:MAX_CHARS]
    normalized = text

    return normalized

def get_openai_embedding(text: str) -> List[float]:
    """
    Returns a single embedding vector for text using OpenAI.
    """
    
    client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

    input = _normalize_text_input(text)


    resp = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=input
    )

    embeddings = resp.data[0].embedding
    return embeddings

    
def get_ollama_embedding(text: str, model: str = "your-ollama-model") -> List[float]:
    """
    Example placeholder for Ollama/local embeddings.
    Implementation depends on how you run Ollama (HTTP API, CLI, etc).
    Replace this with the exact request to your local Ollama instance.
    """
    import requests
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")  # adjust if needed
    # NOTE: adjust path & payload according to your Ollama setup
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/embeddings",
            json={"model": model, "input": text},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        # adapt based on Ollama's actual response shape:
        # e.g., data["embedding"] or data["data"][0]["embedding"]
        return data["embedding"]
    except Exception as e:
        logger.exception("Ollama embedding failed")
        raise

def get_embedding(text: str) -> List[float]:
    """
    Dispatch to the configured provider.
    """
    provider = SiteSetting.get_provider()
    if provider == "openai":
        return get_openai_embedding(text)
    elif provider == "ollama":
        return get_ollama_embedding(text)
    else:
        raise RuntimeError(f"Unknown embedding provider: {provider}")