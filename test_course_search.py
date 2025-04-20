import os
import logging
from dotenv import load_dotenv
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add app directory to path for imports
sys.path.append(".")

# Load environment variables
load_dotenv()

from app.db.vector_store import get_agent_vectorstore

def test_course_search():
    """Test function to directly search for ECE courses using different methods"""
    logger.info("Starting direct course search test")
    
    # Initialize vector store with ECE agent permissions
    ece_vectorstore = get_agent_vectorstore("ece")
    
    # Test courses to search for
    test_courses = ["EECE 230", "EECE 338", "EECE 210"]
    
    for course in test_courses:
        logger.info(f"\n--- Testing search for {course} ---")
        
        # Test 1: Direct similarity search with course code
        logger.info(f"TEST 1: Direct similarity search for '{course}'")
        try:
            docs = ece_vectorstore.similarity_search(
                course,
                k=5,
                namespace="ece_namespace"
            )
            logger.info(f"Found {len(docs)} documents")
            if docs:
                for i, doc in enumerate(docs[:2]):  # Log first 2 docs
                    logger.info(f"Doc {i+1} content: {doc.page_content[:100]}...")
                    logger.info(f"Doc {i+1} metadata: {doc.metadata}")
        except Exception as e:
            logger.error(f"Error in direct search: {str(e)}")
        
        # Test 2: Search with metadata filter
        logger.info(f"\nTEST 2: Search with exact metadata filter for '{course}'")
        try:
            docs = ece_vectorstore.similarity_search(
                "course information",
                k=5,
                namespace="ece_namespace",
                filter={"course_code": {"$eq": course}}
            )
            logger.info(f"Found {len(docs)} documents with exact filter")
            if docs:
                for i, doc in enumerate(docs[:2]):  # Log first 2 docs
                    logger.info(f"Doc {i+1} metadata: {doc.metadata}")
        except Exception as e:
            logger.error(f"Error in filter search: {str(e)}")
        
        # Test 3: Search with looser metadata filter
        logger.info(f"\nTEST 3: Search with partial metadata filter for '{course.split()[1]}'")
        course_number = course.split()[1]
        try:
            docs = ece_vectorstore.similarity_search(
                "course information",
                k=5,
                namespace="ece_namespace",
                filter={"course_code": {"$contains": course_number}}
            )
            logger.info(f"Found {len(docs)} documents with partial number filter")
            if docs:
                for i, doc in enumerate(docs[:2]):  # Log first 2 docs
                    logger.info(f"Doc {i+1} metadata: {doc.metadata}")
        except Exception as e:
            logger.error(f"Error in partial filter search: {str(e)}")

if __name__ == "__main__":
    test_course_search() 