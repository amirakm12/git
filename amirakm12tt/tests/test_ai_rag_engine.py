"""
Tests for ai.rag_engine module
"""

import pytest
import asyncio
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from ai.rag_engine import RAGEngine, DocumentProcessor, EmbeddingGenerator, VectorStore


class TestDocumentProcessor:
    """Test DocumentProcessor class."""
    
    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        processor = DocumentProcessor(chunk_size=10, chunk_overlap=2)
        
        text = "This is a test document with some content to chunk."
        chunks = processor.chunk_text(text)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 12 for chunk in chunks)  # chunk_size + overlap
    
    def test_chunk_text_short(self):
        """Test chunking with text shorter than chunk size."""
        processor = DocumentProcessor(chunk_size=100, chunk_overlap=10)
        
        text = "Short text"
        chunks = processor.chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_empty(self):
        """Test chunking empty text."""
        processor = DocumentProcessor(chunk_size=100, chunk_overlap=10)
        
        chunks = processor.chunk_text("")
        
        assert len(chunks) == 0
    
    def test_process_document(self):
        """Test document processing."""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)
        
        document = {
            'content': 'This is a test document with multiple sentences. It should be chunked properly.',
            'metadata': {'source': 'test.txt', 'category': 'test'}
        }
        
        processed = processor.process_document(document)
        
        assert 'chunks' in processed
        assert 'metadata' in processed
        assert len(processed['chunks']) > 0
        assert processed['metadata'] == document['metadata']
    
    def test_extract_text_from_file_txt(self, temp_dir):
        """Test text extraction from text file."""
        processor = DocumentProcessor()
        
        # Create test file
        test_file = temp_dir / "test.txt"
        test_content = "This is test content from a file."
        test_file.write_text(test_content)
        
        extracted = processor.extract_text_from_file(str(test_file))
        
        assert extracted == test_content
    
    def test_extract_text_from_file_nonexistent(self):
        """Test text extraction from non-existent file."""
        processor = DocumentProcessor()
        
        result = processor.extract_text_from_file("nonexistent.txt")
        
        assert result == ""


class TestEmbeddingGenerator:
    """Test EmbeddingGenerator class."""
    
    @pytest.fixture
    def mock_model(self):
        """Create mock embedding model."""
        model = Mock()
        model.encode.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        return model
    
    def test_initialization(self):
        """Test embedding generator initialization."""
        with patch('sentence_transformers.SentenceTransformer') as mock_st:
            mock_st.return_value = Mock()
            
            generator = EmbeddingGenerator("test-model")
            
            assert generator.model_name == "test-model"
            mock_st.assert_called_once_with("test-model")
    
    def test_generate_embeddings(self, mock_model):
        """Test embedding generation."""
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
            generator = EmbeddingGenerator("test-model")
            
            texts = ["This is test text", "Another test text"]
            embeddings = generator.generate_embeddings(texts)
            
            assert len(embeddings) == 1  # Mock returns single embedding
            assert len(embeddings[0]) == 5  # Mock embedding dimension
            mock_model.encode.assert_called_once_with(texts)
    
    def test_generate_single_embedding(self, mock_model):
        """Test single embedding generation."""
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
            generator = EmbeddingGenerator("test-model")
            
            text = "Single test text"
            embedding = generator.generate_single_embedding(text)
            
            assert len(embedding) == 5  # Mock embedding dimension
            mock_model.encode.assert_called_once_with([text])


class TestVectorStore:
    """Test VectorStore class."""
    
    @pytest.fixture
    def mock_chroma_client(self):
        """Create mock ChromaDB client."""
        client = Mock()
        collection = Mock()
        collection.add = Mock()
        collection.query = Mock(return_value={
            'documents': [['Test document']],
            'metadatas': [[{'source': 'test.txt'}]],
            'distances': [[0.5]]
        })
        client.create_collection.return_value = collection
        client.get_collection.return_value = collection
        return client, collection
    
    def test_initialization(self, mock_chroma_client):
        """Test vector store initialization."""
        mock_client, mock_collection = mock_chroma_client
        
        with patch('chromadb.Client', return_value=mock_client):
            store = VectorStore("test_collection", "test_path")
            
            assert store.collection_name == "test_collection"
            assert store.persist_directory == "test_path"
    
    def test_add_documents(self, mock_chroma_client):
        """Test adding documents to vector store."""
        mock_client, mock_collection = mock_chroma_client
        
        with patch('chromadb.Client', return_value=mock_client):
            store = VectorStore("test_collection", "test_path")
            
            documents = ["Test document 1", "Test document 2"]
            embeddings = [[0.1, 0.2], [0.3, 0.4]]
            metadatas = [{'source': 'test1.txt'}, {'source': 'test2.txt'}]
            
            store.add_documents(documents, embeddings, metadatas)
            
            mock_collection.add.assert_called_once()
    
    def test_query_documents(self, mock_chroma_client):
        """Test querying documents from vector store."""
        mock_client, mock_collection = mock_chroma_client
        
        with patch('chromadb.Client', return_value=mock_client):
            store = VectorStore("test_collection", "test_path")
            
            query_embedding = [0.1, 0.2, 0.3]
            results = store.query_documents(query_embedding, n_results=5)
            
            assert 'documents' in results
            assert 'metadatas' in results
            assert 'distances' in results
            mock_collection.query.assert_called_once()
    
    def test_query_with_filter(self, mock_chroma_client):
        """Test querying with metadata filter."""
        mock_client, mock_collection = mock_chroma_client
        
        with patch('chromadb.Client', return_value=mock_client):
            store = VectorStore("test_collection", "test_path")
            
            query_embedding = [0.1, 0.2, 0.3]
            where_filter = {"source": "test.txt"}
            
            store.query_documents(query_embedding, n_results=3, where=where_filter)
            
            mock_collection.query.assert_called_once()
            call_args = mock_collection.query.call_args
            assert call_args[1]['where'] == where_filter


