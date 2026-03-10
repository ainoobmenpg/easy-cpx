"""
Tests for CI-ScriptScan
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add scripts to path - go up to root then into scripts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "ci-script-scan"))

from scan import (
    compile_patterns,
    is_excluded,
    load_config,
    scan_directory,
    scan_file,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "version": "1.0.0",
        "patterns": {
            "simplified_chinese": [
                "[一-龥]",
                "[㐀-䶿]",
            ],
            "mixed_chinese_english": [
                "[a-zA-Z]+[一-龥]+",
                "[一-龥]+[a-zA-Z]+",
            ],
        },
        "excluded_paths": [
            "node_modules/",
            ".git/",
            "__pycache__/",
        ],
        "excluded_files": [
            "package-lock.json",
        ],
    }


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_config(self, temp_dir):
        """Test loading a valid config file."""
        config_path = os.path.join(temp_dir, "config.json")
        config_data = {
            "patterns": {
                "simplified_chinese": ["[一-龥]"],
                "mixed_chinese_english": ["[a-zA-Z]+[一-龥]+"],
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        result = load_config(config_path)
        assert result == config_data

    def test_load_nonexistent_config(self):
        """Test loading a non-existent config file."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.json")


class TestCompilePatterns:
    """Tests for compile_patterns function."""

    def test_compile_patterns(self, sample_config):
        """Test compiling regex patterns."""
        simplified, mixed = compile_patterns(sample_config)

        assert len(simplified) == 2
        assert len(mixed) == 2

    def test_pattern_matches_simplified_chinese(self, sample_config):
        """Test that patterns match simplified Chinese characters."""
        simplified, _ = compile_patterns(sample_config)

        test_cases = ["中", "国", "人", "简", "体"]
        for char in test_cases:
            matched = any(p.search(char) for p in simplified)
            assert matched, f"Expected '{char}' to match simplified Chinese pattern"

    def test_pattern_matches_mixed_language(self, sample_config):
        """Test that patterns match mixed Chinese-English."""
        _, mixed = compile_patterns(sample_config)

        test_cases = ["test中", "中test", "hello国", "中文english"]
        for text in test_cases:
            matched = any(p.search(text) for p in mixed)
            assert matched, f"Expected '{text}' to match mixed pattern"


class TestIsExcluded:
    """Tests for is_excluded function."""

    def test_excluded_file(self, sample_config):
        """Test that excluded files are detected."""
        assert is_excluded("package-lock.json", sample_config) is True

    def test_excluded_path(self, sample_config):
        """Test that excluded paths are detected."""
        assert is_excluded("node_modules/package.json", sample_config) is True
        assert is_excluded(".git/config", sample_config) is True

    def test_not_excluded(self, sample_config):
        """Test that non-excluded files are not filtered."""
        assert is_excluded("src/app.py", sample_config) is False
        assert is_excluded("docs/readme.md", sample_config) is False


class TestScanFile:
    """Tests for scan_file function."""

    def test_scan_file_with_simplified_chinese(self, sample_config):
        """Test scanning a file with simplified Chinese."""
        simplified, mixed = compile_patterns(sample_config)

        # Create a temporary test file with simplified Chinese
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("这是一个测试\n")
            f.write("简体字检测\n")
            temp_path = f.name

        try:
            issues = scan_file(temp_path, simplified, mixed)

            assert len(issues) > 0
            assert any(i["type"] == "simplified_chinese" for i in issues)
        finally:
            os.unlink(temp_path)

    def test_scan_file_with_mixed_language(self, sample_config):
        """Test scanning a file with mixed Chinese-English."""
        simplified, mixed = compile_patterns(sample_config)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("hello中文test\n")
            f.write("测试english\n")
            temp_path = f.name

        try:
            issues = scan_file(temp_path, simplified, mixed)

            assert len(issues) > 0
            assert any(i["type"] == "mixed_chinese_english" for i in issues)
        finally:
            os.unlink(temp_path)

    def test_scan_clean_file(self, sample_config):
        """Test scanning a clean file with no issues."""
        simplified, mixed = compile_patterns(sample_config)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("This is a clean English text.\n")
            f.write("Just normal code here.\n")
            temp_path = f.name

        try:
            issues = scan_file(temp_path, simplified, mixed)

            assert len(issues) == 0
        finally:
            os.unlink(temp_path)

    def test_scan_file_returns_line_numbers(self, sample_config):
        """Test that line numbers are correctly reported."""
        simplified, mixed = compile_patterns(sample_config)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("Line 1\n")
            f.write("中文在第二行\n")
            f.write("Line 3\n")
            temp_path = f.name

        try:
            issues = scan_file(temp_path, simplified, mixed)

            assert any(i["line"] == 2 for i in issues)
        finally:
            os.unlink(temp_path)


class TestScanDirectory:
    """Tests for scan_directory function."""

    def test_scan_directory_recursive(self, sample_config, temp_dir):
        """Test scanning a directory recursively."""
        simplified, mixed = compile_patterns(sample_config)

        # Create test files
        os.makedirs(os.path.join(temp_dir, "src"))
        os.makedirs(os.path.join(temp_dir, "docs"))

        with open(os.path.join(temp_dir, "src", "main.py"), "w", encoding="utf-8") as f:
            f.write("中文注释\n")

        with open(os.path.join(temp_dir, "docs", "readme.md"), "w", encoding="utf-8") as f:
            f.write("说明文档\n")

        issues = scan_directory(temp_dir, simplified, mixed, sample_config)

        assert len(issues) > 0
        files_with_issues = {i["file"] for i in issues}
        assert any("src/main.py" in f for f in files_with_issues)

    def test_excludes_excluded_paths(self, sample_config, temp_dir):
        """Test that excluded paths are not scanned."""
        simplified, mixed = compile_patterns(sample_config)

        # Create files in excluded paths
        os.makedirs(os.path.join(temp_dir, "node_modules", "package"))
        with open(
            os.path.join(temp_dir, "node_modules", "package", "index.js"), "w", encoding="utf-8"
        ) as f:
            f.write("中文\n")

        with open(os.path.join(temp_dir, "main.js"), "w", encoding="utf-8") as f:
            f.write("中文\n")

        issues = scan_directory(temp_dir, simplified, mixed, sample_config)

        # Only the non-excluded file should have issues
        files_with_issues = {i["file"] for i in issues}
        assert not any("node_modules" in f for f in files_with_issues)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
