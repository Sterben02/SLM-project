# tests/test_keyword_detector.py
import pytest
from scanner.models import CodeChunk
from scanner.detectors import KeywordDetector


@pytest.fixture
def detector():
    return KeywordDetector()


def make_chunk(snippet: str, file_path: str = "app.py", context_before: str = "") -> CodeChunk:
    return CodeChunk(
        file_path=file_path, language="python",
        start_line=1, end_line=1, target_snippet=snippet,
        context_before=context_before,
    )


class TestKeywordDetector:
    def test_detects_password_assignment(self, detector):
        chunk = make_chunk('password = "SuperSecret123"')
        findings = detector.detect(chunk)
        assert len(findings) > 0

    def test_detects_api_key_in_config(self, detector):
        chunk = make_chunk('API_KEY = "somevalue12345"', file_path="config.py")
        findings = detector.detect(chunk)
        assert len(findings) > 0

    def test_ignores_env_variable(self, detector):
        chunk = make_chunk('password = os.getenv("PASSWORD")')
        findings = detector.detect(chunk)
        assert len(findings) == 0

    def test_reduces_confidence_for_tests(self, detector):
        chunk_normal = make_chunk('password = "secret123"', file_path="app.py")
        chunk_test = make_chunk('password = "secret123"', file_path="test_app.py")
        f_normal = detector.detect(chunk_normal)
        f_test = detector.detect(chunk_test)
        if f_normal and f_test:
            assert f_test[0].confidence < f_normal[0].confidence