"""
Comprehensive tests for HTTP client utilities and external service calls
"""

import pytest
import asyncio
import threading
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from src.core.http_client import (
    OptimizedHTTPClient,
    get_http_client,
    http_client_context,
)
from src.core.http_client_v2 import (
    get_advanced_http_client,
    AdvancedHTTPClient,
)


class TestOptimizedHTTPClient:
    """Test OptimizedHTTPClient functionality"""

    @pytest.fixture
    def http_client(self):
        """Create HTTP client for testing"""
        return OptimizedHTTPClient(
            max_keepalive_connections=10,
            max_connections=100,
            timeout=5.0,
            retry_attempts=2,
            retry_backoff_factor=0.1,
        )

    @pytest.fixture
    def mock_response(self):
        """Create mock HTTP response"""
        response = MagicMock()
        response.status_code = 200
        response.headers = {"content-type": "application/json"}
        response.json.return_value = {"status": "success"}
        response.text = '{"status": "success"}'
        response.raise_for_status.return_value = None
        return response

    @pytest.mark.asyncio
    async def test_initialization(self, http_client):
        """Test client initialization"""
        assert http_client.max_keepalive_connections == 10
        assert http_client.timeout == 5.0
        assert http_client.retry_attempts == 2
        assert http_client._client is None
        assert not http_client._closed

    @pytest.mark.asyncio
    async def test_async_context_manager(self, http_client):
        """Test async context manager"""
        async with http_client as client:
            assert client._client is not None
            assert not client._closed

        assert http_client._closed

    @pytest.mark.asyncio
    async def test_manual_initialization(self, http_client):
        """Test manual initialization"""
        await http_client.initialize()
        assert http_client._client is not None
        assert isinstance(http_client._client, httpx.AsyncClient)

        # Test double initialization
        await http_client.initialize()  # Should not fail
        assert http_client._client is not None

    @pytest.mark.asyncio
    async def test_close_client(self, http_client):
        """Test client closing"""
        await http_client.initialize()
        assert not http_client._closed

        await http_client.close()
        assert http_client._closed

        # Test double close
        await http_client.close()  # Should not fail

    @pytest.mark.asyncio
    async def test_successful_request(self, http_client, mock_response):
        """Test successful HTTP request"""
        await http_client.initialize()

        with patch.object(
            http_client._client, "request", return_value=mock_response
        ) as mock_request:
            response = await http_client.request("GET", "https://api.example.com/test")

            assert response == mock_response
            mock_request.assert_called_once_with(
                method="GET",
                url="https://api.example.com/test",
                headers=None,
                json=None,
                data=None,
                params=None,
            )

    @pytest.mark.asyncio
    async def test_request_with_all_parameters(self, http_client, mock_response):
        """Test request with all parameters"""
        await http_client.initialize()

        headers = {"Authorization": "Bearer token"}
        json_data = {"key": "value"}
        params = {"param": "value"}

        with patch.object(
            http_client._client, "request", return_value=mock_response
        ) as mock_request:
            response = await http_client.request(
                "POST",
                "https://api.example.com/test",
                headers=headers,
                json=json_data,
                params=params,
            )

            mock_request.assert_called_once_with(
                method="POST",
                url="https://api.example.com/test",
                headers=headers,
                json=json_data,
                data=None,
                params=params,
            )

    @pytest.mark.asyncio
    async def test_request_auto_initialization(self, http_client, mock_response):
        """Test that request auto-initializes client"""
        # Don't call initialize first
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.request.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            response = await http_client.request("GET", "https://api.example.com/test")

            assert response == mock_response
            assert http_client._client is not None

    @pytest.mark.asyncio
    async def test_request_after_close_raises_error(self, http_client):
        """Test that request after close raises error"""
        await http_client.initialize()
        await http_client.close()

        with pytest.raises(RuntimeError, match="HTTP client is closed"):
            await http_client.request("GET", "https://api.example.com/test")

    @pytest.mark.asyncio
    async def test_connection_error_retry(self, http_client):
        """Test retry on connection errors"""
        await http_client.initialize()

        # Mock connection error that fails twice then succeeds
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(http_client._client, "request") as mock_request:
            mock_request.side_effect = [
                httpx.ConnectError("Connection failed"),
                httpx.ConnectError("Connection failed"),
                mock_response,
            ]

            response = await http_client.request("GET", "https://api.example.com/test")

            assert response == mock_response
            assert mock_request.call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_timeout_error_retry(self, http_client):
        """Test retry on timeout errors"""
        await http_client.initialize()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(http_client._client, "request") as mock_request:
            mock_request.side_effect = [
                httpx.TimeoutException("Request timed out"),
                mock_response,
            ]

            response = await http_client.request("GET", "https://api.example.com/test")

            assert response == mock_response
            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self, http_client):
        """Test that max retries are exhausted"""
        await http_client.initialize()

        with patch.object(
            http_client._client,
            "request",
            side_effect=httpx.ConnectError("Connection failed"),
        ):
            with pytest.raises(httpx.ConnectError):
                await http_client.request("GET", "https://api.example.com/test")

    @pytest.mark.asyncio
    async def test_non_retryable_error(self, http_client):
        """Test non-retryable errors don't retry"""
        await http_client.initialize()

        with patch.object(
            http_client._client,
            "request",
            side_effect=httpx.HTTPStatusError(
                "400 Bad Request",
                response=MagicMock(status_code=400),
                request=MagicMock(),
            ),
        ):
            with pytest.raises(httpx.HTTPStatusError):
                await http_client.request("GET", "https://api.example.com/test")

    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(self, http_client):
        """Test exponential backoff delays"""
        await http_client.initialize()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(http_client._client, "request") as mock_request:
            with patch("asyncio.sleep") as mock_sleep:
                mock_request.side_effect = [
                    httpx.ConnectError("Connection failed"),
                    httpx.ConnectError("Connection failed"),
                    mock_response,
                ]

                await http_client.request("GET", "https://api.example.com/test")

                # Check backoff delays: 0.1, 0.2
                expected_delays = [0.1, 0.2]
                actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
                assert actual_delays == expected_delays

    @pytest.mark.asyncio
    async def test_metrics_collection(self, http_client, mock_response):
        """Test metrics collection"""
        await http_client.initialize()

        with patch.object(http_client._client, "request", return_value=mock_response):
            await http_client.request("GET", "https://api.example.com/test")

            metrics = http_client.get_metrics()
            assert metrics["requests_total"] == 1
            assert metrics["errors_total"] == 0
            assert metrics["avg_response_time_ms"] >= 0
            assert metrics["error_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_metrics_with_errors(self, http_client):
        """Test metrics with errors"""
        await http_client.initialize()

        with patch.object(
            http_client._client,
            "request",
            side_effect=httpx.ConnectError("Connection failed"),
        ):
            with pytest.raises(httpx.ConnectError):
                await http_client.request("GET", "https://api.example.com/test")

            metrics = http_client.get_metrics()
            assert metrics["requests_total"] == 0  # Failed before making request
            assert metrics["errors_total"] >= 1  # At least one error recorded

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, http_client, mock_response):
        """Test circuit breaker integration"""
        mock_circuit_breaker = AsyncMock()
        mock_circuit_breaker.execute.return_value = mock_response
        http_client.circuit_breaker = mock_circuit_breaker

        await http_client.initialize()

        response = await http_client.request("GET", "https://api.example.com/test")

        assert response == mock_response
        mock_circuit_breaker.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_logging(self, http_client, mock_response):
        """Test request logging"""
        await http_client.initialize()

        with patch.object(http_client._client, "request", return_value=mock_response):
            with patch("src.core.http_client.logger") as mock_logger:
                await http_client.request("GET", "https://api.example.com/test")

                # Check success logging
                mock_logger.info.assert_called()
                call_args = mock_logger.info.call_args
                assert "HTTP request successful" in call_args[0][0]
                assert call_args[1]["extra"]["method"] == "GET"
                assert call_args[1]["extra"]["status_code"] == 200

    @pytest.mark.asyncio
    async def test_error_logging(self, http_client):
        """Test error logging"""
        await http_client.initialize()

        with patch.object(
            http_client._client,
            "request",
            side_effect=httpx.ConnectError("Connection failed"),
        ):
            with patch("src.core.http_client.logger") as mock_logger:
                with pytest.raises(httpx.ConnectError):
                    await http_client.request("GET", "https://api.example.com/test")

                # Check error logging
                mock_logger.error.assert_called()
                call_args = mock_logger.error.call_args
                assert "HTTP request failed after all retries" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_retry_logging(self, http_client):
        """Test retry logging"""
        await http_client.initialize()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(http_client._client, "request") as mock_request:
            with patch("src.core.http_client.logger") as mock_logger:
                mock_request.side_effect = [
                    httpx.ConnectError("Connection failed"),
                    mock_response,
                ]

                await http_client.request("GET", "https://api.example.com/test")

                # Check retry logging
                mock_logger.warning.assert_called()
                call_args = mock_logger.warning.call_args
                assert "HTTP request failed, retrying" in call_args[0][0]
                assert call_args[1]["extra"]["attempt"] == 1


