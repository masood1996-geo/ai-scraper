"""
LLM Provider abstraction — supports OpenRouter, OpenAI, and any OpenAI-compatible API.

Sends cleaned HTML/text to an LLM and gets structured JSON back.
"""

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Provider endpoint registry
PROVIDERS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "google/gemini-2.5-flash",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
    },
    "kilo": {
        "base_url": "https://api.kilo.ai/api/gateway",
        "default_model": "claude-sonnet-4-5",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama3.1",
    },
}


class LLMClient:
    """
    Unified LLM client for structured data extraction.

    Wraps the OpenAI SDK and routes to different providers
    based on configuration.
    """

    def __init__(
        self,
        provider: str = "openrouter",
        api_key: str = "",
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ):
        self.provider = provider.lower()
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens

        provider_config = PROVIDERS.get(self.provider, {})
        self.base_url = provider_config.get("base_url")
        self.model = model or provider_config.get("default_model", "gpt-4o-mini")

        # Initialize OpenAI-compatible client
        import openai
        self._client = openai.OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        logger.info("LLM client ready: %s / %s", self.provider, self.model)

    def extract(
        self,
        text: str,
        schema: Dict[str, Any],
        instructions: str = "",
    ) -> List[Dict]:
        """
        Send text to LLM and extract structured data matching the schema.

        Args:
            text: Raw text or HTML content to process.
            schema: Dict describing the fields to extract.
                     Example: {"title": "str", "price": "str", "url": "str"}
            instructions: Optional extra instructions for the LLM.

        Returns:
            List of dicts matching the schema.
        """
        schema_desc = json.dumps(schema, indent=2)

        system_prompt = (
            "You are a precise data extraction engine. "
            "Extract structured data from the provided content. "
            "Output ONLY a valid JSON array of objects matching the schema below. "
            "No markdown formatting, no explanation, no commentary — just the raw JSON array.\n\n"
            f"Schema (extract these fields for each item found):\n{schema_desc}"
        )

        if instructions:
            system_prompt += f"\n\nAdditional instructions:\n{instructions}"

        # Truncate content to avoid token limit issues
        max_chars = 50_000
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.warning("Content truncated to %d characters", max_chars)

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            raw_output = response.choices[0].message.content.strip()

            # Clean common LLM output artifacts
            for prefix in ["```json", "```"]:
                if raw_output.startswith(prefix):
                    raw_output = raw_output[len(prefix):]
            if raw_output.endswith("```"):
                raw_output = raw_output[:-3]
            raw_output = raw_output.strip()

            result = json.loads(raw_output)

            if isinstance(result, dict):
                result = [result]
            if not isinstance(result, list):
                logger.warning("LLM returned unexpected type: %s", type(result))
                return []

            logger.info("Extracted %d items from LLM response", len(result))
            return result

        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM JSON output: %s", e)
            logger.debug("Raw output was: %s", raw_output[:500] if 'raw_output' in dir() else "N/A")
            return []

        except Exception as e:
            logger.error("LLM extraction failed: %s", e)
            return []

    def ask(self, question: str) -> str:
        """
        Simple Q&A — ask the LLM a question and get a text response.

        Args:
            question: The question to ask.

        Returns:
            Text response from the LLM.
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": question}],
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("LLM query failed: %s", e)
            return f"Error: {e}"
