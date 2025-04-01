#!/usr/bin/env python
import os
import logging
import sys
import argparse
from pinecone import Pinecone
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import environment variables
load_dotenv()

# Get API keys and settings from environment
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Validate environment variables
if not PINECONE_API_KEY:
    logger.error("PINECONE_API_KEY environment variable is not set")
    sys.exit(1)
    
if not PINECONE_INDEX_NAME:
    logger.error("PINECONE_INDEX_NAME environment variable is not set")
    sys.exit(1)

def delete_namespace_contents():
    """
    Delete all vectors in the schedule_maker_namespace
    """
    logger.info(f"Connecting to Pinecone index: {PINECONE_INDEX_NAME}")
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
        
        # Check if namespace exists
        namespace = "schedule_maker_namespace"
        stats = index.describe_index_stats()
        
        if namespace in stats.namespaces:
            namespace_size = stats.namespaces[namespace].vector_count
            logger.info(f"Found namespace '{namespace}' containing {namespace_size} vectors")
            
            # Delete all vectors in the namespace
            logger.info(f"Deleting all vectors in namespace '{namespace}'...")
            index.delete(delete_all=True, namespace=namespace)
            
            # Verify deletion
            updated_stats = index.describe_index_stats()
            if namespace in updated_stats.namespaces:
                remaining = updated_stats.namespaces[namespace].vector_count
                logger.info(f"Deletion complete. {remaining} vectors remaining in namespace.")
            else:
                logger.info(f"Deletion complete. Namespace '{namespace}' is now empty.")
                
            return True
        else:
            logger.info(f"Namespace '{namespace}' not found or is already empty.")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting namespace contents: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete all contents from schedule_maker_namespace")
    parser.add_argument("--confirm", action="store_true", 
                        help="Confirm deletion without prompting")
    
    args = parser.parse_args()
    
    if not args.confirm:
        confirmation = input("WARNING: This will delete ALL vectors in schedule_maker_namespace. Type 'DELETE' to confirm: ")
        if confirmation != "DELETE":
            logger.info("Deletion cancelled.")
            sys.exit(0)
    
    success = delete_namespace_contents()
    
    if success:
        logger.info("Successfully deleted all vectors from schedule_maker_namespace")
    else:
        logger.error("Failed to delete vectors from schedule_maker_namespace")
        sys.exit(1)