class TestHTTPClientGlobalFunctions:
    """Test global HTTP client functions"""

    @pytest.mark.asyncio
    async def test_get_http_client_creates_instance(self):
        """Test get_http_client creates new instance"""
        with patch("src.core.http_client._http_client", None):
            client = await get_http_client()
            assert isinstance(client, OptimizedHTTPClient)
            assert client._client is not None

    @pytest.mark.asyncio
    async def test_get_http_client_reuses_instance(self):
        """Test get_http_client reuses existing instance"""
        with patch("src.core.http_client._http_client", None):
            client1 = await get_http_client()
            client2 = await get_http_client()
            assert client1 is client2

    @pytest.mark.asyncio
    async def test_get_http_client_recreates_closed_instance(self):
        """Test get_http_client recreates closed instance"""
        with patch("src.core.http_client._http_client", None):
            client1 = await get_http_client()
            await client1.close()

            client2 = await get_http_client()
            assert client1 is not client2
            assert not client2._closed

    @pytest.mark.asyncio
    async def test_http_client_context(self):
        """Test http_client_context context manager"""
        with patch("src.core.http_client._http_client", None):
            async with http_client_context() as client:
                assert isinstance(client, OptimizedHTTPClient)
                assert client._client is not None

            # Global client should not be closed
            global_client = await get_http_client()
            assert not global_client._closed


