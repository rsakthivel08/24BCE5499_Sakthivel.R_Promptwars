"""
tests/test_extraction.py
─────────────────────────
Unit tests for document extraction and text cleaning.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.extraction.text_cleaner import clean_text


class TestTextCleaner:
    def test_clean_text_removes_control_chars(self):
        raw = "Hello\x00World\x01Test"
        result = clean_text(raw)
        assert "\x00" not in result
        assert "Hello" in result
        assert "World" in result

    def test_clean_text_collapses_blank_lines(self):
        raw = "Line 1\n\n\n\n\nLine 2"
        result = clean_text(raw)
        # Should have at most 2 consecutive blank lines
        assert "\n\n\n\n" not in result
        assert "Line 1" in result
        assert "Line 2" in result

    def test_clean_text_truncates(self):
        raw = "A" * 20000
        result = clean_text(raw, max_chars=100)
        assert len(result) <= 200  # 100 chars + truncation notice
        assert "truncated" in result

    def test_clean_text_strips_line_whitespace(self):
        raw = "  hello world  \n  foo bar  "
        result = clean_text(raw)
        lines = result.strip().split("\n")
        for line in lines:
            if line:
                assert line == line.strip()

    def test_clean_text_preserves_newlines(self):
        raw = "Line 1\nLine 2\nLine 3"
        result = clean_text(raw)
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result


class TestDocumentParser:
    def test_unsupported_extension_raises(self):
        from app.extraction.document_parser import extract_text
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text(Path("file.xyz"))

    def test_txt_extraction(self, tmp_path):
        from app.extraction.document_parser import extract_text
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello World\nThis is a test.", encoding="utf-8")
        result = extract_text(txt_file)
        assert "Hello World" in result
        assert "This is a test." in result
