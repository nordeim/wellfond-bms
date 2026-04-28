"""SSE Async/Sync Handling Tests

Tests for validating that SSE streams use proper Django async patterns.
Ensures database connection handling is consistent across all SSE endpoints.

TDD Phase 2: Write failing test before implementation.
"""

import pytest
import asyncio
import inspect
from unittest.mock import patch, MagicMock, AsyncMock

from apps.operations.routers.stream import (
    _generate_alert_stream,
    _generate_dog_alert_stream,
)


class TestSSEAsyncHandling:
    """Test that SSE streams use sync_to_async with thread_sensitive=True."""

    @patch('apps.operations.routers.stream.get_pending_alerts')
    @patch('apps.operations.routers.stream.asyncio')
    async def test_alert_stream_uses_sync_to_async(self, mock_asyncio, mock_get_pending_alerts):
        """
        Verify _generate_alert_stream uses sync_to_async, not asyncio.to_thread.
        
        The stream.py file has two async generators:
        - _generate_alert_stream: Should use sync_to_async(thread_sensitive=True)
        - _generate_dog_alert_stream: Should also use sync_to_async(thread_sensitive=True)
        
        This test verifies they both use the correct pattern.
        """
        # Setup mock to return empty alerts
        mock_get_pending_alerts.return_value = []
        
        # Mock sync_to_async to capture calls
        with patch('apps.operations.routers.stream.sync_to_async') as mock_sync_to_async:
            # Setup sync_to_async to return an async function
            async def mock_wrapped(*args, **kwargs):
                return []
            
            mock_sync_to_async.return_value = mock_wrapped
            
            # Start the generator
            gen = _generate_alert_stream(
                user_id="test-user-id",
                entity_id="test-entity-id",
                user_role="admin"
            )
            
            # Try to get first result (will timeout)
            try:
                await asyncio.wait_for(gen.__anext__(), timeout=0.1)
            except (asyncio.TimeoutError, StopAsyncIteration):
                pass
            
            # Verify sync_to_async was called with thread_sensitive=True
            mock_sync_to_async.assert_called()
            call_kwargs = mock_sync_to_async.call_args[1] if mock_sync_to_async.call_args else {}
            
            # Check thread_sensitive is True
            assert call_kwargs.get('thread_sensitive') is True, (
                "_generate_alert_stream must use sync_to_async(thread_sensitive=True) "
                "for proper Django database connection handling"
            )

    @patch('apps.operations.routers.stream.get_pending_alerts')
    async def test_dog_alert_stream_uses_sync_to_async(self, mock_get_pending_alerts):
        """
        Verify _generate_dog_alert_stream uses sync_to_async, not asyncio.to_thread.
        
        This is the CRITICAL fix - the dog alert stream currently uses asyncio.to_thread()
        which doesn't properly handle Django database connections.
        """
        # Setup mock
        mock_get_pending_alerts.return_value = []
        
        # Mock both patterns to track usage
        with patch('apps.operations.routers.stream.sync_to_async') as mock_sync_to_async:
            with patch.object(asyncio, 'to_thread') as mock_to_thread:
                # Setup sync_to_async to return async function
                async def mock_wrapped(*args, **kwargs):
                    return []
                mock_sync_to_async.return_value = mock_wrapped
                
                # Start the generator
                gen = _generate_dog_alert_stream(
                    dog_id="test-dog-id",
                    user_id="test-user-id",
                    entity_id="test-entity-id",
                    user_role="admin"
                )
                
                # Try to get first result
                try:
                    await asyncio.wait_for(gen.__anext__(), timeout=0.1)
                except (asyncio.TimeoutError, StopAsyncIteration):
                    pass
                
                # CRITICAL: sync_to_async should be called, asyncio.to_thread should NOT
                assert mock_sync_to_async.called, (
                    "_generate_dog_alert_stream must use sync_to_async for database operations"
                )
                
                # Verify thread_sensitive=True
                call_kwargs = mock_sync_to_async.call_args[1] if mock_sync_to_async.call_args else {}
                assert call_kwargs.get('thread_sensitive') is True, (
                    "sync_to_async must be called with thread_sensitive=True"
                )
                
                # asyncio.to_thread should NOT be called (this is the bug)
                assert not mock_to_thread.called, (
                    "_generate_dog_alert_stream incorrectly uses asyncio.to_thread(). "
                    "Must use sync_to_async(thread_sensitive=True) instead for Django ORM"
                )

    def test_source_code_uses_correct_pattern(self):
        """
        Verify the source code uses sync_to_async, not asyncio.to_thread.
        
        This is a static analysis test to catch the pattern mismatch.
        """
        import ast
        import inspect
        
        # Get source of _generate_dog_alert_stream
        source = inspect.getsource(_generate_dog_alert_stream)
        
        # Parse AST
        tree = ast.parse(source)
        
        # Find all await expressions
        for node in ast.walk(tree):
            if isinstance(node, ast.Await):
                # Check if awaiting asyncio.to_thread
                if isinstance(node.value, ast.Call):
                    func = node.value.func
                    if isinstance(func, ast.Attribute):
                        # Check for asyncio.to_thread
                        if func.attr == 'to_thread':
                            raise AssertionError(
                                "CRITICAL BUG: _generate_dog_alert_stream uses asyncio.to_thread() "
                                "which does NOT properly handle Django database connections. "
                                "Must use sync_to_async(get_pending_alerts, thread_sensitive=True) instead."
                            )

    def test_both_streams_use_same_pattern(self):
        """Verify both alert streams use the same database access pattern."""
        import ast
        import inspect
        
        # Get source of both functions
        alert_source = inspect.getsource(_generate_alert_stream)
        dog_alert_source = inspect.getsource(_generate_dog_alert_stream)
        
        # Check _generate_alert_stream uses sync_to_async (correct)
        if 'sync_to_async' not in alert_source:
            raise AssertionError("_generate_alert_stream should use sync_to_async")
        
        # Check _generate_dog_alert_stream also uses sync_to_async
        # (it may have comments mentioning asyncio.to_thread which is OK)
        if 'sync_to_async(get_pending_alerts' not in dog_alert_source:
            raise AssertionError(
                "INCONSISTENCY: _generate_dog_alert_stream must call sync_to_async(get_pending_alerts) "
                "like _generate_alert_stream does. Both must use sync_to_async(thread_sensitive=True) "
                "for consistent database connection handling."
            )
        
        # Both should use sync_to_async
        assert 'sync_to_async' in dog_alert_source, (
            "_generate_dog_alert_stream must use sync_to_async like _generate_alert_stream"
        )
