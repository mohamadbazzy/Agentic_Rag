import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables
load_dotenv()

# Get API key and index name from environment
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "academic-advisor-knowledge")

def delete_all_vectors_in_namespaces():
    """Delete all vectors in all namespaces of the Pinecone index"""
    print(f"Connecting to Pinecone index: {INDEX_NAME}")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(name=INDEX_NAME)
    
    # Get all namespaces
    stats = index.describe_index_stats()
    namespaces = stats.get('namespaces', {}).keys()
    
    if not namespaces:
        print("No namespaces found in the index.")
        return
    
    print(f"Found {len(namespaces)} namespaces:")
    for namespace in namespaces:
        print(f"  - {namespace}")
        
    confirm = input("\nAre you sure you want to delete ALL vectors in ALL namespaces? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    # Delete vectors from each namespace
    for namespace in namespaces:
        try:
            # In new Pinecone API, we can delete all vectors in a namespace with delete_all()
            index.delete(namespace=namespace, delete_all=True)
            print(f"Successfully deleted all vectors in namespace: {namespace}")
        except Exception as e:
            print(f"Error deleting vectors in namespace {namespace}: {str(e)}")
    
    print("\nDeletion complete. Verifying namespaces are empty...")
    
    # Verify namespaces are empty
    stats_after = index.describe_index_stats()
    for namespace, ns_stats in stats_after.get('namespaces', {}).items():
        vector_count = ns_stats.get('vector_count', 0)
        print(f"  - {namespace}: {vector_count} vectors remaining")

if __name__ == "__main__":
    delete_all_vectors_in_namespaces()
