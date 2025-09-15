import pytest
import asyncio
import pytest_asyncio
from src.utils.semantic_cache import SemanticCache
from src.core.smart_cache import SmartCache

def test_semantic_cache_initialization():
    """Test that the SemanticCache initializes correctly."""
    try:
        cache = SemanticCache()
        assert cache is not None
        assert cache.similarity_threshold == 0.95
        assert cache.index.ntotal == 0
    except ImportError:
        pytest.skip("Skipping semantic cache tests because dependencies are not installed.")

@pytest.fixture
def semantic_cache():
    """Fixture to provide a clean SemanticCache instance for each test."""
    try:
        return SemanticCache(similarity_threshold=0.9)
    except ImportError:
        pytest.skip("Skipping semantic cache tests because dependencies are not installed.")
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

# --- Integration Tests with SmartCache ---

@pytest_asyncio.fixture
async def integrated_cache():
    """Fixture for a SmartCache instance with semantic caching enabled."""
    try:
        from sentence_transformers import SentenceTransformer
        import faiss

        cache = SmartCache(enable_semantic_caching=True)
        await cache.start()
        yield cache
        await cache.stop()
    except ImportError:
        pytest.skip("Skipping integrated semantic cache tests because dependencies are not installed.")
        yield None

@pytest.mark.asyncio
async def test_smart_cache_integration_direct_hit(integrated_cache):
    """Test that a direct hit in SmartCache works as expected and doesn't trigger semantic search."""
    if integrated_cache is None:
        return

    query = "Direct hit query"
    response = "Direct response"

    hashed_key = integrated_cache.generate_key(query)

    await integrated_cache.set(hashed_key, response, original_query=query)

    result = await integrated_cache.get(hashed_key, original_query=query)

    assert result == response
    assert integrated_cache.hits == 1
    assert integrated_cache.semantic_hits == 0

@pytest.mark.asyncio
async def test_smart_cache_integration_semantic_hit(integrated_cache):
    """Test that a semantic hit works as a fallback in SmartCache."""
    if integrated_cache is None:
        return

    original_query = "What is the currency of Japan?"
    response = "The currency is the Yen."
    hashed_key_1 = integrated_cache.generate_key(original_query)
    await integrated_cache.set(hashed_key_1, response, original_query=original_query)

    similar_query = "Tell me about Japan's currency"
    hashed_key_2 = integrated_cache.generate_key(similar_query)

    result = await integrated_cache.get(hashed_key_2, original_query=similar_query)

    assert result is not None
    assert result == response
    assert integrated_cache.misses == 1
    assert integrated_cache.semantic_hits == 1
    assert integrated_cache.hits == 0

@pytest.mark.asyncio
async def test_smart_cache_integration_miss(integrated_cache):
    """Test a complete miss in both direct and semantic lookups."""
    if integrated_cache is None:
        return

    query = "Query that is not in the cache"
    hashed_key = integrated_cache.generate_key(query)

    result = await integrated_cache.get(hashed_key, original_query=query)

    assert result is None
    assert integrated_cache.misses == 1
    assert integrated_cache.semantic_hits == 0
    assert integrated_cache.hits == 0
