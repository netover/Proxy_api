"""Context condensation and summarization utilities."""

from typing import List, Optional, Dict, Any
import hashlib
import time
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class ContextCondenser:
    """Context condensation service for summarizing long conversations."""

    def __init__(self, max_tokens: int = 512):
        self.max_tokens = max_tokens

    async def condense(
        self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None
    ) -> str:
        """
        Condense a list of messages into a summary.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum tokens for the summary (overrides instance default)

        Returns:
            Condensed summary of the messages
        """
        target_tokens = max_tokens or self.max_tokens

        if not messages:
            return ""

        # Simple concatenation for now - can be enhanced with actual LLM summarization
        content = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in messages]
        )

        # Basic truncation if content is too long
        if (
            len(content) > target_tokens * 4
        ):  # Rough estimate: 4 chars per token
            content = content[: target_tokens * 4] + "..."

        return content

    async def condense_chunks(
        self, chunks: List[str], max_tokens: int = 512
    ) -> str:
        """
        Condense multiple text chunks into a single summary.

        Args:
            chunks: List of text chunks to condense
            max_tokens: Maximum tokens for the summary

        Returns:
            Condensed summary of all chunks
        """
        if not chunks:
            return ""

        combined = "\n\n---\n\n".join(chunks)

        # Basic truncation if content is too long
        if len(combined) > max_tokens * 4:
            combined = combined[: max_tokens * 4] + "..."

        return combined
