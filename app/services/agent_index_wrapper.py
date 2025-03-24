from typing import Dict, List, Optional, Union, Any, Literal, cast
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
import json
import logging

# Set up logging
logger = logging.getLogger(__name__)

class AgentNamespaceRegistry:
    """Registry that maintains which agent has access to which namespaces."""
    
    def __init__(self):
        self._registry = {}  # agent_id -> list of allowed namespaces
    
    def register_agent(self, agent_id: str, namespaces: List[str]):
        """Register an agent with its allowed namespaces."""
        self._registry[agent_id] = list(set(namespaces))
        logger.info(f"Registered agent '{agent_id}' with namespaces: {namespaces}")
    
    def get_allowed_namespaces(self, agent_id: str) -> List[str]:
        """Get the namespaces an agent is allowed to access."""
        namespaces = self._registry.get(agent_id, [])
        if not namespaces:
            logger.warning(f"Agent '{agent_id}' has no registered namespaces")
        return namespaces
    
    def has_namespace_access(self, agent_id: str, namespace: str) -> bool:
        """Check if an agent has access to a specific namespace."""
        if agent_id not in self._registry:
            logger.warning(f"Agent '{agent_id}' is not registered in the namespace registry")
            return False
        
        has_access = namespace in self._registry[agent_id]
        if not has_access:
            logger.debug(f"Agent '{agent_id}' denied access to namespace '{namespace}'")
        return has_access


# Global registry instance
namespace_registry = AgentNamespaceRegistry()


class AgentRestrictedIndex:
    """
    A wrapper around Pinecone Index that enforces namespace restrictions for agents.
    This class intercepts all calls to methods that interact with namespaces and
    verifies the agent has access to the requested namespace.
    """
    
    def __init__(self, index, agent_id: str):
        """
        Initialize the restricted index.
        
        Args:
            index: The underlying Pinecone index
            agent_id: The ID of the agent using this index
        """
        self._index = index
        self._agent_id = agent_id
        self._allowed_namespaces = namespace_registry.get_allowed_namespaces(agent_id)
        logger.info(f"Created restricted index for agent '{agent_id}' with allowed namespaces: {self._allowed_namespaces}")
    
    def _check_namespace_access(self, namespace: Optional[str]) -> str:
        """
        Check if the agent has access to the specified namespace.
        """
        # If namespace is None or empty, use the agent's specific namespace
        if not namespace:
            # Use the first allowed namespace for this agent
            if self._allowed_namespaces:
                namespace = self._allowed_namespaces[0]
                logger.info(f"Using default namespace '{namespace}' for agent '{self._agent_id}'")
            else:
                namespace = ''  # Empty string is default if no allowed namespaces
        
        if not namespace_registry.has_namespace_access(self._agent_id, namespace):
            raise PermissionError(
                f"Agent '{self._agent_id}' does not have access to namespace '{namespace}'. "
                f"Allowed namespaces: {self._allowed_namespaces}"
            )
        
        return namespace
    
    def query(self, vector, namespace=None, top_k=None, filter=None, include_values=None, 
              include_metadata=None, sparse_vector=None, **kwargs):
        """
        Wrapper for the query method that enforces namespace restrictions.
        """
        namespace = self._check_namespace_access(namespace)
        
        return self._index.query(
            vector=vector,
            namespace=namespace,
            top_k=top_k,
            filter=filter,
            include_values=include_values,
            include_metadata=include_metadata,
            sparse_vector=sparse_vector,
            **kwargs
        )
    
    def query_namespaces(self, vector, namespaces, metric, top_k=None, filter=None, 
                         include_values=None, include_metadata=None, sparse_vector=None, **kwargs):
        """
        Wrapper for query_namespaces that filters out unauthorized namespaces.
        """
        if not namespaces:
            raise ValueError("At least one namespace must be specified")
            
        # Filter namespaces to only include those the agent has access to
        authorized_namespaces = [
            ns for ns in namespaces 
            if namespace_registry.has_namespace_access(self._agent_id, ns)
        ]
        
        if not authorized_namespaces:
            raise PermissionError(
                f"Agent '{self._agent_id}' does not have access to any of the requested namespaces: {namespaces}. "
                f"Allowed namespaces: {self._allowed_namespaces}"
            )
        
        logger.info(f"Agent '{self._agent_id}' querying authorized namespaces: {authorized_namespaces}")
        
        # Call the original query_namespaces with only the authorized namespaces
        return self._index.query_namespaces(
            vector=vector,
            namespaces=authorized_namespaces,
            metric=metric,
            top_k=top_k,
            filter=filter,
            include_values=include_values,
            include_metadata=include_metadata,
            sparse_vector=sparse_vector,
            **kwargs
        )
    
    def upsert(self, vectors, namespace=None, batch_size=None, show_progress=None, **kwargs):
        """
        Wrapper for the upsert method that enforces namespace restrictions.
        """
        namespace = self._check_namespace_access(namespace)
        
        return self._index.upsert(
            vectors=vectors, 
            namespace=namespace, 
            batch_size=batch_size,
            show_progress=show_progress,
            **kwargs
        )
    
    def delete(self, ids=None, delete_all=None, namespace=None, filter=None, **kwargs):
        """
        Wrapper for the delete method that enforces namespace restrictions.
        """
        namespace = self._check_namespace_access(namespace)
        
        return self._index.delete(
            ids=ids,
            delete_all=delete_all,
            namespace=namespace,
            filter=filter,
            **kwargs
        )
    
    def update(self, id, values=None, set_metadata=None, namespace=None, sparse_values=None, **kwargs):
        """
        Wrapper for the update method that enforces namespace restrictions.
        """
        namespace = self._check_namespace_access(namespace)
        
        return self._index.update(
            id=id,
            values=values,
            set_metadata=set_metadata,
            namespace=namespace,
            sparse_values=sparse_values,
            **kwargs
        )
    
    def fetch(self, ids, namespace=None, **kwargs):
        """
        Wrapper for the fetch method that enforces namespace restrictions.
        """
        namespace = self._check_namespace_access(namespace)
        
        return self._index.fetch(ids=ids, namespace=namespace, **kwargs)
    
    def list(self, prefix=None, limit=None, pagination_token=None, namespace=None, **kwargs):
        """
        Wrapper for the list method that enforces namespace restrictions.
        """
        namespace = self._check_namespace_access(namespace)
        
        return self._index.list(
            prefix=prefix,
            limit=limit,
            pagination_token=pagination_token,
            namespace=namespace,
            **kwargs
        )
    
    def describe_index_stats(self, filter=None, **kwargs):
        """
        Pass through for describe_index_stats.
        Note: This method may reveal information about namespaces the agent doesn't have access to.
        A more restrictive implementation could filter the results.
        """
        return self._index.describe_index_stats(filter=filter, **kwargs)
    
    # Pass through any other methods/attributes to the underlying index
    def __getattr__(self, name):
        return getattr(self._index, name)


def get_restricted_index(index, agent_id: str) -> AgentRestrictedIndex:
    """
    Factory function to create a namespace-restricted index for an agent.
    
    Args:
        index: The Pinecone index to wrap
        agent_id: The ID of the agent that will use this index
        
    Returns:
        A namespace-restricted index
    """
    return AgentRestrictedIndex(index, agent_id)


def register_agent_namespaces(agent_id: str, namespaces: List[str]):
    """
    Register which namespaces an agent is allowed to access.
    
    Args:
        agent_id: The ID of the agent
        namespaces: List of namespaces the agent is allowed to access
    """
    namespace_registry.register_agent(agent_id, namespaces)