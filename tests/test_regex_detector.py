# tests/test_regex_detector.py
import pytest
from scanner.models import CodeChunk
from scanner.detectors import RegexDetector


@pytest.fixture
def detector():
    return RegexDetector()


def make_chunk(snippet: str, file_path: str = "test.py") -> CodeChunk:
    return CodeChunk(
        file_path=file_path,
        language="python",
        start_line=1,
        end_line=1,
        target_snippet=snippet,
    )


class TestRegexDetector:
    def test_detects_aws_key(self, detector):
        chunk = make_chunk('key = "AKIAIOSFODNN7EXAMPLE"')
        findings = detector.detect(chunk)
        assert len(findings) > 0
        assert findings[0].type == "aws_access_key"

    def test_detects_github_token(self, detector):
        chunk = make_chunk('TOKEN = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef12"')
        findings = detector.detect(chunk)
        assert any(f.type == "github_token" for f in findings)

    def test_detects_jwt(self, detector):
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        chunk = make_chunk(f'token = "{jwt}"')
        findings = detector.detect(chunk)
        assert any(f.type == "jwt_token" for f in findings)

    def test_detects_private_key(self, detector):
        chunk = make_chunk('key = "-----BEGIN RSA PRIVATE KEY-----"')
        findings = detector.detect(chunk)
        assert any(f.type == "private_key" for f in findings)

    def test_detects_eval(self, detector):
        chunk = make_chunk('result = eval(user_input)')
        findings = detector.detect(chunk)
        assert any(f.type == "eval_usage" for f in findings)

    def test_detects_shell_true(self, detector):
        chunk = make_chunk('subprocess.run(cmd, shell=True)')
        findings = detector.detect(chunk)
        assert any(f.type == "shell_true" for f in findings)

    def test_detects_sql_concat(self, detector):
        chunk = make_chunk('query = "SELECT * FROM users WHERE id = " + user_id')
        findings = detector.detect(chunk)
        assert any(f.type == "sql_concat" for f in findings)

    def test_detects_md5(self, detector):
        chunk = make_chunk('h = hashlib.md5(password.encode())')
        findings = detector.detect(chunk)
        assert any(f.type == "weak_hash_md5" for f in findings)

    def test_ignores_commented_eval(self, detector):
        chunk = make_chunk('# result = eval(user_input)')
        findings = detector.detect(chunk)
        assert not any(f.type == "eval_usage" for f in findings)

    def test_no_false_positive_on_safe_code(self, detector):
        chunk = make_chunk('x = 2 + 2')
        findings = detector.detect(chunk)
        assert len(findings) == 0