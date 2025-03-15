import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

# Load environment variables - simple version without encoding handling
load_dotenv()

# Initialize Pinecone with the new API
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Define the index name
index_name = "academic-advisor-knowledge"

def main():
    # Check if the index exists, if not create it
    if index_name not in pc.list_indexes().names():
        print(f"Creating new Pinecone index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=1536,  # OpenAI embeddings dimension
            metric="cosine"
        )
    
    # Load the PDF
    print("Loading PDF file...")
    loader = PyPDFLoader("2024-catalog.pdf")
    documents = loader.load()
    
    # Split text into chunks
    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
    
    print(f"Split into {len(chunks)} chunks")
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings()
    
    # Upload to Pinecone
    print("Uploading to Pinecone...")
    vectorstore = PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        index_name=index_name
    )
    
    print(f"Successfully uploaded {len(chunks)} chunks to Pinecone index '{index_name}'")
    return vectorstore

if __name__ == "__main__":
    main()