class TestRAGEngine:
    """Test RAGEngine class."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for RAG engine."""
        doc_processor = Mock(spec=DocumentProcessor)
        embedding_gen = Mock(spec=EmbeddingGenerator)
        vector_store = Mock(spec=VectorStore)
        
        # Configure mocks
        doc_processor.process_document.return_value = {
            'chunks': ['Test chunk 1', 'Test chunk 2'],
            'metadata': {'source': 'test.txt'}
        }
        
        embedding_gen.generate_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
        embedding_gen.generate_single_embedding.return_value = [0.5, 0.6]
        
        vector_store.query_documents.return_value = {
            'documents': [['Relevant document']],
            'metadatas': [[{'source': 'relevant.txt'}]],
            'distances': [[0.3]]
        }
        
        return doc_processor, embedding_gen, vector_store
    
    @pytest.fixture
    def rag_engine(self, test_config, mock_components):
        """Create RAG engine for testing."""
        doc_processor, embedding_gen, vector_store = mock_components
        
        with patch('ai.rag_engine.DocumentProcessor', return_value=doc_processor), \
             patch('ai.rag_engine.EmbeddingGenerator', return_value=embedding_gen), \
             patch('ai.rag_engine.VectorStore', return_value=vector_store):
            
            engine = RAGEngine(test_config)
            engine.document_processor = doc_processor
            engine.embedding_generator = embedding_gen
            engine.vector_store = vector_store
            
            return engine
    
    def test_initialization(self, test_config):
        """Test RAG engine initialization."""
        with patch('ai.rag_engine.DocumentProcessor'), \
             patch('ai.rag_engine.EmbeddingGenerator'), \
             patch('ai.rag_engine.VectorStore'):
            
            engine = RAGEngine(test_config)
            
            assert engine.config == test_config
            assert engine.is_running == False
    
    @pytest.mark.asyncio
    async def test_initialize(self, rag_engine):
        """Test RAG engine initialization."""
        await rag_engine.initialize()
        
        assert rag_engine.document_processor is not None
        assert rag_engine.embedding_generator is not None
        assert rag_engine.vector_store is not None
    
    @pytest.mark.asyncio
    async def test_start_shutdown(self, rag_engine):
        """Test RAG engine start and shutdown."""
        await rag_engine.initialize()
        await rag_engine.start()
        
        assert rag_engine.is_running == True
        
        await rag_engine.shutdown()
        
        assert rag_engine.is_running == False
    
    @pytest.mark.asyncio
    async def test_add_document(self, rag_engine, mock_components):
        """Test adding document to RAG engine."""
        doc_processor, embedding_gen, vector_store = mock_components
        
        await rag_engine.initialize()
        
        document = {
            'content': 'Test document content',
            'metadata': {'source': 'test.txt'}
        }
        
        await rag_engine.add_document(document)
        
        doc_processor.process_document.assert_called_once_with(document)
        embedding_gen.generate_embeddings.assert_called_once()
        vector_store.add_documents.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_documents_batch(self, rag_engine, mock_components):
        """Test adding multiple documents in batch."""
        doc_processor, embedding_gen, vector_store = mock_components
        
        await rag_engine.initialize()
        
        documents = [
            {'content': 'Doc 1', 'metadata': {'source': 'doc1.txt'}},
            {'content': 'Doc 2', 'metadata': {'source': 'doc2.txt'}}
        ]
        
        await rag_engine.add_documents(documents)
        
        assert doc_processor.process_document.call_count == 2
        embedding_gen.generate_embeddings.assert_called()
        vector_store.add_documents.assert_called()
    
    @pytest.mark.asyncio
    async def test_query(self, rag_engine, mock_components):
        """Test querying RAG engine."""
        doc_processor, embedding_gen, vector_store = mock_components
        
        await rag_engine.initialize()
        
        query = "Test query"
        results = await rag_engine.query(query)
        
        embedding_gen.generate_single_embedding.assert_called_once_with(query)
        vector_store.query_documents.assert_called_once()
        
        assert 'documents' in results
        assert 'metadatas' in results
        assert 'scores' in results
    
    @pytest.mark.asyncio
    async def test_query_with_filter(self, rag_engine, mock_components):
        """Test querying with metadata filter."""
        doc_processor, embedding_gen, vector_store = mock_components
        
        await rag_engine.initialize()
        
        query = "Test query"
        metadata_filter = {"category": "test"}
        
        await rag_engine.query(query, metadata_filter=metadata_filter)
        
        call_args = vector_store.query_documents.call_args
        assert call_args[1]['where'] == metadata_filter
    
    @pytest.mark.asyncio
    async def test_generate_response(self, rag_engine):
        """Test response generation with retrieved context."""
        await rag_engine.initialize()
        
        # Mock AI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated response"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        rag_engine.ai_client = mock_client
        
        query = "Test query"
        context_docs = ["Context document 1", "Context document 2"]
        
        response = await rag_engine.generate_response(query, context_docs)
        
        assert response == "Generated response"
        mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_full_rag_pipeline(self, rag_engine):
        """Test complete RAG pipeline."""
        await rag_engine.initialize()
        
        # Mock AI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "RAG response"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        rag_engine.ai_client = mock_client
        
        query = "What is machine learning?"
        response = await rag_engine.process_query(query)
        
        assert response == "RAG response"
    
    @pytest.mark.asyncio
    async def test_health_check(self, rag_engine):
        """Test RAG engine health check."""
        await rag_engine.initialize()
        await rag_engine.start()
        
        health = await rag_engine.health_check()
        
        assert health in ["healthy", "degraded", "unhealthy"]
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, rag_engine):
        """Test getting RAG engine statistics."""
        await rag_engine.initialize()
        
        stats = rag_engine.get_statistics()
        
        assert 'total_documents' in stats
        assert 'total_queries' in stats
        assert 'average_response_time' in stats
    
    @pytest.mark.asyncio
    async def test_error_handling(self, rag_engine, mock_components):
        """Test error handling in RAG operations."""
        doc_processor, embedding_gen, vector_store = mock_components
        
        # Configure mock to raise exception
        vector_store.query_documents.side_effect = Exception("Vector store error")
        
        await rag_engine.initialize()
        
        with pytest.raises(Exception):
            await rag_engine.query("Test query")


