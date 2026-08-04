# tests/test_entropy_detector.py
import pytest
from scanner.models import CodeChunk
from scanner.detectors import EntropyDetector
from scanner.utils.entropy import shannon_entropy


@pytest.fixture
def detector():
    return EntropyDetector()


def make_chunk(snippet: str) -> CodeChunk:
    return CodeChunk(
        file_path="test.py", language="python",
        start_line=1, end_line=1, target_snippet=snippet,
    )


class TestEntropy:
    def test_low_entropy_for_repeated(self):
        assert shannon_entropy("aaaa") == 0.0

    def test_high_entropy_for_random(self):
        assert shannon_entropy("a8f5f167f44f4964e6c998dee827110c") > 3.5

    def test_detects_high_entropy_key(self, detector):
        chunk = make_chunk('API_KEY = "a8f5f167f44f4964e6c998dee827110c4b3f5a1d"')
        findings = detector.detect(chunk)
        assert len(findings) > 0

    def test_ignores_test_values(self, detector):
        chunk = make_chunk('API_KEY = "test_key_example_dummy_value"')
        findings = detector.detect(chunk)
        assert len(findings) == 0

    def test_ignores_comments(self, detector):
        chunk = make_chunk('# API_KEY = "a8f5f167f44f4964e6c998dee827110c"')
        findings = detector.detect(chunk)
        assert len(findings) == 0