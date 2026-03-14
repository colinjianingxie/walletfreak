"""xAI/Grok API client — extracted from update_cards_grok.py."""

import json
import logging
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class GrokClient:
    """Client for the xAI Grok API with web search support."""

    API_URL = "https://api.x.ai/v1/chat/completions"
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
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        sources = self._build_search_sources(apply_url)

        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides JSON updates for credit cards.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "model": self.model,
            "stream": False,
            "temperature": 0.2,
            "search_parameters": {
                "mode": "on",
                "sources": sources,
                "return_citations": False,
                "max_search_results": 10,
            },
        }

        try:
            response = requests.post(self.API_URL, headers=headers, json=data)
            if response.status_code == 404:
                logger.error("API 404 Not Found. URL: %s", self.API_URL)
            response.raise_for_status()

            result = response.json()
            content = result['choices'][0]['message']['content']

            # Strip markdown code fences
            content = self._strip_markdown(content)
            return json.loads(content)

        except Exception as e:
            logger.error("API Request Failed: %s", e)
            if 'response' in locals():
                logger.error("Response Body: %s", response.text)
            return None

    @staticmethod
    def _build_search_sources(apply_url: str | None) -> list[dict]:
        """Build search source configuration from an application URL."""
        if not apply_url:
            return [{"type": "web"}]

        try:
            parsed = urlparse(apply_url)
            domain = parsed.netloc
            if domain.startswith("www."):
                domain = domain[4:]
            if domain:
                return [{"type": "web", "country": "US", "allowed_websites": [domain]}]
        except Exception:
            pass

        return [{"type": "web"}]

    @staticmethod
    def _strip_markdown(content: str) -> str:
        """Remove markdown code fences from API response content."""
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return content
