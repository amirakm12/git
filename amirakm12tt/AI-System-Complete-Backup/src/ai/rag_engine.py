"""
Retrieval-Augmented Generation (RAG) Engine
Advanced knowledge retrieval and integration system
"""

import asyncio
import logging
import os
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json
import hashlib
from dataclasses import dataclass
from enum import Enum

# Vector database and embeddings
import chromadb
from chromadb.config import Settings
import numpy as np
from sentence_transformers import SentenceTransformer
import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, PDFLoader, CSVLoader
from langchain.schema import Document

from ..core.config import SystemConfig

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Types of documents supported."""
    TEXT = "text"
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"

@dataclass
class RetrievalResult:
    """Result from knowledge retrieval."""
    content: str
    metadata: Dict[str, Any]
    relevance_score: float
    source: str
    document_id: str
    chunk_id: str

@dataclass
class QueryResult:
    """Result from RAG query."""
    query: str
    retrieved_documents: List[RetrievalResult]
    generated_response: str
    confidence_score: float
    processing_time: float
    metadata: Dict[str, Any]

class RAGEngine:
    """Retrieval-Augmented Generation Engine."""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.is_running = False
        
        # Vector database
        self.vector_db = None
        self.collection = None
        
        # Embedding model
        self.embedding_model = None
        
        # Text processing
        self.text_splitter = None
        
        # Document management
        self.documents = {}
        self.document_index = {}
        
        # Query cache
        self.query_cache = {}
        self.cache_max_size = 1000
        
        # Performance metrics
        self.metrics = {
            'total_queries': 0,
            'cache_hits': 0,
            'retrieval_times': [],
            'generation_times': []
        }
        
        logger.info("RAG Engine initialized")
    
    async def initialize(self):
        """Initialize the RAG engine."""
        logger.info("Initializing RAG Engine...")
        
        try:
            # Initialize vector database
            await self._initialize_vector_db()
            
            # Initialize embedding model
            await self._initialize_embedding_model()
            
            # Initialize text splitter
            self._initialize_text_splitter()
            
            # Load existing documents
            await self._load_existing_documents()
            
            # Initialize OpenAI client
            self._initialize_openai()
            
            logger.info("RAG Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG Engine: {e}")
            raise
    
    async def start(self):
        """Start the RAG engine."""
        logger.info("Starting RAG Engine...")
        
        try:
            # Start background tasks
            self.background_tasks = {
                'cache_cleaner': asyncio.create_task(self._cache_cleanup_loop()),
                'index_optimizer': asyncio.create_task(self._index_optimization_loop()),
                'metrics_collector': asyncio.create_task(self._metrics_collection_loop())
            }
            
            self.is_running = True
            logger.info("RAG Engine started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start RAG Engine: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the RAG engine."""
        logger.info("Shutting down RAG Engine...")
        
        self.is_running = False
        
        # Cancel background tasks
        for task_name, task in self.background_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled {task_name}")
        
        # Save cache and index
        await self._save_cache()
        await self._save_document_index()
        
        logger.info("RAG Engine shutdown complete")
    
    async def _initialize_vector_db(self):
        """Initialize ChromaDB vector database."""
        db_path = Path(self.config.rag.vector_db_path)
        db_path.mkdir(parents=True, exist_ok=True)
        
        # Configure ChromaDB
        settings = Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=str(db_path),
            anonymized_telemetry=False
        )
        
        self.vector_db = chromadb.Client(settings)
        
        # Get or create collection
        try:
            self.collection = self.vector_db.get_collection("knowledge_base")
            logger.info("Loaded existing vector database collection")
        except Exception:
            self.collection = self.vector_db.create_collection(
                name="knowledge_base",
                metadata={"description": "RAG knowledge base"}
            )
            logger.info("Created new vector database collection")
    
    async def _initialize_embedding_model(self):
        """Initialize sentence transformer embedding model."""
        model_name = self.config.rag.embedding_model
        
        try:
            # Load in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            self.embedding_model = await loop.run_in_executor(
                None, SentenceTransformer, model_name
            )
            logger.info(f"Loaded embedding model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            # Fallback to a smaller model
            self.embedding_model = await loop.run_in_executor(
                None, SentenceTransformer, "all-MiniLM-L6-v2"
            )
            logger.info("Loaded fallback embedding model")
    
    def _initialize_text_splitter(self):
        """Initialize text splitter for document chunking."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.rag.chunk_size,
            chunk_overlap=self.config.rag.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def _initialize_openai(self):
        """Initialize OpenAI client."""
        api_key = self.config.get_api_key("openai")
        if api_key:
            openai.api_key = api_key
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OpenAI API key not found - generation features limited")
    
    async def _load_existing_documents(self):
        """Load existing documents from the index."""
        index_file = Path(self.config.rag.vector_db_path) / "document_index.json"
        
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    self.document_index = json.load(f)
                logger.info(f"Loaded {len(self.document_index)} documents from index")
            except Exception as e:
                logger.error(f"Error loading document index: {e}")
    
    async def add_document(self, file_path: str, document_type: DocumentType = None, metadata: Dict[str, Any] = None) -> str:
        """Add a document to the knowledge base."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Auto-detect document type if not provided
        if document_type is None:
            document_type = self._detect_document_type(file_path)
        
        # Generate document ID
        document_id = self._generate_document_id(file_path)
        
        try:
            # Load document
            documents = await self._load_document(file_path, document_type)
            
            # Split into chunks
            chunks = []
            for doc in documents:
                doc_chunks = self.text_splitter.split_text(doc.page_content)
                for i, chunk in enumerate(doc_chunks):
                    chunk_id = f"{document_id}_chunk_{i}"
                    chunks.append({
                        'id': chunk_id,
                        'content': chunk,
                        'metadata': {
                            'document_id': document_id,
                            'chunk_index': i,
                            'source': str(file_path),
                            'document_type': document_type.value,
                            **(metadata or {}),
                            **doc.metadata
                        }
                    })
            
            # Generate embeddings
            contents = [chunk['content'] for chunk in chunks]
            embeddings = await self._generate_embeddings(contents)
            
            # Add to vector database
            self.collection.add(
                ids=[chunk['id'] for chunk in chunks],
                documents=contents,
                embeddings=embeddings,
                metadatas=[chunk['metadata'] for chunk in chunks]
            )
            
            # Update document index
            self.document_index[document_id] = {
                'file_path': str(file_path),
                'document_type': document_type.value,
                'chunk_count': len(chunks),
                'added_at': time.time(),
                'metadata': metadata or {}
            }
            
            logger.info(f"Added document {document_id} with {len(chunks)} chunks")
            return document_id
            
        except Exception as e:
            logger.error(f"Error adding document {file_path}: {e}")
            raise
    
    async def add_text(self, text: str, source: str = "manual", metadata: Dict[str, Any] = None) -> str:
        """Add raw text to the knowledge base."""
        # Generate document ID
        document_id = hashlib.md5(f"{source}_{text[:100]}".encode()).hexdigest()
        
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            chunk_data = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                chunk_data.append({
                    'id': chunk_id,
                    'content': chunk,
                    'metadata': {
                        'document_id': document_id,
                        'chunk_index': i,
                        'source': source,
                        'document_type': 'text',
                        **(metadata or {})
                    }
                })
            
            # Generate embeddings
            contents = [chunk['content'] for chunk in chunk_data]
            embeddings = await self._generate_embeddings(contents)
            
            # Add to vector database
            self.collection.add(
                ids=[chunk['id'] for chunk in chunk_data],
                documents=contents,
                embeddings=embeddings,
                metadatas=[chunk['metadata'] for chunk in chunk_data]
            )
            
            # Update document index
            self.document_index[document_id] = {
                'source': source,
                'document_type': 'text',
                'chunk_count': len(chunks),
                'added_at': time.time(),
                'metadata': metadata or {}
            }
            
            logger.info(f"Added text document {document_id} with {len(chunks)} chunks")
            return document_id
            
        except Exception as e:
            logger.error(f"Error adding text: {e}")
            raise
    
    async def query(self, query: str, max_results: int = None, min_relevance: float = None) -> QueryResult:
        """Query the knowledge base."""
        start_time = time.time()
        
        # Check cache first
        cache_key = hashlib.md5(query.encode()).hexdigest()
        if cache_key in self.query_cache:
            self.metrics['cache_hits'] += 1
            cached_result = self.query_cache[cache_key]
            cached_result.metadata['cached'] = True
            return cached_result
        
        try:
            max_results = max_results or self.config.rag.max_retrieved_docs
            min_relevance = min_relevance or self.config.rag.similarity_threshold
            
            # Generate query embedding
            query_embedding = await self._generate_embeddings([query])
            
            # Retrieve relevant documents
            retrieval_start = time.time()
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=max_results * 2,  # Get more to filter by relevance
                include=['documents', 'metadatas', 'distances']
            )
            
            retrieval_time = time.time() - retrieval_start
            self.metrics['retrieval_times'].append(retrieval_time)
            
            # Process results
            retrieved_docs = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                # Convert distance to similarity score (ChromaDB uses cosine distance)
                relevance_score = 1.0 - distance
                
                if relevance_score >= min_relevance:
                    retrieved_docs.append(RetrievalResult(
                        content=doc,
                        metadata=metadata,
                        relevance_score=relevance_score,
                        source=metadata.get('source', 'unknown'),
                        document_id=metadata.get('document_id', 'unknown'),
                        chunk_id=results['ids'][0][i]
                    ))
            
            # Limit results
            retrieved_docs = retrieved_docs[:max_results]
            
            # Generate response using retrieved context
            generation_start = time.time()
            generated_response = await self._generate_response(query, retrieved_docs)
            generation_time = time.time() - generation_start
            self.metrics['generation_times'].append(generation_time)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(retrieved_docs, generated_response)
            
            # Create result
            result = QueryResult(
                query=query,
                retrieved_documents=retrieved_docs,
                generated_response=generated_response,
                confidence_score=confidence_score,
                processing_time=time.time() - start_time,
                metadata={
                    'retrieval_time': retrieval_time,
                    'generation_time': generation_time,
                    'total_candidates': len(results['documents'][0]),
                    'filtered_results': len(retrieved_docs)
                }
            )
            
            # Cache result
            self._cache_result(cache_key, result)
            
            self.metrics['total_queries'] += 1
            return result
            
        except Exception as e:
            logger.error(f"Error processing query '{query}': {e}")
            raise
    
    async def _load_document(self, file_path: Path, document_type: DocumentType) -> List[Document]:
        """Load document based on type."""
        if document_type == DocumentType.TEXT:
            loader = TextLoader(str(file_path))
        elif document_type == DocumentType.PDF:
            loader = PDFLoader(str(file_path))
        elif document_type == DocumentType.CSV:
            loader = CSVLoader(str(file_path))
        elif document_type == DocumentType.JSON:
            # Custom JSON loader
            return await self._load_json_document(file_path)
        elif document_type == DocumentType.MARKDOWN:
            loader = TextLoader(str(file_path))
        else:
            raise ValueError(f"Unsupported document type: {document_type}")
        
        return loader.load()
    
    async def _load_json_document(self, file_path: Path) -> List[Document]:
        """Load JSON document."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert JSON to text representation
        if isinstance(data, list):
            documents = []
            for i, item in enumerate(data):
                content = json.dumps(item, indent=2)
                documents.append(Document(
                    page_content=content,
                    metadata={'source': str(file_path), 'item_index': i}
                ))
            return documents
        else:
            content = json.dumps(data, indent=2)
            return [Document(
                page_content=content,
                metadata={'source': str(file_path)}
            )]
    
    def _detect_document_type(self, file_path: Path) -> DocumentType:
        """Auto-detect document type from file extension."""
        suffix = file_path.suffix.lower()
        
        type_mapping = {
            '.txt': DocumentType.TEXT,
            '.pdf': DocumentType.PDF,
            '.csv': DocumentType.CSV,
            '.json': DocumentType.JSON,
            '.md': DocumentType.MARKDOWN,
            '.markdown': DocumentType.MARKDOWN,
            '.html': DocumentType.HTML,
            '.htm': DocumentType.HTML
        }
        
        return type_mapping.get(suffix, DocumentType.TEXT)
    
    def _generate_document_id(self, file_path: Path) -> str:
        """Generate unique document ID."""
        # Use file path and modification time for uniqueness
        stat = file_path.stat()
        content = f"{file_path}_{stat.st_mtime}_{stat.st_size}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, self.embedding_model.encode, texts
        )
        return embeddings.tolist()
    
    async def _generate_response(self, query: str, retrieved_docs: List[RetrievalResult]) -> str:
        """Generate response using retrieved context."""
        if not retrieved_docs:
            return "I don't have enough information to answer that question."
        
        # Prepare context from retrieved documents
        context_parts = []
        for doc in retrieved_docs:
            context_parts.append(f"Source: {doc.source}\nContent: {doc.content}\n")
        
        context = "\n---\n".join(context_parts)
        
        # Create prompt
        prompt = f"""Based on the following context, please answer the question. If the context doesn't contain enough information to answer the question, please say so.

