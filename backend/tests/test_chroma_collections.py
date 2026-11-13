import chromadb
import pytest

from app.services.chroma_collections import (
    cosine_similarity_from_distance,
    get_cosine_collection,
)


def test_new_collection_uses_cosine_space(tmp_path):
    client = chromadb.PersistentClient(path=str(tmp_path))

    collection = get_cosine_collection(client, "cosine-test")

    assert collection.configuration["hnsw"]["space"] == "cosine"


def test_existing_l2_collection_must_be_recreated(tmp_path):
    client = chromadb.PersistentClient(path=str(tmp_path))
    client.get_or_create_collection("legacy", metadata={"hnsw:space": "l2"})

    with pytest.raises(RuntimeError, match="recreate it with cosine"):
        get_cosine_collection(client, "legacy")


def test_cosine_similarity_is_one_minus_distance_without_clipping():
    assert cosine_similarity_from_distance(0.2) == pytest.approx(0.8)
    assert cosine_similarity_from_distance(1.2) == pytest.approx(-0.2)
