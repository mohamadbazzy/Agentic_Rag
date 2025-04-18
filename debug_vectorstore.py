# debug_vectorstore.py

import os
import logging
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API keys and settings from environment
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "academic-advisor-knowledge")

def debug_documents():
    """Debug function to retrieve and inspect documents from vectorstore"""
    logger.info(f"Connecting to Pinecone index: {INDEX_NAME}")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(name=INDEX_NAME)
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    
    # Create vector store
    vectorstore = PineconeVectorStore(
        index=index, 
        embedding=embeddings, 
        text_key="text"
    )
    
    # Test query to search for ECE documents
    test_query = "Electrical and Computer Engineering: General information"
    
    # Try different searches to debug
    logger.info("SEARCH TEST 1: With ece_namespace and department filter")
    try:
        docs_with_filter = vectorstore.similarity_search(
            test_query, 
            k=3,
            namespace="ece_namespace",
            filter={"department": "ece"}
        )
        logger.info(f"Found {len(docs_with_filter)} documents with filter")
        if docs_with_filter:
            for i, doc in enumerate(docs_with_filter):
                logger.info(f"Doc {i+1} content sample: {doc.page_content[:200]}...")
                logger.info(f"Doc {i+1} metadata: {doc.metadata}")
        else:
            logger.warning("No documents found with filter")
    except Exception as e:
        logger.error(f"Error in search with filter: {str(e)}")
    
    logger.info("\nSEARCH TEST 2: With ece_namespace but no filter")
    try:
        docs_no_filter = vectorstore.similarity_search(
            test_query, 
            k=3,
            namespace="ece_namespace"
        )
        logger.info(f"Found {len(docs_no_filter)} documents without filter")
        if docs_no_filter:
            for i, doc in enumerate(docs_no_filter):
                logger.info(f"Doc {i+1} content sample: {doc.page_content[:200]}...")
                logger.info(f"Doc {i+1} metadata: {doc.metadata}")
        else:
            logger.warning("No documents found without filter")
    except Exception as e:
        logger.error(f"Error in search without filter: {str(e)}")
    
    logger.info("\nSEARCH TEST 3: With ece_namespace and track filter")
    try:
        docs_track_filter = vectorstore.similarity_search(
            test_query, 
            k=3,
            namespace="ece_namespace",
            filter={"track": "general_ece"}
        )
        logger.info(f"Found {len(docs_track_filter)} documents with track filter")
        if docs_track_filter:
            for i, doc in enumerate(docs_track_filter):
                logger.info(f"Doc {i+1} content sample: {doc.page_content[:200]}...")
                logger.info(f"Doc {i+1} metadata: {doc.metadata}")
        else:
            logger.warning("No documents found with track filter")
    except Exception as e:
        logger.error(f"Error in search with track filter: {str(e)}")
    
    # Test context creation
    logger.info("\nTesting context creation")
    if docs_no_filter:
        try:
            context = [{"content": doc.page_content, "source": doc.metadata.get("source", "unknown")} 
                     for doc in docs_no_filter]
            context_str = "\n".join([item["content"] for item in context])
            logger.info(f"Context length: {len(context_str)} characters")
            logger.info(f"Context sample: {context_str[:300]}...")
        except Exception as e:
            logger.error(f"Error creating context: {str(e)}")

if __name__ == "__main__":
    debug_documents()