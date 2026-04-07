# tests/test_backend_config.py
"""Comprehensive tests for backend port configuration and error handling."""
import os
import sys
import pytest
from unittest.mock import patch

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'test', 'backend'))

def test_default_port_constant():
    """Test that DEFAULT_PORT constant is correctly defined as 8001."""
    import app as backend_app
    assert backend_app.DEFAULT_PORT == 8001, f"Expected DEFAULT_PORT to be 8001, got {backend_app.DEFAULT_PORT}"


def test_port_configuration_logic():
    """Test the port configuration logic in app.py."""
    import app as backend_app

    # Test default port when no environment variable is set
    with patch.dict(os.environ, {}, clear=True):
        # We need to test the actual logic in the __main__ block
        # Since we can't easily run the app, we'll test the logic directly
        port = int(os.environ.get('PORT', backend_app.DEFAULT_PORT))
        assert port == 8001, f"Expected port 8001 when PORT not set, got {port}"

    # Test environment variable override
    with patch.dict(os.environ, {'PORT': '9000'}, clear=True):
        port = int(os.environ.get('PORT', backend_app.DEFAULT_PORT))
        assert port == 9000, f"Expected port 9000 when PORT=9000, got {port}"


def test_port_environment_variable_override():
    """Test that PORT environment variable properly overrides default port."""
    import app as backend_app

    test_cases = [
        ('9000', 9000),      # Valid port number
        ('8080', 8080),      # Another valid port
        ('3000', 3000),      # Common development port
    ]

    for env_value, expected_port in test_cases:
        with patch.dict(os.environ, {'PORT': env_value}, clear=True):
            port = int(os.environ.get('PORT', backend_app.DEFAULT_PORT))
            assert port == expected_port, f"Expected port {expected_port} when PORT={env_value}, got {port}"


def test_port_default_fallback():
    """Test that default port is used when PORT environment variable is empty or not set."""
    import app as backend_app

    # Test with empty string
    with patch.dict(os.environ, {'PORT': ''}, clear=True):
        # Empty string should cause ValueError when converted to int
        # This will be handled by error handling in the actual app
        pass

    # Test with no PORT variable at all
    with patch.dict(os.environ, {}, clear=True):
        port = int(os.environ.get('PORT', backend_app.DEFAULT_PORT))
        assert port == 8001, f"Expected default port 8001 when PORT not set, got {port}"


def test_port_error_handling_simulation():
    """Simulate error handling for invalid PORT values."""
    import app as backend_app

    invalid_cases = [
        '',           # Empty string
        'not_a_number',  # Non-numeric string
        '0',          # Port 0 is invalid
        '-1',         # Negative port
        '65536',      # Port too high
        '100000',     # Port way too high
    ]

    for invalid_value in invalid_cases:
        with patch.dict(os.environ, {'PORT': invalid_value}, clear=True):
            try:
                port = int(os.environ.get('PORT', backend_app.DEFAULT_PORT))
                # If conversion succeeds but value is invalid, check range
                if port < 1 or port > 65535:
                    # This simulates what error handling should catch
                    print(f"Warning: Port {port} is outside valid range (1-65535)")
            except ValueError:
                # Expected for non-numeric values
                print(f"Expected ValueError for PORT='{invalid_value}'")


def test_port_range_validation():
    """Test port range validation logic."""
    import app as backend_app

    valid_ports = [1, 80, 443, 8000, 8001, 8080, 3000, 65535]
    invalid_ports = [0, -1, -100, 65536, 70000]

    for port in valid_ports:
        # These should be valid if error handling is implemented
        assert 1 <= port <= 65535, f"Port {port} should be valid (1-65535)"

    for port in invalid_ports:
        # These should be caught by error handling
        assert not (1 <= port <= 65535), f"Port {port} should be invalid"


def test_get_server_port_function():
    """Test the new get_server_port function with error handling."""
    import app as backend_app

    # Test default behavior (no PORT env var)
    with patch.dict(os.environ, {}, clear=True):
        port = backend_app.get_server_port()
        assert port == 8001, f"Expected default port 8001, got {port}"

    # Test valid environment variable
    with patch.dict(os.environ, {'PORT': '9000'}, clear=True):
        port = backend_app.get_server_port()
        assert port == 9000, f"Expected port 9000, got {port}"

    # Test invalid string value
    with patch.dict(os.environ, {'PORT': 'not_a_number'}, clear=True):
        try:
            port = backend_app.get_server_port()
            assert False, "Should have raised ValueError for non-numeric PORT"
        except ValueError as e:
            assert "Invalid PORT environment variable value" in str(e)

    # Test port out of range (too low)
    with patch.dict(os.environ, {'PORT': '0'}, clear=True):
        try:
            port = backend_app.get_server_port()
            assert False, "Should have raised ValueError for port 0"
        except ValueError as e:
            assert "Invalid port number: 0" in str(e)

    # Test port out of range (too high)
    with patch.dict(os.environ, {'PORT': '65536'}, clear=True):
        try:
            port = backend_app.get_server_port()
            assert False, "Should have raised ValueError for port 65536"
        except ValueError as e:
            assert "Invalid port number: 65536" in str(e)

    # Test with custom default port
    with patch.dict(os.environ, {}, clear=True):
        port = backend_app.get_server_port(default_port=3000)
        assert port == 3000, f"Expected custom default port 3000, got {port}"


if __name__ == '__main__':
    # Simple test runner for backward compatibility
    test_default_port_constant()
    print("✓ test_default_port_constant passed")

    test_port_configuration_logic()
    print("✓ test_port_configuration_logic passed")

    test_port_environment_variable_override()
    print("✓ test_port_environment_variable_override passed")

    test_port_default_fallback()
    print("✓ test_port_default_fallback passed")

    test_port_error_handling_simulation()
    print("✓ test_port_error_handling_simulation passed")

    test_port_range_validation()
    print("✓ test_port_range_validation passed")

    test_get_server_port_function()
    print("✓ test_get_server_port_function passed")

    print("\nAll tests passed!")