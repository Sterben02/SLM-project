# scanner/llm/slm_detector.py
"""
SLM-детектор: Qwen2.5-Coder-1.5B-Instruct + обученные LoRA-адаптеры.
"""
import json
import re
from typing import List

import torch

from scanner.models import CodeChunk, Finding, DetectorType, Severity
from scanner.detectors.base import BaseDetector

INSTRUCTION = (
    "Ты — эксперт по безопасности кода. Проанализируй фрагмент кода и определи:\n"
    "1. Содержит ли он секрет (API-ключ, токен, пароль, приватный ключ, JWT).\n"
    "2. Содержит ли он небезопасный паттерн (eval, exec, shell=True, "
    "SQL-конкатенация, слабый хэш, захардкоженные учётные данные).\n\n"
    "Ответь строго в формате JSON:\n"
    '{"is_secret": bool, "secret_type": str|null, "is_insecure": bool, '
    '"insecure_type": str|null, "confidence": float, "explanation": str}'
)

DEFAULT_ADAPTER_PATH = "models_cache/qwen-secret-scanner-lora"
DEFAULT_BASE_MODEL = "models_cache/qwen-base"


class SLMDetector(BaseDetector):
    name = "slm"
    detector_type = DetectorType.SLM

    def __init__(
        self,
        adapter_path: str = DEFAULT_ADAPTER_PATH,
        base_model: str = DEFAULT_BASE_MODEL,
    ):
        self.adapter_path = adapter_path
        self.base_model = base_model
        self._model = None
        self._tokenizer = None
        self._device = None

    def _load(self):
        if self._model is not None:
            return

        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel

        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if self._device == "cuda" else torch.float32

        print(f"🤖 Загрузка SLM ({self._device})...")
        base = AutoModelForCausalLM.from_pretrained(
            self.base_model, torch_dtype=dtype
        )
        model = PeftModel.from_pretrained(base, self.adapter_path)
        model.eval()
        model.to(self._device)

        self._model = model
        self._tokenizer = AutoTokenizer.from_pretrained(self.adapter_path)
        print("✅ SLM загружена")

    def detect(self, chunk: CodeChunk) -> List[Finding]:
        self._load()

        input_text = (
            f"Язык: {chunk.language}\n"
            f"Файл: {chunk.file_path}\n\n"
            f"```{chunk.language}\n"
            f"{chunk.context_before}{chunk.target_snippet}\n{chunk.context_after}"
            f"```"
        )

        messages = [
            {"role": "system", "content": INSTRUCTION},
            {"role": "user", "content": input_text},
        ]
        prompt = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._device)

        with torch.no_grad():
            out = self._model.generate(
                **inputs, max_new_tokens=256, do_sample=False
            )

        text = self._tokenizer.decode(
            out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )

        parsed = self._parse_json(text)
        if parsed is None:
            return []
        return self._to_findings(chunk, parsed)

    @staticmethod
    def _parse_json(text: str) -> dict | None:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    def _to_findings(self, chunk: CodeChunk, parsed: dict) -> List[Finding]:
        findings = []
        confidence = float(parsed.get("confidence", 0.7))
        explanation = str(parsed.get("explanation", ""))

        if parsed.get("is_secret"):
            findings.append(Finding(
                file=chunk.file_path,
                line=chunk.start_line,
                type=str(parsed.get("secret_type") or "secret"),
                category="secret",
                severity=Severity.HIGH,
                confidence=confidence,
                detector=self.detector_type,
                snippet=chunk.target_snippet.strip(),
                explanation=f"[slm] {explanation}",
            ))

        if parsed.get("is_insecure"):
            findings.append(Finding(
                file=chunk.file_path,
                line=chunk.start_line,
                type=str(parsed.get("insecure_type") or "insecure_code"),
                category="insecure_code",
                severity=Severity.HIGH,
                confidence=confidence,
                detector=self.detector_type,
                snippet=chunk.target_snippet.strip(),
                explanation=f"[slm] {explanation}",
            ))

        return findings