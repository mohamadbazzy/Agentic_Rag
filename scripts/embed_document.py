import os
import argparse
import re
import json
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredMarkdownLoader
from pinecone import Pinecone

# Load environment variables
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "academic-advisor-knowledge")

def split_by_term_structure(text, source):
    pattern = re.compile(r"(Term\s+[IVX]+\s*\((Fall|Spring|Summer)\))", re.IGNORECASE)
    sections = pattern.split(text)
    result = []
    i = 0
    while i < len(sections):
        if pattern.match(sections[i]):
            term = sections[i].strip()
            if i + 1 < len(sections):
                content = sections[i + 1].strip()
                metadata = {"term": term, "source": source}
                result.append(Document(page_content=f"{term}\n{content}", metadata=metadata))
                i += 2
            else:
                break
        else:
            i += 1
    return result

def split_by_course_descriptions(text, source):
    pattern = re.compile(r"(EECE\s\d{3}\s[^\n]+?)\n(.*?)(?=\nEECE\s\d{3}\s|\Z)", re.DOTALL)
    matches = pattern.findall(text)
    result = []
    for title, body in matches:
        title_line = title.strip()
        body = body.strip()
        code_match = re.match(r"(EECE\s\d{3})\s(.*)", title_line)
        if code_match:
            course_code = code_match.group(1)
            course_title = code_match.group(2)
            metadata = {
                "course_code": course_code,
                "course_title": course_title,
                "source": source
            }
            result.append(Document(page_content=f"{title_line}\n{body}", metadata=metadata))
    return result

def embed_document(document_path, namespace, chunk_size=1000, chunk_overlap=200, metadata=None):
    print(f"Processing document: {document_path}")
    print(f"Target namespace: {namespace}")

    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(name=INDEX_NAME)
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="text")

    file_extension = os.path.splitext(document_path)[1].lower()
    if file_extension == '.pdf':
        loader = PyPDFLoader(document_path)
    elif file_extension == '.md':
        loader = UnstructuredMarkdownLoader(document_path)
    else:
        loader = TextLoader(document_path, encoding='utf-8')

    documents = loader.load()
    print(f"Loaded {len(documents)} document parts")

    full_text = "\n".join([doc.page_content for doc in documents])

    term_chunks = split_by_term_structure(full_text, source=os.path.basename(document_path))
    print(f"Identified {len(term_chunks)} term-based curriculum chunks")

    course_chunks = split_by_course_descriptions(full_text, source=os.path.basename(document_path))
    print(f"Identified {len(course_chunks)} course description chunks")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    general_chunks = splitter.split_documents(documents)
    print(f"Created {len(general_chunks)} general text chunks")

    all_chunks = general_chunks + term_chunks + course_chunks

    for chunk in all_chunks:
        if 'source' not in chunk.metadata:
            chunk.metadata['source'] = os.path.basename(document_path)
        if metadata:
            chunk.metadata.update(metadata)

    if all_chunks:
        print("\nSample chunk:")
        print(f"Content: {all_chunks[0].page_content[:200]}...")
        print(f"Metadata: {all_chunks[0].metadata}")

    print(f"\nUploading {len(all_chunks)} chunks to namespace '{namespace}'...")
    vectorstore.add_documents(documents=all_chunks, namespace=namespace)
    print(f"Successfully embedded document into namespace '{namespace}'")
    print(f"Total chunks: {len(all_chunks)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed a document into Pinecone vector store")
    parser.add_argument("document_path", help="Path to the document file")
    parser.add_argument("namespace", help="Namespace to store the embeddings")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Size of text chunks")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Overlap between chunks")
    parser.add_argument("--metadata", type=str, help="JSON string of metadata to attach to documents")

    args = parser.parse_args()

    metadata_dict = None
    if args.metadata:
        try:
            metadata_dict = json.loads(args.metadata)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in metadata parameter")
            exit(1)

    embed_document(args.document_path, args.namespace, args.chunk_size, args.chunk_overlap, metadata_dict)
