from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing_extensions import List, Any
import numpy as np


class Embeddings:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2" ):
        self.model_name = model_name
        self.model = None
        self._load_model()
        
    def _load_model(self):
        try:
            self.model = SentenceTransformer(self.model_name)
            print(f"Model Dimension : {self.model.get_embedding_dimension()}")
        except Exception as e:
            print(f"Error Loading Model: {self.model_name} : {e}")
            raise ValueError("Model Cannot Be Loaded...")
        
    def chunk_documents(self, docs: List[Any], chunk_size: int = 1000, chunk_overlap: int = 200)->List[Any]:
        splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", ""],
            chunk_size=chunk_size,
            chunk_overlap = chunk_overlap,
            length_function = len
        )
        chunks =  splitter.split_documents(docs)
        print(f"Splitted {len(docs)} into {len(chunks)} chunks")
        return chunks
    
    def embed_chunks(self, chunks: List[Any]):
        texts = [chunk.page_content for chunk in chunks]
        embeddings = self.generate_embeddings(texts)
        print(f"Embeddings shape{embeddings.shape}")
        return embeddings
    
    def generate_embeddings(self, texts: list[str])->np.ndarray:
        try:
            encodings = self.model.encode(texts, show_progress_bar=True)
            return encodings
        except Exception as e :
            print(e)

    def get_embedding_dimension(self):
        if not self.model:
            raise ValueError("Model Doesn't Exist")
        return self.model.get_embedding_dimension()