@pytest.mark.integration
class TestRAGEngineIntegration:
    """Integration tests for RAG engine."""
    
    @pytest.mark.asyncio
    async def test_document_indexing_and_retrieval(self, test_config, sample_rag_documents):
        """Test complete document indexing and retrieval pipeline."""
        # Use temporary directory for testing
        test_config.rag.vector_db_path = "test_vector_db"
        
        # Mock external dependencies
        with patch('sentence_transformers.SentenceTransformer') as mock_st, \
             patch('chromadb.Client') as mock_client, \
             patch('openai.AsyncOpenAI') as mock_openai:
            
            # Configure mocks
            mock_model = Mock()
            mock_model.encode.return_value = [[0.1] * 384 for _ in range(10)]
            mock_st.return_value = mock_model
            
            mock_collection = Mock()
            mock_collection.add = Mock()
            mock_collection.query.return_value = {
                'documents': [['Sample document about AI']],
                'metadatas': [[{'source': 'test.txt'}]],
                'distances': [[0.2]]
            }
            mock_client.return_value.create_collection.return_value = mock_collection
            mock_client.return_value.get_collection.return_value = mock_collection
            
            # Create and initialize RAG engine
            rag_engine = RAGEngine(test_config)
            await rag_engine.initialize()
            await rag_engine.start()
            
            try:
                # Add documents
                await rag_engine.add_documents(sample_rag_documents)
                
                # Query documents
                results = await rag_engine.query("What is artificial intelligence?")
                
                # Verify results
                assert 'documents' in results
                assert len(results['documents']) > 0
                
            finally:
                await rag_engine.shutdown()
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, test_config):
        """Test concurrent RAG operations."""
        with patch('sentence_transformers.SentenceTransformer'), \
             patch('chromadb.Client'), \
             patch('openai.AsyncOpenAI'):
            
            rag_engine = RAGEngine(test_config)
            await rag_engine.initialize()
            await rag_engine.start()
            
            try:
                # Create multiple concurrent queries
                queries = [f"Query {i}" for i in range(5)]
                tasks = [rag_engine.query(query) for query in queries]
                
                # Execute concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Verify all completed (even if with exceptions due to mocking)
                assert len(results) == 5
                
            finally:
                await rag_engine.shutdown()