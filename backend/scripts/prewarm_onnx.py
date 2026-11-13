from pathlib import Path
import os
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.services.embeddings import embed_texts


def main() -> None:
    cache_dir = os.getenv("CHROMA_ONNX_CACHE_DIR")
    if not cache_dir:
        raise RuntimeError("CHROMA_ONNX_CACHE_DIR must point to a cache directory inside the backend")
    cache_path = Path(cache_dir)
    if not cache_path.is_absolute():
        cache_path = BACKEND_DIR / cache_path
    try:
        cache_path.resolve().relative_to(BACKEND_DIR.resolve())
    except ValueError as error:
        raise RuntimeError("CHROMA_ONNX_CACHE_DIR must be inside the backend directory") from error

    embed_texts(["Render build-time model prewarm"])
    print("ONNX embedding model prewarmed.")


if __name__ == "__main__":
    main()
