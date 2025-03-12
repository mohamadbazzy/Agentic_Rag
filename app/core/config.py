import os
from dotenv import load_dotenv, dotenv_values

def load_environment():
    """Load environment variables from .env file"""
    try:
        load_dotenv()
    except UnicodeDecodeError:
        # If UTF-8 fails, try with utf-16
        config = dotenv_values(".env", encoding="utf-16")
        
        # Set environment variables manually
        for key, value in config.items():
            os.environ[key] = value

# Initialize environment variables
load_environment()

# Environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your_openai_api_key")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "your_pinecone_api_key")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT", "your_pinecone_environment")
LANGCHAIN_API_KEY = os.environ.get("LANGCHAIN_API_KEY", "your_langchain_api_key")

# Optional LangSmith tracing
os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "AcademicAdvisorSystem"

# Pinecone configuration
INDEX_NAME = "academic-advisor-knowledge"