Context:
{context}

Question: {query}

Answer:"""
        
        try:
            # Use OpenAI API if available
            if hasattr(openai, 'api_key') and openai.api_key:
                response = await self._call_openai_api(prompt)
                return response
            else:
                # Fallback to simple context-based response
                return self._generate_simple_response(query, retrieved_docs)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_simple_response(query, retrieved_docs)
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API for response generation."""
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.config.ai_model.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.ai_model.max_tokens,
                temperature=self.config.ai_model.temperature,
                timeout=self.config.ai_model.timeout
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _generate_simple_response(self, query: str, retrieved_docs: List[RetrievalResult]) -> str:
        """Generate simple response without LLM."""
        if not retrieved_docs:
            return "No relevant information found."
        
        # Find the most relevant document
        best_doc = max(retrieved_docs, key=lambda d: d.relevance_score)
        
        # Extract relevant sentences
        sentences = best_doc.content.split('.')
        relevant_sentences = []
        
        query_words = set(query.lower().split())
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            if query_words & sentence_words:  # Intersection
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            response = '. '.join(relevant_sentences[:3])  # Top 3 sentences
            return f"{response}. (Source: {best_doc.source})"
        else:
            return f"Based on the available information: {best_doc.content[:200]}... (Source: {best_doc.source})"
    
    def _calculate_confidence_score(self, retrieved_docs: List[RetrievalResult], response: str) -> float:
        """Calculate confidence score for the response."""
        if not retrieved_docs:
            return 0.0
        
        # Base confidence on relevance scores
        avg_relevance = sum(doc.relevance_score for doc in retrieved_docs) / len(retrieved_docs)
        
        # Adjust based on number of retrieved documents
        doc_count_factor = min(1.0, len(retrieved_docs) / 3.0)
        
        # Adjust based on response length (longer responses might be more comprehensive)
        response_length_factor = min(1.0, len(response) / 100.0)
        
        confidence = avg_relevance * 0.6 + doc_count_factor * 0.2 + response_length_factor * 0.2
        
        return min(1.0, confidence)
    
    def _cache_result(self, cache_key: str, result: QueryResult):
        """Cache query result."""
        if len(self.query_cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.query_cache))
            del self.query_cache[oldest_key]
        
        self.query_cache[cache_key] = result
    
    async def _cache_cleanup_loop(self):
        """Clean up expired cache entries."""
        while self.is_running:
            try:
                # Simple cache cleanup - remove entries older than 1 hour
                current_time = time.time()
                expired_keys = []
                
                for key, result in self.query_cache.items():
                    if current_time - result.processing_time > 3600:  # 1 hour
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.query_cache[key]
                
                if expired_keys:
                    logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
                
                await asyncio.sleep(300)  # Clean every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
                await asyncio.sleep(300)
    
    async def _index_optimization_loop(self):
        """Optimize vector database index periodically."""
        while self.is_running:
            try:
                # Persist the collection to disk
                self.vector_db.persist()
                logger.info("Vector database persisted")
                
                await asyncio.sleep(1800)  # Optimize every 30 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in index optimization: {e}")
                await asyncio.sleep(1800)
    
    async def _metrics_collection_loop(self):
        """Collect and log performance metrics."""
        while self.is_running:
            try:
                if self.metrics['total_queries'] > 0:
                    cache_hit_rate = self.metrics['cache_hits'] / self.metrics['total_queries']
                    avg_retrieval_time = sum(self.metrics['retrieval_times']) / len(self.metrics['retrieval_times']) if self.metrics['retrieval_times'] else 0
                    avg_generation_time = sum(self.metrics['generation_times']) / len(self.metrics['generation_times']) if self.metrics['generation_times'] else 0
                    
                    logger.info(f"RAG Metrics - Queries: {self.metrics['total_queries']}, "
                              f"Cache Hit Rate: {cache_hit_rate:.2%}, "
                              f"Avg Retrieval Time: {avg_retrieval_time:.3f}s, "
                              f"Avg Generation Time: {avg_generation_time:.3f}s")
                
                await asyncio.sleep(600)  # Log every 10 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(600)
    
    async def _save_cache(self):
        """Save query cache to disk."""
        try:
            cache_file = Path(self.config.rag.vector_db_path) / "query_cache.json"
            # Only save cache keys and basic info, not full results
            cache_summary = {
                key: {
                    'query': result.query,
                    'timestamp': result.processing_time,
                    'confidence': result.confidence_score
                }
                for key, result in self.query_cache.items()
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_summary, f, indent=2)
            
            logger.info("Query cache saved")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    async def _save_document_index(self):
        """Save document index to disk."""
        try:
            index_file = Path(self.config.rag.vector_db_path) / "document_index.json"
            with open(index_file, 'w') as f:
                json.dump(self.document_index, f, indent=2)
            
            logger.info("Document index saved")
        except Exception as e:
            logger.error(f"Error saving document index: {e}")
    
    # Public API methods
    
    async def health_check(self) -> str:
        """Perform health check."""
        try:
            # Test vector database connection
            collection_count = self.collection.count()
            
            # Test embedding model
            test_embedding = await self._generate_embeddings(["test"])
            
            if collection_count >= 0 and test_embedding:
                return "healthy"
            else:
                return "unhealthy"
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return "unhealthy"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get RAG engine statistics."""
        return {
            'total_documents': len(self.document_index),
            'total_chunks': self.collection.count() if self.collection else 0,
            'cache_size': len(self.query_cache),
            'metrics': self.metrics.copy()
        }
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the knowledge base."""
        return [
            {
                'document_id': doc_id,
                'source': info.get('file_path', info.get('source', 'unknown')),
                'document_type': info['document_type'],
                'chunk_count': info['chunk_count'],
                'added_at': info['added_at'],
                'metadata': info.get('metadata', {})
            }
            for doc_id, info in self.document_index.items()
        ]
    
    async def remove_document(self, document_id: str) -> bool:
        """Remove a document from the knowledge base."""
        if document_id not in self.document_index:
            return False
        
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"document_id": document_id},
                include=['documents']
            )
            
            if results['ids']:
                # Delete chunks from vector database
                self.collection.delete(ids=results['ids'])
                
                # Remove from document index
                del self.document_index[document_id]
                
                logger.info(f"Removed document {document_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing document {document_id}: {e}")
            return False
    
    async def restart(self):
        """Restart the RAG engine."""
        logger.info("Restarting RAG Engine...")
        await self.shutdown()
        await asyncio.sleep(1)
        await self.initialize()
        await self.start()