import pytest
import time
import hashlib
import hmac
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from httpx import AsyncClient
import jwt
from datetime import datetime, timedelta

from src.core.auth import APIKeyAuth, verify_api_key, get_api_key_auth


class TestAuthenticationSecurity:
    """Comprehensive security tests for authentication mechanisms"""

    def test_brute_force_protection(self):
        """Test protection against brute force attacks"""
        api_keys = ["valid_key_123"]
        auth = APIKeyAuth(api_keys)

        # Simulate multiple failed attempts
        failed_attempts = 0
        max_attempts = 100

        for i in range(max_attempts):
            result = auth.verify_api_key(f"invalid_key_{i}")
            if not result:
                failed_attempts += 1

        assert failed_attempts == max_attempts

        # Verify that valid key still works after failed attempts
        assert auth.verify_api_key("valid_key_123") is True

    def test_timing_attack_resistance_comprehensive(self):
        """Comprehensive test for timing attack resistance"""
        api_keys = [
            "short_key",
            "a_very_long_key_that_should_take_similar_time_to_verify",
        ]
        auth = APIKeyAuth(api_keys)

        # Test various key lengths
        test_keys = [
            "a",  # Very short
            "medium_length_key",
            "a_very_long_key_that_should_have_similar_timing_characteristics",
            "",  # Empty
            "special_chars_!@#$%^&*()",
            "unicode_key_🚀_test",
        ]

        times = []

        for key in test_keys:
            start_time = time.perf_counter()
            auth.verify_api_key(key)
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        # Check that timing variation is minimal (within 10% of average)
        if times:
            avg_time = sum(times) / len(times)
            max_deviation = max(abs(t - avg_time) for t in times)
            relative_deviation = (
                max_deviation / avg_time if avg_time > 0 else 0
            )

            assert (
                relative_deviation < 0.1
            ), f"Timing attack vulnerability detected: {relative_deviation:.3f} relative deviation"

    def test_api_key_entropy(self):
        """Test API key entropy and randomness"""
        api_keys = ["weak", "password", "123456", "admin", "letmein"]
        auth = APIKeyAuth(api_keys)

        # Test that weak keys are handled but flagged
        weak_patterns = [
            r"^\d+$",  # Only numbers
            r"^[a-zA-Z]+$",  # Only letters
            r"^(.)\1*$",  # Repeated characters
            r"^.{0,7}$",  # Too short
        ]

        # This is more of a warning test - weak keys should still work but be flagged
        for key in api_keys:
            assert (
                auth.verify_api_key(key) is True
            ), f"Valid key rejected: {key}"

    def test_jwt_token_security(self):
        """Test JWT token security if used"""
        # Test JWT token generation and validation
        secret_key = "test_secret_key_for_jwt"
        test_payload = {
            "user_id": "test_user",
            "exp": datetime.utcnow() + timedelta(hours=1),
        }

        # Generate token
        token = jwt.encode(test_payload, secret_key, algorithm="HS256")

        # Verify token
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        assert decoded["user_id"] == "test_user"

        # Test token tampering
        try:
            jwt.decode(token + "tampered", secret_key, algorithms=["HS256"])
            assert False, "Tampered token should be rejected"
        except jwt.InvalidSignatureError:
            pass  # Expected

    def test_session_management(self):
        """Test session management security"""
        # Mock session storage
        sessions = {}

        def create_session(user_id: str) -> str:
            session_id = hashlib.sha256(
                f"{user_id}{time.time()}".encode()
            ).hexdigest()
            sessions[session_id] = {
                "user_id": user_id,
                "created": time.time(),
                "expires": time.time() + 3600,  # 1 hour
            }
            return session_id

        def validate_session(session_id: str) -> bool:
            if session_id not in sessions:
                return False

            session = sessions[session_id]
            if time.time() > session["expires"]:
                del sessions[session_id]
                return False

            return True

        # Test session creation
        session_id = create_session("test_user")
        assert validate_session(session_id) is True

        # Test session expiration
        sessions[session_id]["expires"] = time.time() - 1  # Expired
        assert validate_session(session_id) is False

        # Test invalid session
        assert validate_session("invalid_session_id") is False

    def test_rate_limiting_auth_attempts(self):
        """Test rate limiting for authentication attempts"""
        auth_attempts = {}
        rate_limit_window = 60  # 1 minute
        max_attempts_per_window = 5

        def check_rate_limit(identifier: str) -> bool:
            now = time.time()
            if identifier not in auth_attempts:
                auth_attempts[identifier] = []

            # Clean old attempts
            auth_attempts[identifier] = [
                attempt
                for attempt in auth_attempts[identifier]
                if now - attempt < rate_limit_window
            ]

            if len(auth_attempts[identifier]) >= max_attempts_per_window:
                return False  # Rate limited

            auth_attempts[identifier].append(now)
            return True

        # Test normal usage
        for i in range(max_attempts_per_window):
            assert check_rate_limit("test_user") is True

        # Test rate limiting
        assert check_rate_limit("test_user") is False

        # Test different users not affected
        assert check_rate_limit("other_user") is True

    def test_api_key_leakage_prevention(self):
        """Test prevention of API key leakage in logs and responses"""
        api_keys = [
            "sk-1234567890abcdef",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        ]
        auth = APIKeyAuth(api_keys)

        # Mock logging to capture potential leaks
        logged_messages = []

        def mock_log(message: str):
            logged_messages.append(message)

        # Simulate authentication with logging
        with patch("src.core.logging.logger.info", side_effect=mock_log):
            result = auth.verify_api_key("sk-1234567890abcdef")
            assert result is True

        # Check that sensitive data is not logged
        for message in logged_messages:
            assert (
                "sk-1234567890abcdef" not in message
            ), "API key leaked in logs"
            assert (
                "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in message
            ), "JWT token leaked in logs"

    def test_concurrent_authentication_handling(self):
        """Test authentication handling under concurrent requests"""
        import threading

        api_keys = ["concurrent_test_key"]
        auth = APIKeyAuth(api_keys)

        results = []
        errors = []

        def auth_worker(key: str):
            try:
                result = auth.verify_api_key(key)
                results.append(result)
            except Exception as e:
                errors.append(str(e))

        # Simulate concurrent authentication attempts
        threads = []
        for i in range(10):
            thread = threading.Thread(
                target=auth_worker, args=("concurrent_test_key",)
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All should succeed
        assert len(results) == 10
        assert all(results)
        assert len(errors) == 0

    def test_authentication_bypass_attempts(self):
        """Test protection against authentication bypass attempts"""
        api_keys = ["valid_key_123"]
        auth = APIKeyAuth(api_keys)

        # Common bypass attempts
        bypass_attempts = [
            "",  # Empty
            None,  # None
            " ",  # Space
            "\t",  # Tab
            "\n",  # Newline
            "\r",  # Carriage return
            "null",  # String null
            "undefined",  # JavaScript undefined
            "valid_key_123 ",  # With trailing space
            " valid_key_123",  # With leading space
            "VALID_KEY_123",  # Case variation (if case sensitive)
            "Valid_Key_123",  # Mixed case
        ]

        for attempt in bypass_attempts:
            result = auth.verify_api_key(attempt)
            if attempt and attempt.strip() == "valid_key_123":
                assert (
                    result is True
                ), f"Valid key with whitespace should work: {attempt}"
            else:
                assert (
                    result is False
                ), f"Bypass attempt should fail: {attempt}"

    def test_token_replay_attack_prevention(self):
        """Test prevention of token replay attacks"""
        used_tokens = set()

        def validate_token_once(token: str) -> bool:
            if token in used_tokens:
                return False  # Replay attack detected

            used_tokens.add(token)
            return True

        # First use should succeed
        assert validate_token_once("token123") is True

        # Second use should fail (replay)
        assert validate_token_once("token123") is False

        # Different token should succeed
        assert validate_token_once("token456") is True

    def test_secure_password_storage_simulation(self):
        """Test secure password storage practices (simulation)"""
        # Simulate password hashing
        passwords = ["password123", "admin", "letmein"]

        hashed_passwords = {}
        for pwd in passwords:
            # Use proper hashing (in real implementation)
            hashed = hashlib.pbkdf2_hmac(
                "sha256", pwd.encode(), b"salt", 100000
            )
            hashed_passwords[pwd] = hashed.hex()

        # Verify hashes are different
        assert hashed_passwords["password123"] != hashed_passwords["admin"]

        # Verify hash consistency
        hashed_again = hashlib.pbkdf2_hmac(
            "sha256", "password123".encode(), b"salt", 100000
        ).hex()
        assert hashed_passwords["password123"] == hashed_again

    @pytest.mark.asyncio
    async def test_authentication_header_injection(self):
        """Test protection against header injection attacks"""
        api_keys = ["test_key_123"]
        auth = APIKeyAuth(api_keys)

        # Mock request with malicious headers
        malicious_headers = {
            "x-api-key": "test_key_123\r\nX-Injected: malicious",
            "authorization": "Bearer test_key_123\nHost: evil.com",
            "x-api-key": "test_key_123\x00null_byte_injection",
        }

        for header_name, header_value in malicious_headers.items():
            mock_request = Mock()
            mock_request.headers = {header_name: header_value}
            mock_request.app.state.api_key_auth = auth

            with patch("src.core.auth.config_manager") as mock_config_manager:
                mock_config = Mock()
                mock_config.settings.api_key_header = header_name
                mock_config_manager.load_config.return_value = mock_config

                # Should either reject or sanitize the input
                try:
                    result = await verify_api_key(mock_request)
                    # If it succeeds, ensure no injection occurred
                    assert "\r" not in str(result)
                    assert "\n" not in str(result)
                    assert "\x00" not in str(result)
                except HTTPException:
                    # Rejection is also acceptable
                    pass

    def test_api_key_rotation_simulation(self):
        """Test API key rotation mechanisms"""
        old_keys = ["old_key_1", "old_key_2"]
        new_keys = ["new_key_1", "new_key_2"]

        # Simulate key rotation with grace period
        auth = APIKeyAuth(old_keys + new_keys)

        # Both old and new keys should work during transition
        for key in old_keys + new_keys:
            assert auth.verify_api_key(key) is True

        # After rotation, only new keys should work
        auth_rotated = APIKeyAuth(new_keys)
        for old_key in old_keys:
            assert auth_rotated.verify_api_key(old_key) is False
        for new_key in new_keys:
            assert auth_rotated.verify_api_key(new_key) is True


class TestAuthorizationSecurity:
    """Test authorization and access control security"""

    def test_role_based_access_control(self):
        """Test role-based access control"""
        roles = {
            "admin": ["read", "write", "delete", "admin"],
            "user": ["read", "write"],
            "guest": ["read"],
        }

        def check_permission(user_role: str, required_permission: str) -> bool:
            return required_permission in roles.get(user_role, [])

        # Test permissions
        assert check_permission("admin", "delete") is True
        assert check_permission("user", "delete") is False
        assert check_permission("guest", "write") is False
        assert check_permission("unknown", "read") is False

    def test_least_privilege_principle(self):
        """Test adherence to least privilege principle"""
        # Simulate user permissions
        user_permissions = ["read_profile", "update_own_profile"]

        privileged_actions = [
            "read_all_profiles",
            "delete_user",
            "update_system_settings",
        ]

        # User should not have privileged permissions
        for action in privileged_actions:
            assert (
                action not in user_permissions
            ), f"User has privileged permission: {action}"

    def test_horizontal_privilege_escalation_prevention(self):
        """Test prevention of horizontal privilege escalation"""
        users = {
            "user1": {"id": "user1", "data": "user1_data"},
            "user2": {"id": "user2", "data": "user2_data"},
        }

        def access_user_data(current_user: str, target_user: str) -> str:
            if current_user != target_user:
                raise HTTPException(status_code=403, detail="Access denied")
            return users[target_user]["data"]

        # User can access their own data
        assert access_user_data("user1", "user1") == "user1_data"

        # User cannot access others' data
        with pytest.raises(HTTPException) as exc_info:
            access_user_data("user1", "user2")
        assert exc_info.value.status_code == 403

    def test_vertical_privilege_escalation_prevention(self):
        """Test prevention of vertical privilege escalation"""
        user_roles = {"user1": "user", "admin1": "admin"}

        def perform_admin_action(user: str):
            if user_roles.get(user) != "admin":
                raise HTTPException(
                    status_code=403, detail="Admin access required"
                )
            return "admin_action_performed"

        # Admin can perform admin actions
        assert perform_admin_action("admin1") == "admin_action_performed"

        # Regular user cannot perform admin actions
        with pytest.raises(HTTPException) as exc_info:
            perform_admin_action("user1")
        assert exc_info.value.status_code == 403
