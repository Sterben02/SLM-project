# scanner/core/__init__.py
from .scanner import scan_path, iter_files, parse_file
from .aggregator import dedupe_findings

__all__ = ["scan_path", "iter_files", "parse_file", "dedupe_findings"]