import os
import json
import logging
import argparse
from typing import Dict, List, Optional
from pinecone import Pinecone, ServerlessSpec

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default namespace configuration - updated with additional namespaces
DEFAULT_NAMESPACE_CONFIG = {
    "advisor": ["advisor_namespace"],
    "supervisor": ["supervisor_namespace"],
    "mechanical": ["mechanical_namespace"],
    "chemical": ["chemical_namespace"],
    "civil": ["civil_namespace"],
    "ece": ["ece_namespace"],
    "cse": ["cse_namespace"],
    "cce": ["cce_namespace"],
    "msfea_advisor": ["msfea_advisor_namespace"],
    # Added new namespaces for future agents
    "industrial": ["industrial_namespace"],
    "gpa": ["gpa_namespace"],
    "schedule_maker": ["schedule_maker_namespace"],
    # Add any other departments or agents as needed
}

def load_namespace_config() -> List[str]:
    """
    Load the namespace configuration and return a flat list of all namespaces.
    
    Returns:
        A list of all namespaces to create
    """
    # Try loading from environment variable
    config_json = os.environ.get("AGENT_NAMESPACE_CONFIG")
    config = None
    
    if config_json:
        try:
            config = json.loads(config_json)
            logger.info("Loaded namespace configuration from environment variable")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in AGENT_NAMESPACE_CONFIG environment variable")
    
    # Try loading from config file if environment variable wasn't set or was invalid
    if not config:
        config_path = os.environ.get("AGENT_NAMESPACE_CONFIG_PATH", "agent_namespaces.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Loaded namespace configuration from file: {config_path}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load namespace config file: {e}")
    
    # Fall back to default configuration if needed
    if not config:
        logger.info("Using default namespace configuration")
        config = DEFAULT_NAMESPACE_CONFIG
    
    # Extract all namespaces from configuration and flatten the list
    all_namespaces = []
    for agent_id, namespaces in config.items():
        all_namespaces.extend(namespaces)
    
    # Remove duplicates
    unique_namespaces = list(set(all_namespaces))
    logger.info(f"Found {len(unique_namespaces)} unique namespaces to create")
    
    return unique_namespaces

def create_pinecone_namespaces(api_key: str, index_name: str, dimension: int, namespaces: List[str]):
    """
    Create all required namespaces in Pinecone by upserting a dummy vector into each.
    
    Args:
        api_key: Pinecone API key
        index_name: Name of the Pinecone index to use
        dimension: Vector dimension for the index
        namespaces: List of namespaces to create
    """
    logger.info(f"Connecting to Pinecone index '{index_name}'")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=api_key)
    
    # Check if index exists, create it if it doesn't
    try:
        # Try to describe the index to check if it exists
        index_info = pc.describe_index(index_name)
        logger.info(f"Using existing index '{index_name}'")
        
        # Check if dimension matches
        if hasattr(index_info, 'dimension') and index_info.dimension != dimension:
            logger.warning(f"Index dimension ({index_info.dimension}) doesn't match specified dimension ({dimension})")
    except Exception as e:
        logger.info(f"Index '{index_name}' doesn't exist. Creating it...")
        try:
            # Create the index with serverless configuration
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",  # You can change this to euclidean or dotproduct if needed
                spec=ServerlessSpec(cloud="aws", region="us-west-2")  # Change the region as needed
            )
            logger.info(f"Created index '{index_name}' with dimension {dimension}")
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return
    
    # Get the index
    index = pc.Index(name=index_name)
    
    # Create a dummy vector (all zeros) with the correct dimension
    dummy_vector = [0.0] * dimension
    dummy_vector[0] = 1.0
    
    # For each namespace, upsert a dummy vector
    for namespace in namespaces:
        try:
            # Create a unique ID for the dummy vector
            dummy_id = f"dummy_vector_{namespace}"
            
            # Upsert the dummy vector
            index.upsert(
                vectors=[
                    {
                        "id": dummy_id,
                        "values": dummy_vector,
                        "metadata": {"type": "namespace_initialization"}
                    }
                ],
                namespace=namespace
            )
            logger.info(f"Successfully created namespace '{namespace}'")
            
            # Optionally, delete the dummy vector to keep the index clean
            # Uncomment the next line if you want to delete the dummy vectors after creating namespaces
            # index.delete(ids=[dummy_id], namespace=namespace)
            
        except Exception as e:
            logger.error(f"Failed to create namespace '{namespace}': {e}")
    
    # Verify namespaces were created
    try:
        stats = index.describe_index_stats()
        if hasattr(stats, 'namespaces'):
            created_namespaces = list(stats.namespaces.keys())
            logger.info(f"Verified namespaces in index: {created_namespaces}")
            
            # Check if all requested namespaces were created
            missing_namespaces = [ns for ns in namespaces if ns not in created_namespaces]
            if missing_namespaces:
                logger.warning(f"Some namespaces could not be verified: {missing_namespaces}")
            else:
                logger.info("All namespaces successfully created and verified!")
        else:
            logger.warning("Could not verify namespaces - index stats format unexpected")
    except Exception as e:
        logger.error(f"Failed to verify namespaces: {e}")

def main():
    """Main function to parse arguments and create namespaces"""
    parser = argparse.ArgumentParser(description='Initialize Pinecone namespaces for agent isolation')
    
    parser.add_argument('--api-key', type=str, 
                        default=os.environ.get('PINECONE_API_KEY'),
                        help='Pinecone API key (defaults to PINECONE_API_KEY environment variable)')
    
    parser.add_argument('--index-name', type=str, 
                        default=os.environ.get('PINECONE_INDEX_NAME', 'academic-advisor-knowledge'),
                        help='Pinecone index name (defaults to PINECONE_INDEX_NAME environment variable or "agent-isolation-index")')
    
    parser.add_argument('--dimension', type=int, 
                        default=int(os.environ.get('PINECONE_DIMENSION', '1536')),
                        help='Vector dimension (defaults to PINECONE_DIMENSION environment variable or 1536)')
    
    parser.add_argument('--config-file', type=str,
                        default=os.environ.get('AGENT_NAMESPACE_CONFIG_PATH', 'agent_namespaces.json'),
                        help='Path to namespace configuration file')
    
    args = parser.parse_args()
    
    # Validate API key
    if not args.api_key:
        logger.error("No Pinecone API key provided. Set the PINECONE_API_KEY environment variable or pass --api-key")
        return
    
    # Load namespaces from configuration
    namespaces = load_namespace_config()
    
    # Create the namespaces
    create_pinecone_namespaces(
        api_key=args.api_key,
        index_name=args.index_name,
        dimension=args.dimension,
        namespaces=namespaces
    )
    
    logger.info("Namespace initialization process completed")

if __name__ == "__main__":
    main()