import documentLoader
import embeddingManager

if __name__ == "__main__":
    print("\n🚀 Starting Pipeline...")

    # 1. Load Documents
    documents = documentLoader.load_all_docs(r"./doc_files")
    print(f"📦 Loaded {len(documents)} raw files.")

    # 2. Chunk Documents
    chunks = embeddingManager.Embeddings().chunk_documents(documents)
    print(f"✂️  Created {len(chunks)} text chunks.")

    # 3. Generate Embeddings
    embeddings = embeddingManager.Embeddings().embed_chunks(chunks)
    print(f"🧠 Generated vector embeddings successfully.")
    print("\n🔍 --- Embeddings Preview ---")
    print(f"Total Vectors Generated: {len(embeddings)}")
    if len(embeddings) > 0:
        print(f"Vector Dimensions (Length): {len(embeddings[0])}")
        print(f"First Vector Sample (First 5 numbers): {embeddings[0][:5]}...")
    print("🏁 Pipeline Complete!\n")
    