class TestHTTPClientTimeoutScenarios:
    """Test timeout-specific scenarios"""

    @pytest.fixture
    def timeout_client(self):
        """Create client with short timeout for testing"""
        return OptimizedHTTPClient(
            timeout=0.1,
            connect_timeout=0.05,
            retry_attempts=1,  # Very short timeout
        )

    @pytest.mark.asyncio
    async def test_connect_timeout(self, timeout_client):
        """Test connection timeout"""
        await timeout_client.initialize()

        with patch.object(
            timeout_client._client,
            "request",
            side_effect=httpx.ConnectTimeout("Connect timeout"),
        ):
            with pytest.raises(httpx.ConnectTimeout):
                await timeout_client.request("GET", "https://api.example.com/test")

    @pytest.mark.asyncio
    async def test_read_timeout(self, timeout_client):
        """Test read timeout"""
        await timeout_client.initialize()

        with patch.object(
            timeout_client._client,
            "request",
            side_effect=httpx.ReadTimeout("Read timeout"),
        ):
            with pytest.raises(httpx.ReadTimeout):
                await timeout_client.request("GET", "https://api.example.com/test")

    @pytest.mark.asyncio
    async def test_timeout_with_retry(self, timeout_client):
        """Test timeout with retry"""
        await timeout_client.initialize()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(timeout_client._client, "request") as mock_request:
            mock_request.side_effect = [
                httpx.TimeoutException("Timeout"),
                mock_response,
            ]

            response = await timeout_client.request(
                "GET", "https://api.example.com/test"
            )

            assert response == mock_response
            assert mock_request.call_count == 2


