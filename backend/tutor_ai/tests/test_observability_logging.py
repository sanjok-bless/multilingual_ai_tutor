"""Tests for structured logging configuration."""

import json
import logging
import os
import subprocess
import sys
import time
from collections.abc import Generator
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import httpx
import pytest
import structlog

from tutor_ai import observability


@pytest.fixture
def isolated_logging() -> Generator[None]:
    """Fixture to isolate logging configuration across tests."""
    original_handlers = logging.root.handlers[:]
    original_level = logging.root.level
    yield
    logging.root.handlers = original_handlers
    logging.root.level = original_level


def test_configure_logging_sets_json_output(isolated_logging: Generator[None]) -> None:
    """Test that logging outputs JSON with extra fields."""
    observability.configure_logging("INFO")

    logger = structlog.get_logger()
    output = StringIO()

    # Create formatter with JSON renderer
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler(output)
    handler.setFormatter(formatter)
    logging.root.handlers.clear()
    logging.root.addHandler(handler)

    logger.warning("Test message", session_id="test-123", language="english")

    log_output = output.getvalue()
    log_json = json.loads(log_output.strip())

    # Verify field values
    assert log_json["event"] == "Test message"
    assert log_json["severity"] == "warning"
    assert log_json["session_id"] == "test-123"
    assert log_json["language"] == "english"
    assert "ts" in log_json

    # Verify field ordering: ts and severity should be first two fields
    keys = list(log_json.keys())
    assert keys[0] == "ts", f"Expected 'ts' as first field, got '{keys[0]}'"
    assert keys[1] == "severity", f"Expected 'severity' as second field, got '{keys[1]}'"
    assert keys[2] == "event", f"Expected 'event' as third field, got '{keys[2]}'"


def test_log_level_filtering(isolated_logging: Generator[None]) -> None:
    """Test that log level filtering works correctly."""
    output = StringIO()

    with redirect_stdout(output):
        observability.configure_logging("WARNING")
        logger = structlog.get_logger()

        logger.info("This should not appear")
        logger.warning("This should appear")

    log_output = output.getvalue()
    log_lines = [line.strip() for line in log_output.strip().split("\n") if line.strip()]

    # INFO level should be filtered out (WARNING is set)
    assert len(log_lines) == 1, f"Expected 1 log line (WARNING only), got {len(log_lines)}"

    # Verify the WARNING message appears
    log_json = json.loads(log_lines[0])
    assert log_json["event"] == "This should appear"
    assert log_json["severity"] == "warning"


def test_configure_logging_prevents_duplicate_handlers(isolated_logging: Generator[None]) -> None:
    """Test that configure_logging() clears existing handlers to prevent duplicates.

    Regression test for duplicate logging bug where every log appeared twice.
    """
    output = StringIO()

    # Simulate existing handlers (like in production before configure_logging is called)
    handler1 = logging.StreamHandler(output)
    handler2 = logging.StreamHandler(output)
    logging.root.addHandler(handler1)
    logging.root.addHandler(handler2)

    # Track initial count (pytest adds some handlers)
    initial_count = len(logging.root.handlers)

    with redirect_stdout(output):
        # Configure logging - should clear old handlers and add exactly 1 new one
        observability.configure_logging("INFO")

        # Contract: configure_logging ensures exactly 1 handler, not initial_count + 1
        assert len(logging.root.handlers) == 1, (
            f"Expected exactly 1 handler after configure_logging, "
            f"but got {len(logging.root.handlers)} (started with {initial_count}). "
            f"Handlers not cleared causes duplicate logs in production."
        )

        # Verify actual log output: should produce exactly 1 log line, not duplicates
        logger = observability.get_logger()
        logger.info("Test message", request_id="test-123")

    log_output = output.getvalue()
    log_lines = [line.strip() for line in log_output.strip().split("\n") if line.strip()]

    assert len(log_lines) == 1, (
        f"Expected exactly 1 log line but got {len(log_lines)}. Multiple handlers would produce duplicate log entries."
    )

    # Verify it's valid JSON
    log_json = json.loads(log_lines[0])
    assert log_json["event"] == "Test message"
    assert log_json["severity"] == "info"
    assert log_json["request_id"] == "test-123"


