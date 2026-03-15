"""xAI/Grok API client — uses the /v1/responses endpoint with tool-based web search."""

import json
import logging
import requests
from dataclasses import dataclass, field
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# xAI Grok pricing per million tokens (as of 2025)
# Update these if pricing changes
GROK_PRICING = {
    "grok-4": {"input": 3.00, "output": 15.00},
    "grok-3": {"input": 3.00, "output": 15.00},
    "grok-3-mini": {"input": 0.30, "output": 0.50},
}


@dataclass
class ApiUsage:
    """Token usage and cost from a single API call."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0


@dataclass
class GrokCallResult:
    """Result from a Grok API call including parsed data and usage."""
    data: dict | None = None
    usage: ApiUsage = field(default_factory=ApiUsage)


class GrokClient:
    """Client for the xAI Grok API with web search support."""

    API_URL = "https://api.x.ai/v1/responses"
    DEFAULT_MODEL = "grok-4"

    def __init__(self, api_key: str, model: str | None = None):
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL

    def call(self, prompt: str, apply_url: str | None = None) -> dict | None:
        """Send a prompt to Grok and return parsed JSON response.

        Args:
            prompt: The user prompt to send.
            apply_url: Optional card application URL to restrict search domain.

        Returns:
            Parsed JSON dict from the response, or None on failure.
        """
        result = self.call_with_usage(prompt, apply_url)
        return result.data

    def call_with_usage(self, prompt: str, apply_url: str | None = None) -> GrokCallResult:
        """Send a prompt to Grok and return parsed JSON response with usage/cost info.

        Returns:
            GrokCallResult with data and usage fields.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "stream": False,
            "temperature": 0.2,
            "instructions": "You are a helpful assistant that provides JSON updates for credit cards.",
            "input": prompt,
            "tools": [{"type": "web_search"}],
        }

        call_result = GrokCallResult()

        try:
            response = requests.post(self.API_URL, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()

            # Extract usage
            usage_data = result.get('usage', {})
            call_result.usage = self._compute_usage(usage_data)

            # Extract text from output array
            content = self._extract_text(result)
            if content:
                content = self._strip_markdown(content)
                call_result.data = json.loads(content)

        except Exception as e:
            logger.error("API Request Failed: %s", e)
            if 'response' in locals():
                logger.error("Response Body: %s", response.text[:500])

        return call_result

    def _extract_text(self, result: dict) -> str | None:
        """Extract text content from /v1/responses output format."""
        for output_item in result.get('output', []):
            if output_item.get('type') == 'message':
                for content_item in output_item.get('content', []):
                    if content_item.get('type') == 'output_text':
                        return content_item.get('text')
        return None

    def _compute_usage(self, usage_data: dict) -> ApiUsage:
        """Compute token usage and cost from API response."""
        prompt_tokens = usage_data.get('input_tokens', usage_data.get('prompt_tokens', 0))
        completion_tokens = usage_data.get('output_tokens', usage_data.get('completion_tokens', 0))
        total_tokens = usage_data.get('total_tokens', prompt_tokens + completion_tokens)

        pricing = GROK_PRICING.get(self.model, GROK_PRICING["grok-4"])
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return ApiUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
        )

    @staticmethod
    def _strip_markdown(content: str) -> str:
        """Remove markdown code fences from API response content."""
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return content
