import os
import pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document
from app.core.config import PINECONE_API_KEY, OPENAI_API_KEY, INDEX_NAME
from pinecone import Pinecone
import logging
from app.services.agent_index_wrapper import get_restricted_index

# Initialize embeddings
embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(name=INDEX_NAME)

# Create vector store
vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="text")

# Make sure the _index attribute is accessible for our wrapper
# If your implementation is different, you may need to adjust the wrapping approach

def initialize_vector_store():
    """Initialize and configure Pinecone vector store"""
    # Check if index exists, if not create it
    existing_indexes = [index.name for index in pc.list_indexes()]
    if INDEX_NAME not in existing_indexes:
        # Create index with the newer API format
        pc.create_index(
            name=INDEX_NAME,
            dimension=1536,  # OpenAI embeddings dimension
            metric="cosine",
            spec=pinecone.ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

    # Get the index
    index = pc.Index(INDEX_NAME)

    # Initialize embeddings and vector store
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    # Updated to use PineconeVectorStore instead of Pinecone
    vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="text")
    
    return vectorstore

# Initialize the vector store
vectorstore = initialize_vector_store()

logger = logging.getLogger(__name__)

# Global cache to store agent-specific vectorstores
_agent_vectorstore_cache = {}

def get_agent_vectorstore(agent_id):
    """
    Returns a vector store configured for the specified agent.
    Uses a cache to avoid recreating the same vector store multiple times.
    """
    global _agent_vectorstore_cache
    
    # Return cached instance if available
    if agent_id in _agent_vectorstore_cache:
        logger.debug(f"Using cached vector store for agent '{agent_id}'")
        return _agent_vectorstore_cache[agent_id]
    
    # Don't try to deep copy, create a new instance instead
    from app.core.config import OPENAI_API_KEY
    from langchain_openai import OpenAIEmbeddings
    from langchain_pinecone import PineconeVectorStore
    
    # Get the original index from the global vectorstore
    original_index = vectorstore._index  # Use the existing vectorstore's index
    
    # Create a restricted index for this agent
    restricted_index = get_restricted_index(original_index, agent_id)
    
    # Create a new embeddings object
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    
    # Create a new vector store with the restricted index
    namespace = f"{agent_id}_namespace"
    agent_vectorstore = PineconeVectorStore(
        index=restricted_index,
        embedding=embeddings,
        text_key="text",
        namespace=namespace
    )
    
    logger.info(f"Created vector store for agent '{agent_id}' with namespace '{namespace}'")
    
    # Cache the vector store
    _agent_vectorstore_cache[agent_id] = agent_vectorstore
    
    return agent_vectorstore

def verify_namespace_contents(agent_id):
    """Verify contents of a namespace for debugging"""
    try:
        vs = get_agent_vectorstore(agent_id)
        # Get a sample of documents from the namespace
        docs = vs.similarity_search("mechanical engineering", k=5, namespace=f"{agent_id}_namespace")
        logger.info(f"Found {len(docs)} documents in {agent_id}_namespace")
        for i, doc in enumerate(docs):
            logger.info(f"Doc {i+1}: {doc.page_content[:100]}... | Metadata: {doc.metadata}")
        return len(docs)
    except Exception as e:
        logger.error(f"Error verifying {agent_id}_namespace: {str(e)}")
        return 0