class TestHTTPClientErrorScenarios:
    """Test various error scenarios"""

    @pytest.fixture
    def error_client(self):
        """Create client for error testing"""
        return OptimizedHTTPClient(retry_attempts=0)  # No retries for cleaner tests

    @pytest.mark.asyncio
    async def test_4xx_errors_not_retried(self, error_client):
        """Test 4xx errors are not retried"""
        await error_client.initialize()

        response = MagicMock()
        response.status_code = 400
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request", response=response, request=MagicMock()
        )

        with patch.object(error_client._client, "request", return_value=response):
            with pytest.raises(httpx.HTTPStatusError):
                await error_client.request("GET", "https://api.example.com/test")

    @pytest.mark.asyncio
    async def test_5xx_errors_retried(self, error_client):
        """Test 5xx errors are retried"""
        await error_client.initialize()

        response = MagicMock()
        response.status_code = 500
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error", response=response, request=MagicMock()
        )

        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.raise_for_status.return_value = None

        with patch.object(error_client._client, "request") as mock_request:
            mock_request.side_effect = [response, mock_success_response]

            result = await error_client.request("GET", "https://api.example.com/test")

            assert result == mock_success_response
            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_network_errors_retried(self, error_client):
        """Test network errors are retried"""
        await error_client.initialize()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(error_client._client, "request") as mock_request:
            mock_request.side_effect = [
                httpx.NetworkError("Network error"),
                mock_response,
            ]

            result = await error_client.request("GET", "https://api.example.com/test")

            assert result == mock_response
            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_ssl_errors_not_retried(self, error_client):
        """Test SSL errors are not retried"""
        await error_client.initialize()

        # Create a custom SSL error class
        class SSLError(Exception):
            pass

        ssl_error = SSLError("SSL certificate verify failed")

        with patch.object(error_client._client, "request", side_effect=ssl_error):
            with pytest.raises(SSLError) as exc_info:
                await error_client.request("GET", "https://api.example.com/test")

            assert "SSL certificate verify failed" in str(exc_info.value)


