import os
import pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document
from app.core.config import PINECONE_API_KEY, OPENAI_API_KEY, INDEX_NAME

# Initialize Pinecone
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

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
