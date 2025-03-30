# This file allows the package to be run with python -m
import logging
import time
from app.services.namespace_config import DEFAULT_NAMESPACE_CONFIG
from app.services.agent_index_wrapper import register_agent_namespaces

# Set up logging
logger = logging.getLogger(__name__)

logger.info("Department Agents Service Starting...")

if __name__ == "__main__":
    try:
        # Register namespaces for all department agents
        logger.info("Registering namespaces for department agents...")
        register_agent_namespaces(DEFAULT_NAMESPACE_CONFIG)
        
        logger.info("Department Agents ready and waiting for queries")
        # Keep the process running
        while True:
            time.sleep(60)
    except Exception as e:
        logger.error(f"Error in department service: {e}") 