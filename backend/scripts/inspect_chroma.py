"""Quick script to inspect ChromaDB contents."""

import chromadb
from pathlib import Path

CHROMA_PATH = "./chroma_data"

def inspect_chroma():
    """Display all data stored in ChromaDB."""
    print(f"Connecting to ChromaDB at: {CHROMA_PATH}\n")
    
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collections = client.list_collections()
        
        if not collections:
            print("❌ No collections found in ChromaDB")
            return
        
        print(f"✓ Found {len(collections)} collection(s):\n")
        
        for collection in collections:
            print(f"📦 Collection: {collection.name}")
            print(f"   Metadata: {collection.metadata}")
            
            # Get all documents in this collection
            all_docs = collection.get(include=["documents", "metadatas", "embeddings"])
            
            print(f"   Total documents: {len(all_docs['ids'])}\n")
            
            for idx, doc_id in enumerate(all_docs['ids'], 1):
                print(f"   [{idx}] ID: {doc_id}")
                print(f"       Document: {all_docs['documents'][idx-1][:150]}...")
                print(f"       Metadata: {all_docs['metadatas'][idx-1]}")
                if all_docs['embeddings'] is not None:
                    try:
                        embedding = all_docs['embeddings'][idx-1]
                        print(f"       Embedding: {len(embedding)} dimensions, first 3 values: {embedding[:3]}")
                    except:
                        print(f"       Embedding: Present but unable to display")
                print()
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_chroma()
