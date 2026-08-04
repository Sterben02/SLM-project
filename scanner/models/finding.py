# scanner/models/finding.py
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectorType(str, Enum):
    REGEX = "regex"
    ENTROPY = "entropy"
    KEYWORD = "keyword"
    SLM = "slm"
    AGGREGATED = "aggregated"


class Finding(BaseModel):
    """Результат срабатывания детектора."""
    file: str
    line: int
    type: str
    category: str  # "secret" или "insecure_code"
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    detector: DetectorType
    snippet: str
    explanation: str
    metadata: Optional[dict] = None