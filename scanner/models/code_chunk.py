# scanner/models/code_chunk.py
from pydantic import BaseModel


class CodeChunk(BaseModel):
    """Фрагмент кода для анализа."""
    file_path: str
    language: str
    start_line: int
    end_line: int
    target_snippet: str
    context_before: str = ""
    context_after: str = ""

    @property
    def full_text(self) -> str:
        """Полный текст с контекстом (для SLM)."""
        return f"{self.context_before}{self.target_snippet}{self.context_after}"