class TestHTTPClientMetrics:
    """Test metrics collection and reporting"""

    @pytest.fixture
    def metrics_client(self):
        """Create client for metrics testing"""
        return OptimizedHTTPClient()

    @pytest.mark.asyncio
    async def test_initial_metrics(self, metrics_client):
        """Test initial metrics state"""
        metrics = metrics_client.get_metrics()

        assert metrics["requests_total"] == 0
        assert metrics["errors_total"] == 0
        assert metrics["avg_response_time_ms"] == 0
        assert metrics["error_rate"] == 0

    @pytest.mark.asyncio
    async def test_metrics_after_successful_requests(self, metrics_client):
        """Test metrics after successful requests"""
        await metrics_client.initialize()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None

        with patch.object(
            metrics_client._client, "request", return_value=mock_response
        ):
            await metrics_client.request("GET", "https://api.example.com/test1")
            await metrics_client.request("GET", "https://api.example.com/test2")

            metrics = metrics_client.get_metrics()

            assert metrics["requests_total"] == 2
            assert metrics["errors_total"] == 0
            assert metrics["avg_response_time_ms"] >= 0
            assert metrics["error_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_metrics_with_mixed_results(self, metrics_client):
        """Test metrics with mixed success/failure"""
        await metrics_client.initialize()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None

        with patch.object(metrics_client._client, "request") as mock_request:
            # Success
            mock_request.return_value = mock_response
            await metrics_client.request("GET", "https://api.example.com/success")

            # Failure
            mock_request.side_effect = httpx.ConnectError("Connection failed")
            with pytest.raises(httpx.ConnectError):
                await metrics_client.request("GET", "https://api.example.com/failure")

            metrics = metrics_client.get_metrics()

            assert metrics["requests_total"] == 1  # Only successful request counted
            assert metrics["errors_total"] >= 1  # At least one error recorded
            assert metrics["error_rate"] == 1.0  # 1 error out of 1 total request

    @pytest.mark.asyncio
    async def test_connection_pool_metrics(self, metrics_client):
        """Test connection pool metrics"""
        await metrics_client.initialize()

        with patch("src.core.http_client.metrics_collector") as mock_collector:
            metrics_client.get_metrics()

            # Verify connection pool metrics are sent to collector
            mock_collector.update_connection_pool_metrics.assert_called_once()
            call_args = mock_collector.update_connection_pool_metrics.call_args[0][0]

            assert "max_keepalive_connections" in call_args
            assert "max_connections" in call_args
            assert "total_requests" in call_args
            assert "error_count" in call_args


class TestRaceConditionFixes:
    """Test race condition fixes in global instance management"""

    @pytest.mark.asyncio
    async def test_concurrent_get_http_client_creates_single_instance(self):
        """Test that concurrent calls to get_http_client create only one instance"""
        with patch("src.core.http_client._http_client", None):
            # Create multiple concurrent tasks
            tasks = [get_http_client() for _ in range(10)]
            clients = await asyncio.gather(*tasks)

            # All should be the same instance
            first_client = clients[0]
            for client in clients[1:]:
                assert client is first_client

            assert isinstance(first_client, OptimizedHTTPClient)

    def test_concurrent_get_advanced_http_client_creates_single_instance(self):
        """Test that concurrent calls to get_advanced_http_client create only one instance per provider"""
        with patch("src.core.http_client_v2._http_clients", {}):
            results = []
            exceptions = []

            def get_client():
                try:
                    client = get_advanced_http_client("test_provider")
                    results.append(client)
                except Exception as e:
                    exceptions.append(e)

            # Create multiple threads
            threads = []
            for _ in range(10):
                t = threading.Thread(target=get_client)
                threads.append(t)
                t.start()

            # Wait for all threads
            for t in threads:
                t.join()

            # Check results
            assert len(exceptions) == 0
            assert len(results) == 10

            # All should be the same instance
            first_client = results[0]
            for client in results[1:]:
                assert client is first_client

            assert isinstance(first_client, AdvancedHTTPClient)
            assert first_client.provider_name == "test_provider"

    def test_concurrent_different_providers_create_separate_instances(self):
        """Test that different providers get separate instances"""
        with patch("src.core.http_client_v2._http_clients", {}):
            results = {}
            exceptions = []

            def get_client(provider):
                try:
                    client = get_advanced_http_client(provider)
                    if provider not in results:
                        results[provider] = []
                    results[provider].append(client)
                except Exception as e:
                    exceptions.append(e)

            # Create multiple threads for different providers
            threads = []
            providers = ["provider1", "provider2", "provider1", "provider2"]
            for provider in providers:
                t = threading.Thread(target=get_client, args=(provider,))
                threads.append(t)
                t.start()

            # Wait for all threads
            for t in threads:
                t.join()

            # Check results
            assert len(exceptions) == 0
            assert len(results) == 2

            # provider1 instances should be the same
            provider1_clients = results["provider1"]
            first_p1 = provider1_clients[0]
            for client in provider1_clients[1:]:
                assert client is first_p1

            # provider2 instances should be the same
            provider2_clients = results["provider2"]
            first_p2 = provider2_clients[0]
            for client in provider2_clients[1:]:
                assert client is first_p2

            # Different providers should have different instances
            assert first_p1 is not first_p2


if __name__ == "__main__":
    pytest.main([__file__])
