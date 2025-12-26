from typing import List, Dict, Any, Optional
import os
from pathlib import Path
import faiss
import pickle
from langchain.vectorstores import FAISS, Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document as LangchainDocument

class VectorStoreManager:
    """Manages vector store operations"""
    
    def __init__(self, config: dict):
        self.config = config
        self.vector_store_type = config['vector_store']['type']
        self.persist_directory = Path(config['vector_store']['persist_directory'])
        self.index_name = config['vector_store']['index_name']
        self.similarity_threshold = config['vector_store'].get('similarity_threshold', 0.7)
        
        # Create directory if it doesn't exist
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=config['documents'].get('embedding_model', 'text-embedding-3-small')
        )
        
    def _get_vector_store_path(self) -> Path:
        """Get the path for vector store files"""
        if self.vector_store_type == 'faiss':
            return self.persist_directory / f"{self.index_name}.faiss"
        else:
            return self.persist_directory
    
    def create_vector_store(self, documents: List[LangchainDocument]) -> FAISS:
        """Create a new vector store from documents"""
        if self.vector_store_type == 'faiss':
            vector_store = FAISS.from_documents(documents, self.embeddings)
            # Save to disk
            vector_store.save_local(str(self._get_vector_store_path()))
        else:
            vector_store = Chroma.from_documents(
                documents,
                self.embeddings,
                persist_directory=str(self._get_vector_store_path())
            )
            vector_store.persist()
        
        return vector_store
    
    def load_vector_store(self) -> Optional[FAISS]:
        """Load existing vector store from disk"""
        try:
            vector_store_path = self._get_vector_store_path()
            
            if not vector_store_path.exists():
                return None
                
            if self.vector_store_type == 'faiss':
                vector_store = FAISS.load_local(
                    str(vector_store_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                vector_store = Chroma(
                    persist_directory=str(vector_store_path),
                    embedding_function=self.embeddings
                )
            
            return vector_store
            
        except Exception as e:
            print(f"Error loading vector store: {str(e)}")
            return None
    
    def update_vector_store(self, documents: List[LangchainDocument]) -> FAISS:
        """Update existing vector store with new documents"""
        vector_store = self.load_vector_store()
        
        if vector_store is None:
            return self.create_vector_store(documents)
        
        # Add new documents
        if self.vector_store_type == 'faiss':
            vector_store.add_documents(documents)
            vector_store.save_local(str(self._get_vector_store_path()))
        else:
            vector_store.add_documents(documents)
            vector_store.persist()
        
        return vector_store
    
    def similarity_search(
        self,
        query: str,
        vector_store: FAISS,
        k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[LangchainDocument]:
        """Perform similarity search"""
        if filter_dict:
            # Apply filters if provided
            results = vector_store.similarity_search(
                query,
                k=k,
                filter=filter_dict
            )
        else:
            results = vector_store.similarity_search(query, k=k)
        
        # Filter by similarity threshold if specified
        if self.similarity_threshold > 0:
            if self.vector_store_type == 'faiss':
                # Get similarity scores
                docs_with_scores = vector_store.similarity_search_with_score(query, k=k)
                results = [
                    doc for doc, score in docs_with_scores
                    if 1 - score >= self.similarity_threshold  # FAISS returns distance
                ]
        
        return results
    
    def get_document_metadata(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific document"""
        vector_store = self.load_vector_store()
        if not vector_store:
            return None
        
        try:
            doc = vector_store.docstore.search(doc_id)
            return doc.metadata if doc else None
        except:
            return None
    
    def clear_vector_store(self) -> None:
        """Clear the vector store"""
        vector_store_path = self._get_vector_store_path()
        
        if self.vector_store_type == 'faiss':
            # Remove FAISS index files
            for ext in ['.faiss', '.pkl']:
                file_path = vector_store_path.with_suffix(ext)
                if file_path.exists():
                    file_path.unlink()
        else:
            # Remove Chroma directory
            import shutil
            if vector_store_path.exists():
                shutil.rmtree(vector_store_path)
    
    def get_vector_store_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        vector_store = self.load_vector_store()
        if not vector_store:
            return {
                'status': 'not_found',
                'document_count': 0
            }
        
        try:
            if self.vector_store_type == 'faiss':
                doc_count = len(vector_store.docstore._dict)
                index_size = os.path.getsize(str(self._get_vector_store_path().with_suffix('.faiss')))
                return {
                    'status': 'loaded',
                    'document_count': doc_count,
                    'index_size': index_size,
                    'index_type': 'faiss'
                }
            else:
                doc_count = vector_store._collection.count()
                return {
                    'status': 'loaded',
                    'document_count': doc_count,
                    'index_type': 'chroma'
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'document_count': 0
            }