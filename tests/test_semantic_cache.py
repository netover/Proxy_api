import pytest
from src.utils.semantic_cache import SemanticCache


def test_semantic_cache_initialization():
    """Test that the SemanticCache initializes correctly."""
    try:
        cache = SemanticCache()
        assert cache is not None
        assert cache.similarity_threshold == 0.95
        assert cache.index.ntotal == 0
    except ImportError:
        pytest.skip(
            "Skipping semantic cache tests because dependencies are not installed."
        )


@pytest.fixture
def semantic_cache():
    """Fixture to provide a clean SemanticCache instance for each test."""
    try:
        return SemanticCache(similarity_threshold=0.9)
    except ImportError:
        pytest.skip(
            "Skipping semantic cache tests because dependencies are not installed."
        )
        return None


def test_add_and_search_exact_match(semantic_cache):
    """Test adding an item and searching for the exact same query."""
    if semantic_cache is None:
        return

    query = "What is the weather like in London?"
    response = {"temp": "15C", "condition": "cloudy"}

    semantic_cache.add(query, response)

    result = semantic_cache.search(query)
    assert result is not None
    assert result == response


def test_search_semantically_similar(semantic_cache):
    """Test searching for a semantically similar query."""
    if semantic_cache is None:
        return

    query1 = "How is the weather in London today?"
    response1 = {"temp": "15C", "condition": "cloudy"}
    semantic_cache.add(query1, response1)

    query2 = "What's the forecast for London?"
    response2 = {"temp": "16C", "condition": "sunny"}
    semantic_cache.add(query2, response2)

    search_query = "Tell me about the weather in London."
    result = semantic_cache.search(search_query)

    assert result is not None
    assert result == response1


def test_search_dissimilar(semantic_cache):
    """Test searching for a query that is not similar to anything in the cache."""
    if semantic_cache is None:
        return

    query = "What is the capital of France?"
    response = {"capital": "Paris"}
    semantic_cache.add(query, response)

    search_query = "Who wrote the play Hamlet?"
    result = semantic_cache.search(search_query)

    assert result is None


def test_empty_cache_search(semantic_cache):
    """Test searching in an empty cache."""
    if semantic_cache is None:
        return

    result = semantic_cache.search("Anything")
    assert result is None
