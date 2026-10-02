import documentLoader
import embeddingManager

res = documentLoader.load_all_docs(r"./doc_files")
# print(len(res))
embeddings = embeddingManager.Embeddings()
embs = embeddings.chunk_documents(res)
print(f"embs: {embs.__len__()}")
