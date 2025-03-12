import pytest
from app.services.advisor import advisor_graph

@pytest.fixture
def advisor_graph_fixture():
    """Return the advisor graph for testing"""
    return advisor_graph