@pytest.mark.slow
def test_no_duplicate_http_access_logs_real_server() -> None:
    """Reproduce bug: uvicorn.access logs duplicate our AccessLoggingMiddleware logs.

    Integration test with real uvicorn server to capture actual duplicate logging behavior.
    TestClient bypasses uvicorn, so we need real server to reproduce the bug.
    """
    # Start uvicorn server with stdout capture
    # Set cwd to project root so tutor_ai.main:app module path resolves correctly
    project_root = Path(__file__).parent.parent.parent
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "tutor_ai.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8888",
            "--log-level",
            "info",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=project_root,
        env=os.environ,
    )

    try:
        # Collect all startup logs
        startup_logs = []
        startup_timeout = 10
        start_time = time.time()
        server_ready = False

        while time.time() - start_time < startup_timeout:
            line = process.stdout.readline()
            if line:
                startup_logs.append(line.strip())
                if "Application startup complete" in line:
                    server_ready = True
                    break
            if process.poll() is not None:
                raise RuntimeError(f"Server process died during startup. Logs: {startup_logs}")
            time.sleep(0.1)

        if not server_ready:
            raise TimeoutError(f"Server did not start within timeout. Logs: {startup_logs}")

        # Make real HTTP request
        response = httpx.get("http://127.0.0.1:8888/api/v1/health", timeout=5.0)
        assert response.status_code == 200

        # Give server time to flush access logs
        time.sleep(0.2)

        # Terminate server and collect remaining logs with timeout
        process.terminate()
        try:
            stdout_data, _ = process.communicate(timeout=2)
            request_logs = stdout_data.strip().split("\n") if stdout_data else []
        except subprocess.TimeoutExpired:
            process.kill()
            stdout_data, _ = process.communicate()
            request_logs = stdout_data.strip().split("\n") if stdout_data else []

        # Combine all logs
        log_lines = startup_logs + request_logs

        # Parse JSON logs and find HTTP access logs for /api/v1/health
        http_access_logs = []
        for line in log_lines:
            if not line:
                continue
            try:
                log_json = json.loads(line)
                # Filter for HTTP access logs:
                # 1. AccessLoggingMiddleware: has "path" field
                # 2. uvicorn.access: has "/api/v1/health" in "event" field
                is_middleware_log = "path" in log_json and log_json.get("path") == "/api/v1/health"
                is_uvicorn_log = (
                    "event" in log_json and "/api/v1/health" in log_json["event"] and "GET" in log_json["event"]
                )
                if is_middleware_log or is_uvicorn_log:
                    http_access_logs.append(log_json)
            except json.JSONDecodeError:
                continue

        # Verify no duplicate access logs (regression test)
        assert len(http_access_logs) == 1, (
            f"Expected 1 access log from AccessLoggingMiddleware, got {len(http_access_logs)}. "
            f"Duplicate logs detected - uvicorn.access logger may not be disabled. Logs: {http_access_logs}"
        )

    finally:
        # Ensure cleanup
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def test_exception_logging_includes_stack_trace(isolated_logging: Generator[None]) -> None:
    """Test that exceptions from stdlib logging (FastAPI/Uvicorn) are formatted as strings."""
    output = StringIO()

    # Use redirect_stdout to capture from actual configured handler
    with redirect_stdout(output):
        observability.configure_logging("INFO")

        # Use STDLIB logging (not structlog) - this is what FastAPI/Uvicorn use
        logger = logging.getLogger("uvicorn.error")

        # Trigger exception and log it
        try:
            _ = 1 / 0
        except ZeroDivisionError:
            logger.error("Exception in ASGI application", exc_info=True)

    # Capture and parse log output
    log_output = output.getvalue()
    log_json = json.loads(log_output.strip())

    # Assert string exception format with format_exc_info
    assert "exception" in log_json, f"Expected 'exception' field with traceback, got: {list(log_json.keys())}"

    # Verify it's a string (not structured JSON)
    assert isinstance(log_json["exception"], str), (
        f"Expected exception to be a string with format_exc_info, got: {type(log_json['exception'])}"
    )

    # Verify string contains expected traceback information
    exception_str = log_json["exception"]
    assert "Traceback (most recent call last)" in exception_str, "Expected traceback header"
    assert "ZeroDivisionError" in exception_str, "Expected exception type"
    assert "division by zero" in exception_str, "Expected exception message"
    assert "test_exception_logging_includes_stack_trace" in exception_str, "Expected function name in traceback"
    assert "1 / 0" in exception_str or "1/0" in exception_str, "Expected failing line in traceback"
