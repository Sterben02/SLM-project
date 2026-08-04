# scanner/models/dataset.py
from pydantic import BaseModel, Field
from typing import Optional, Literal

SecretType = Literal[
    "api_key", "access_token", "password", "private_key", "jwt", None
]

# ДОБАВЛЕНО: insecure_code как общий класс
InsecureType = Literal[
    "eval_usage", "exec_usage", "shell_true",
    "sql_concat", "weak_hash", "hardcoded_creds",
    "insecure_code",  # ← ДОБАВИТЬ ЭТУ СТРОКУ
    None
]


class Labels(BaseModel):
    is_secret: bool
    is_insecure: bool
    secret_type: SecretType = None
    insecure_type: InsecureType = None


class Metadata(BaseModel):
    entropy: Optional[float] = None
    variable_name: Optional[str] = None
    matched_regex: Optional[str] = None
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    note: Optional[str] = None


class DatasetItem(BaseModel):
    id: str
    source: Literal["synthetic", "opensource", "manual"]
    language: Literal["python", "c", "javascript", "go", "java"]
    file_path: str
    line_number: int

    context_before: str
    target_snippet: str
    context_after: str

    labels: Labels
    metadata: Metadata = Field(default_factory=Metadata)