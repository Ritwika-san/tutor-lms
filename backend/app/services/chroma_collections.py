from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chromadb.api import ClientAPI
    from chromadb.api.models.Collection import Collection


def get_cosine_collection(client: ClientAPI, name: str) -> Collection:
    collection = client.get_or_create_collection(
        name=name,
        configuration={"hnsw": {"space": "cosine"}},
    )
    space = collection.configuration.get("hnsw", {}).get("space")
    if space != "cosine":
        raise RuntimeError(
            f"Chroma collection {name!r} uses {space!r}; recreate it with cosine space and reindex its documents."
        )
    return collection


def cosine_similarity_from_distance(distance: float) -> float:
    return 1.0 - distance
