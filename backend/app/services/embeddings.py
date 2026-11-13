from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2


@lru_cache(maxsize=1)
def _get_embedding_function() -> ONNXMiniLM_L6_V2:
    try:
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
    except ImportError as error:
        raise RuntimeError("RAG dependencies are not installed") from error

    cache_dir = os.getenv("CHROMA_ONNX_CACHE_DIR")
    if cache_dir:
        cache_path = Path(cache_dir)
        if not cache_path.is_absolute():
            cache_path = Path(__file__).resolve().parents[2] / cache_path
        ONNXMiniLM_L6_V2.DOWNLOAD_PATH = cache_path.resolve()

    return ONNXMiniLM_L6_V2()


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [[float(value) for value in embedding] for embedding in _get_embedding_function()(texts)]
