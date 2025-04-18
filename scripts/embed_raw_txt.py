import os
import argparse
import json
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document
from pinecone import Pinecone
from langchain_community.document_loaders import TextLoader

# Load environment variables
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "academic-advisor-knowledge")
NAMESPACE = "msfea_advisor_namespace"

def embed_raw_txt(document_path, metadata=None):
    print(f"Embedding raw document: {document_path}")

    # Load the raw text
    loader = TextLoader(document_path, encoding='utf-8')
    docs = loader.load()

    if not docs:
        print("No content found in the file.")
        return

    # Treat the entire file as a single document
    full_text = "\n".join([doc.page_content for doc in docs])
    doc = Document(page_content=full_text, metadata={
        "source": os.path.basename(document_path),
        **(metadata or {})
    })

    # Set up Pinecone and embeddings
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(name=INDEX_NAME)
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="text")

    print("Uploading 1 raw document chunk to Pinecone...")
    vectorstore.add_documents(documents=[doc], namespace=NAMESPACE)
    print(f"Successfully embedded document to namespace '{NAMESPACE}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed raw .txt file into Pinecone without chunking")
    parser.add_argument("document_path", help="Path to the .txt file")
    parser.add_argument("--metadata", type=str, help="JSON string of metadata")

    args = parser.parse_args()

    metadata_dict = None
    if args.metadata:
        try:
            metadata_dict = json.loads(args.metadata)
        except json.JSONDecodeError:
            print("Error: Invalid JSON metadata format.")
            exit(1)

    embed_raw_txt(args.document_path, metadata_dict)
