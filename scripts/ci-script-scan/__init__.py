"""
CI-ScriptScan: Simplified Chinese and mixed language pattern detector
"""

from .scan import load_config, compile_patterns, is_excluded, scan_file, scan_directory

__version__ = "1.0.0"
__all__ = [
    "load_config",
    "compile_patterns",
    "is_excluded",
    "scan_file",
    "scan_directory",
]
