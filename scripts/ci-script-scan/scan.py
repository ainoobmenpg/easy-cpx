#!/usr/bin/env python3
"""
CI-ScriptScan: Simplified Chinese and mixed language pattern detector
Detects Simplified Chinese characters and Chinese-English mixed patterns in code/text files.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def load_config(config_path: str) -> dict[str, Any]:
    """Load configuration from JSON file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compile_patterns(config: dict[str, Any]) -> tuple[list[re.Pattern], list[re.Pattern]]:
    """Compile regex patterns from config."""
    simplified_patterns = [
        re.compile(p) for p in config["patterns"].get("simplified_chinese", [])
    ]
    mixed_patterns = [
        re.compile(p) for p in config["patterns"].get("mixed_chinese_english", [])
    ]
    return simplified_patterns, mixed_patterns


def is_excluded(path: str, config: dict[str, Any]) -> bool:
    """Check if path should be excluded."""
    path_obj = Path(path)

    # Check excluded files
    if path_obj.name in config.get("excluded_files", []):
        return True

    # Check excluded paths
    excluded_paths = config.get("excluded_paths", [])
    for exc_path in excluded_paths:
        if exc_path.endswith("/"):
            if exc_path.rstrip("/") in path_obj.parts:
                return True
        else:
            if exc_path in str(path_obj):
                return True

    return False


def scan_file(
    file_path: str,
    simplified_patterns: list[re.Pattern],
    mixed_patterns: list[re.Pattern],
) -> list[dict[str, Any]]:
    """Scan a single file for patterns."""
    issues = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return issues

    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        # Check for simplified Chinese
        for pattern in simplified_patterns:
            matches = pattern.findall(line)
            if matches:
                issues.append({
                    "type": "simplified_chinese",
                    "file": file_path,
                    "line": i,
                    "content": line.strip()[:100],
                    "match": matches[0] if matches else "",
                })

        # Check for mixed Chinese-English
        for pattern in mixed_patterns:
            matches = pattern.findall(line)
            if matches:
                issues.append({
                    "type": "mixed_chinese_english",
                    "file": file_path,
                    "line": i,
                    "content": line.strip()[:100],
                    "match": matches[0] if matches else "",
                })

    return issues


def scan_directory(
    directory: str,
    simplified_patterns: list[re.Pattern],
    mixed_patterns: list[re.Pattern],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Scan directory recursively."""
    all_issues = []

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)

            if is_excluded(file_path, config):
                continue

            # Only scan text files
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    f.read(1024)
            except (UnicodeDecodeError, OSError):
                continue

            issues = scan_file(file_path, simplified_patterns, mixed_patterns)
            all_issues.extend(issues)

    return all_issues


def format_output(issues: list[dict[str, Any]], output_format: str) -> str:
    """Format issues for output."""
    if not issues:
        return ""

    if output_format == "json":
        return json.dumps(issues, indent=2, ensure_ascii=False)

    # Default: text format
    lines = []
    lines.append(f"Found {len(issues)} issue(s):\n")

    current_file = None
    for issue in issues:
        if issue["file"] != current_file:
            current_file = issue["file"]
            lines.append(f"\n--- {issue['file']} ---")

        lines.append(f"  Line {issue['line']}: [{issue['type']}] {issue['content']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="CI-ScriptScan: Detect Simplified Chinese and mixed language patterns"
    )
    parser.add_argument(
        "--config", "-c",
        default="scripts/ci-script-scan/config.json",
        help="Path to config file"
    )
    parser.add_argument(
        "--directory", "-d",
        default=".",
        help="Directory to scan"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 if issues found (for CI)"
    )

    args = parser.parse_args()

    # Load config
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", args.config)
    if not os.path.exists(config_path):
        config_path = args.config

    try:
        config = load_config(config_path)
    except FileNotFoundError:
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config: {e}", file=sys.stderr)
        sys.exit(1)

    # Compile patterns
    simplified_patterns, mixed_patterns = compile_patterns(config)

    # Scan directory
    issues = scan_directory(args.directory, simplified_patterns, mixed_patterns, config)

    # Output results
    if issues:
        output = format_output(issues, args.format)
        print(output)

        if args.exit_code:
            print("\n[CI-ScriptScan] Issues detected. Please review.", file=sys.stderr)
            sys.exit(1)
    else:
        print("[CI-ScriptScan] No issues found.")


if __name__ == "__main__":
    main()
