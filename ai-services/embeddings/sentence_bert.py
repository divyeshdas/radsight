import hashlib
import json
import time
from typing import List, Optional, Dict
import numpy as np
import redis.asyncio as aioredis
from core.model_registry import registry
from core.config import get_ai_settings
import structlog

logger = structlog.get_logger(__name__)
settings = get_ai_settings()

_redis_client: Optional[aioredis.Redis] = None


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password or None,
            db=settings.redis_db,
            decode_responses=False,
        )
    return _redis_client


def _cache_key(text: str) -> str:
    digest = hashlib.sha256(text.encode()).hexdigest()[:32]
    return f"emb:{digest}"


async def _get_cached(key: str) -> Optional[np.ndarray]:
    try:
        r = get_redis()
        data = await r.get(key)
        if data:
            arr = np.frombuffer(data, dtype=np.float32)
            return arr
    except Exception:
        pass
    return None


async def _set_cached(key: str, embedding: np.ndarray) -> None:
    try:
        r = get_redis()
        await r.set(key, embedding.astype(np.float32).tobytes(), ex=settings.redis_embedding_ttl)
    except Exception:
        pass


async def generate_embedding(text: str, use_cache: bool = True) -> Dict:
    t0 = time.perf_counter()
    key = _cache_key(text)
    cache_hit = False

    if use_cache:
        cached = await _get_cached(key)
        if cached is not None:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return {
                "embedding": cached.tolist(),
                "dimension": len(cached),
                "cache_hit": True,
                "inference_ms": round(elapsed_ms, 2),
            }

    model = registry.load_sentence_model()
    truncated = " ".join(text.split()[:400])
    embedding = model.encode(truncated, show_progress_bar=False, normalize_embeddings=True)
    embedding = np.array(embedding, dtype=np.float32)

    if use_cache:
        await _set_cached(key, embedding)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    return {
        "embedding": embedding.tolist(),
        "dimension": len(embedding),
        "cache_hit": False,
        "inference_ms": round(elapsed_ms, 2),
    }


async def generate_batch_embeddings(
    texts: List[str],
    use_cache: bool = True,
    batch_size: int = 16,
) -> List[Dict]:
    results = []
    uncached_indices = []
    uncached_texts = []

    for i, text in enumerate(texts):
        if use_cache:
            key = _cache_key(text)
            cached = await _get_cached(key)
            if cached is not None:
                results.append({
                    "embedding": cached.tolist(),
                    "dimension": len(cached),
                    "cache_hit": True,
                    "inference_ms": 0.0,
                })
                continue

        results.append(None)
        uncached_indices.append(i)
        uncached_texts.append(" ".join(text.split()[:400]))

    if uncached_texts:
        t0 = time.perf_counter()
        model = registry.load_sentence_model()

        all_embeddings = []
        for i in range(0, len(uncached_texts), batch_size):
            batch = uncached_texts[i:i + batch_size]
            batch_emb = model.encode(batch, show_progress_bar=False, normalize_embeddings=True)
            all_embeddings.extend(batch_emb)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        per_ms = elapsed_ms / max(len(uncached_texts), 1)

        for j, idx in enumerate(uncached_indices):
            emb = np.array(all_embeddings[j], dtype=np.float32)
            if use_cache:
                await _set_cached(_cache_key(texts[idx]), emb)

            results[idx] = {
                "embedding": emb.tolist(),
                "dimension": len(emb),
                "cache_hit": False,
                "inference_ms": round(per_ms, 2),
            }

    return results
