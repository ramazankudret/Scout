"""
LLM Guard - Input/Output Güvenlik Katmanı
Prompt injection, data leakage ve diğer LLM saldırılarına karşı koruma
"""

import re
from typing import Tuple, List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from scout.core.logger import get_logger
from scout.core.exceptions import PromptInjectionDetected

logger = get_logger(__name__)


class ThreatLevel(str, Enum):
    """Threat severity levels"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ScanResult:
    """Result of a security scan"""
    is_safe: bool
    threat_level: ThreatLevel
    threats_found: List[str]
    sanitized_content: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class InputSanitizer:
    """
    Sanitizes and validates LLM inputs to prevent prompt injection attacks.
    """
    
    # Known prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?)",
        r"disregard\s+(all\s+)?(previous|above|prior)",
        r"forget\s+(everything|all)",
        r"you\s+are\s+now\s+(a|an|in)\s+\w+\s+mode",
        r"pretend\s+(you\s+are|to\s+be)",
        r"act\s+as\s+(if|a|an)",
        r"dev(eloper)?\s+mode",
        r"DAN\s+mode",
        r"jailbreak",
        r"bypass\s+(the\s+)?(restrictions?|filters?|rules?)",
        r"system\s*:\s*",  # Fake system messages
        r"<\|.*?\|>",  # Token manipulation
        r"\[INST\]",  # Instruction tags
        r"###\s*instruction",
    ]
    
    # Sensitive data patterns (for output filtering)
    SENSITIVE_PATTERNS = [
        r"api[_\s]?key[:\s]*[a-zA-Z0-9_\-]{20,}",
        r"password[:\s]*\S+",
        r"secret[:\s]*\S+",
        r"token[:\s]*[a-zA-Z0-9_\-]{20,}",
        r"-----BEGIN\s+\w+\s+KEY-----",
    ]
    
    def __init__(self):
        self._compiled_injection = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]
        self._compiled_sensitive = [re.compile(p, re.IGNORECASE) for p in self.SENSITIVE_PATTERNS]
    
    def scan_input(self, text: str) -> ScanResult:
        """
        Scan input text for potential prompt injection attacks.
        """
        threats = []
        
        for i, pattern in enumerate(self._compiled_injection):
            if pattern.search(text):
                threats.append(f"injection_pattern_{i}")
        
        # Check for unusual character sequences
        if self._has_unusual_encoding(text):
            threats.append("unusual_encoding")
        
        # Check for excessive special characters
        if self._has_excessive_special_chars(text):
            threats.append("excessive_special_chars")
        
        # Determine threat level
        if not threats:
            threat_level = ThreatLevel.SAFE
        elif len(threats) == 1:
            threat_level = ThreatLevel.MEDIUM
        else:
            threat_level = ThreatLevel.HIGH
        
        is_safe = threat_level == ThreatLevel.SAFE
        
        if not is_safe:
            logger.warning("Potential prompt injection detected", threats=threats, input_preview=text[:100])
        
        return ScanResult(
            is_safe=is_safe,
            threat_level=threat_level,
            threats_found=threats,
            sanitized_content=self._sanitize(text) if not is_safe else text
        )
    
    def scan_output(self, text: str) -> ScanResult:
        """
        Scan LLM output for potential data leakage.
        """
        threats = []
        
        for i, pattern in enumerate(self._compiled_sensitive):
            if pattern.search(text):
                threats.append(f"sensitive_data_{i}")
        
        if not threats:
            return ScanResult(is_safe=True, threat_level=ThreatLevel.SAFE, threats_found=[])
        
        logger.warning("Potential data leakage detected in LLM output", threats=threats)
        
        return ScanResult(
            is_safe=False,
            threat_level=ThreatLevel.HIGH,
            threats_found=threats,
            sanitized_content=self._redact_sensitive(text)
        )
    
    def _sanitize(self, text: str) -> str:
        """Remove or neutralize potentially dangerous content"""
        sanitized = text
        for pattern in self._compiled_injection:
            sanitized = pattern.sub("[BLOCKED]", sanitized)
        return sanitized
    
    def _redact_sensitive(self, text: str) -> str:
        """Redact sensitive information from output"""
        redacted = text
        for pattern in self._compiled_sensitive:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted
    
    def _has_unusual_encoding(self, text: str) -> bool:
        """Check for unusual Unicode or encoding tricks"""
        # Check for zero-width characters
        zero_width = ['\u200b', '\u200c', '\u200d', '\ufeff']
        return any(c in text for c in zero_width)
    
    def _has_excessive_special_chars(self, text: str) -> bool:
        """Check for excessive special characters that might be used for obfuscation"""
        special_count = sum(1 for c in text if not c.isalnum() and not c.isspace())
        return special_count > len(text) * 0.3 if text else False


class LLMGuard:
    """
    Main LLM Guard class - orchestrates input/output security.
    """
    
    def __init__(self):
        self.sanitizer = InputSanitizer()
        self._scan_history: List[Dict[str, Any]] = []
    
    def guard_input(self, text: str, raise_on_threat: bool = True) -> Tuple[str, ScanResult]:
        """
        Guard an input before sending to LLM.
        Returns (processed_text, scan_result)
        """
        result = self.sanitizer.scan_input(text)
        
        # Store for history
        self._scan_history.append({
            "type": "input",
            "result": result,
            "preview": text[:50]
        })
        
        if not result.is_safe and raise_on_threat:
            raise PromptInjectionDetected(text)
        
        return result.sanitized_content or text, result
    
    def guard_output(self, text: str) -> Tuple[str, ScanResult]:
        """
        Guard LLM output before returning to user.
        Returns (processed_text, scan_result)
        """
        result = self.sanitizer.scan_output(text)
        
        self._scan_history.append({
            "type": "output",
            "result": result,
            "preview": text[:50]
        })
        
        return result.sanitized_content or text, result
    
    def get_scan_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent scan history for UI display"""
        return self._scan_history[-limit:]


# Global LLM Guard instance
llm_guard = LLMGuard()
