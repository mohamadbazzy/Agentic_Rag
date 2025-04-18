from typing import Dict, List, Optional
import os
import json
import logging
from .agent_index_wrapper import register_agent_namespaces

# Set up logging
logger = logging.getLogger(__name__)
# Update the DEFAULT_NAMESPACE_CONFIG to include all agents

DEFAULT_NAMESPACE_CONFIG = {
    "advisor": ["advisor_namespace"],
    "supervisor": ["supervisor_namespace"],
    "mechanical": ["mechanical_namespace"],
    "chemical": ["chemical_namespace"],
    "civil": ["civil_namespace"],
    "ece": ["ece_namespace"],
    "ece_track": ["ece_namespace"],
    "cse": ["cse_namespace"],
    "cce": ["cce_namespace"],
    "msfea_advisor": ["msfea_advisor_namespace"],
    # Added new namespaces for future agents
    "industrial": ["industrial_namespace"],
    "gpa": ["gpa_namespace"],
    "schedule_maker": ["schedule_maker_namespace"],
    # Add any other departments or agents as needed
}

def load_namespace_config() -> Dict[str, List[str]]:
    """
    Load the namespace configuration from environment, file, or use default.
    
    Returns:
        A dictionary mapping agent IDs to lists of allowed namespaces
    """
    # Try loading from environment variable
    config_json = os.environ.get("AGENT_NAMESPACE_CONFIG")
    if config_json:
        try:
            config = json.loads(config_json)
            logger.info("Loaded namespace configuration from environment variable")
            return _validate_config(config)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in AGENT_NAMESPACE_CONFIG environment variable")
    
    # Try loading from config file
    config_path = os.environ.get("AGENT_NAMESPACE_CONFIG_PATH", "agent_namespaces.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded namespace configuration from file: {config_path}")
                return _validate_config(config)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load namespace config file: {e}")
    
    # Fall back to default configuration
    logger.info("Using default namespace configuration")
    return DEFAULT_NAMESPACE_CONFIG

def _validate_config(config):
    """Validate the configuration format"""
    if not isinstance(config, dict):
        logger.warning("Invalid configuration format, expecting a dictionary. Using default configuration.")
        return DEFAULT_NAMESPACE_CONFIG
    
    # Ensure all values are lists of strings
    validated_config = {}
    for agent_id, namespaces in config.items():
        if not isinstance(namespaces, list):
            logger.warning(f"Invalid namespaces for agent '{agent_id}', expecting a list. Skipping.")
            continue
            
        # Filter out non-string namespaces
        string_namespaces = [ns for ns in namespaces if isinstance(ns, str)]
        if len(string_namespaces) != len(namespaces):
            logger.warning(f"Some namespaces for agent '{agent_id}' were not strings and were filtered out")
        
        if string_namespaces:  # Only add if there are valid namespaces
            validated_config[agent_id] = string_namespaces
    
    return validated_config

def initialize_agent_namespaces():
    """
    Initialize the namespace registry with the configured namespaces.
    This should be called during application startup.
    """
    logger.info("Initializing agent namespace registry")
    config = load_namespace_config()
    
    for agent_id, namespaces in config.items():
        register_agent_namespaces(agent_id, namespaces)
    
    logger.info(f"Registered {len(config)} agents with their namespace permissions")