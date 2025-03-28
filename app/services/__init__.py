import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import after configuring logging
from .namespace_config import initialize_agent_namespaces

# Initialize agent namespaces on module import
initialize_agent_namespaces()