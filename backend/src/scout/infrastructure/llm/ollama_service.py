"""
Ollama LLM Service Implementation.

This module provides the concrete implementation of ILLMService
using Ollama for local LLM inference.
"""

import json
from typing import Any

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from scout.core.config import settings
from scout.core.logging import get_logger
from scout.domain.interfaces.repositories import ILLMService

logger = get_logger(__name__)


class OllamaService(ILLMService):
    """
    Ollama-based LLM service for local inference.

    Uses ChatOllama from langchain-community for communication
    with the local Ollama server.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float = 0.1,
    ) -> None:
        """
        Initialize OllamaService.

        Args:
            base_url: Ollama server URL (default: from settings)
            model: Model name to use (default: from settings)
            temperature: Sampling temperature (lower = more deterministic)
        """
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.temperature = temperature

        self._llm = ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=self.temperature,
        )
        self._parser = StrOutputParser()

        logger.info(
            "ollama_service_initialized",
            base_url=self.base_url,
            model=self.model,
        )

    async def analyze_threat(
        self, threat_data: dict, context: str | None = None
    ) -> dict:
        """
        Analyze a potential threat using LLM.

        Args:
            threat_data: Dictionary containing threat information
            context: Optional additional context

        Returns:
            Analysis result with severity, recommendations, etc.
        """
        system_prompt = """You are Scout, an AI-powered cybersecurity analyst.
Analyze the following threat data and provide a structured assessment.

Your response MUST be valid JSON with these fields:
- severity: "critical" | "high" | "medium" | "low" | "info"
- confidence: float between 0 and 1
- threat_type: string describing the type of threat
- summary: brief description of the threat
- indicators: list of IoCs (indicators of compromise)
- recommendations: list of recommended actions
- is_false_positive: boolean indicating if likely false positive

Be concise and precise. Focus on actionable insights."""

        user_prompt = f"""Analyze this threat data:
{json.dumps(threat_data, indent=2, default=str)}
"""
        if context:
            user_prompt += f"\n\nAdditional context:\n{context}"

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = await self._llm.ainvoke(messages)
            response_text = response.content

            # Try to parse as JSON
            try:
                # Handle markdown code blocks
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()

                result = json.loads(response_text)
                logger.info("threat_analysis_completed", threat_type=result.get("threat_type"))
                return result
            except json.JSONDecodeError:
                # Return structured response even if parsing fails
                logger.warning("threat_analysis_json_parse_failed", raw_response=response_text[:200])
                return {
                    "severity": "medium",
                    "confidence": 0.5,
                    "threat_type": "unknown",
                    "summary": response_text[:500],
                    "indicators": [],
                    "recommendations": ["Manual review recommended"],
                    "is_false_positive": False,
                    "raw_response": response_text,
                }

        except Exception as e:
            logger.error("threat_analysis_failed", error=str(e))
            raise

    async def summarize_activity(
        self, events: list[dict], timeframe: str
    ) -> str:
        """
        Generate a human-readable summary of security events.

        Args:
            events: List of security event dictionaries
            timeframe: Description of the time period

        Returns:
            Human-readable summary string
        """
        system_prompt = """You are Scout, an AI cybersecurity analyst.
Summarize the following security events concisely.
Focus on:
- Key patterns and anomalies
- Most critical events
- Overall security posture
Keep the summary under 300 words."""

        user_prompt = f"""Summarize these security events from {timeframe}:

{json.dumps(events, indent=2, default=str)}"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = await self._llm.ainvoke(messages)
            summary = response.content

            logger.info("activity_summary_generated", event_count=len(events))
            return summary

        except Exception as e:
            logger.error("activity_summary_failed", error=str(e))
            raise

    async def generate_response_plan(
        self, threat_type: str, severity: str
    ) -> list[str]:
        """
        Generate a list of recommended response actions.

        Args:
            threat_type: Type of threat detected
            severity: Severity level of the threat

        Returns:
            List of recommended response actions
        """
        system_prompt = """You are Scout, an AI cybersecurity analyst.
Generate a step-by-step incident response plan.
Each step should be:
- Specific and actionable
- Prioritized by urgency
- Include both immediate and follow-up actions

Return ONLY a JSON array of strings, each string being one action step.
Example: ["Isolate affected system", "Capture memory dump", ...]"""

        user_prompt = f"""Generate an incident response plan for:
- Threat Type: {threat_type}
- Severity: {severity}

Provide 5-10 specific action steps."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = await self._llm.ainvoke(messages)
            response_text = response.content

            # Try to parse as JSON array
            try:
                # Handle markdown code blocks
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()

                steps = json.loads(response_text)
                if isinstance(steps, list):
                    logger.info("response_plan_generated", step_count=len(steps))
                    return steps
            except json.JSONDecodeError:
                pass

            # Fallback: split by newlines if JSON parsing fails
            lines = [
                line.strip().lstrip("0123456789.-) ")
                for line in response_text.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]
            logger.info("response_plan_generated_fallback", step_count=len(lines))
            return lines[:10]  # Limit to 10 steps

        except Exception as e:
            logger.error("response_plan_failed", error=str(e))
            raise

    async def chat(self, message: str, system_prompt: str | None = None) -> str:
        """
        Simple chat interface for general queries.

        Args:
            message: User message
            system_prompt: Optional system prompt override

        Returns:
            LLM response string
        """
        default_system = """You are Scout, an AI-powered cybersecurity assistant.
You help security analysts with threat detection, incident response,
and security best practices. Be concise and technical."""

        try:
            messages = [
                SystemMessage(content=system_prompt or default_system),
                HumanMessage(content=message),
            ]

            response = await self._llm.ainvoke(messages)
            return response.content

        except Exception as e:
            logger.error("chat_failed", error=str(e))
            raise

    async def analyze_logs(self, logs: str, query: str) -> dict[str, Any]:
        """
        Analyze log data for anomalies or specific patterns.

        Args:
            logs: Raw log data as string
            query: What to look for in the logs

        Returns:
            Analysis result dictionary
        """
        system_prompt = """You are Scout, an AI log analyst specializing in security.
Analyze the provided logs and answer the user's query.

Your response MUST be valid JSON with:
- findings: list of discovered items/anomalies
- severity: "critical" | "high" | "medium" | "low" | "info"
- summary: brief summary of findings
- indicators: list of suspicious IPs, domains, or patterns found
- recommendation: what action to take"""

        user_prompt = f"""Query: {query}

Logs to analyze:
{logs[:8000]}"""  # Limit log size for context window

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = await self._llm.ainvoke(messages)
            response_text = response.content

            # Parse JSON response
            try:
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()

                result = json.loads(response_text)
                logger.info("log_analysis_completed")
                return result
            except json.JSONDecodeError:
                return {
                    "findings": [],
                    "severity": "info",
                    "summary": response_text[:500],
                    "indicators": [],
                    "recommendation": "Manual review recommended",
                    "raw_response": response_text,
                }

        except Exception as e:
            logger.error("log_analysis_failed", error=str(e))
            raise

    def health_check(self) -> dict[str, Any]:
        """
        Check if Ollama service is available.

        Returns:
            Health status dictionary
        """
        import httpx

        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                return {
                    "status": "healthy",
                    "base_url": self.base_url,
                    "configured_model": self.model,
                    "available_models": models,
                    "model_available": self.model in models or any(
                        self.model in m for m in models
                    ),
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                }
        except Exception as e:
            return {
                "status": "unavailable",
                "error": str(e),
                "hint": "Is Ollama running? Start with: ollama serve",
            }
