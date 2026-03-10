"""
Tests for i18n functionality
"""
import json
import pytest
from pathlib import Path


def test_japanese_translations_exist():
    """Test that Japanese translation file exists and is valid JSON."""
    translations_path = Path(__file__).parent.parent.parent / "frontend" / "public" / "locales" / "ja" / "translation.json"
    assert translations_path.exists(), "Japanese translation file should exist"

    with open(translations_path, 'r', encoding='utf-8') as f:
        translations = json.load(f)

    # Check required keys exist
    assert "common" in translations, "Common translations should exist"
    assert "commands" in translations, "Commands translations should exist"
    assert "unitTypes" in translations, "Unit types translations should exist"


def test_english_translations_exist():
    """Test that English translation file exists and is valid JSON."""
    translations_path = Path(__file__).parent.parent.parent / "frontend" / "public" / "locales" / "en" / "translation.json"
    assert translations_path.exists(), "English translation file should exist"

    with open(translations_path, 'r', encoding='utf-8') as f:
        translations = json.load(f)

    # Check required keys exist
    assert "common" in translations, "Common translations should exist"
    assert "commands" in translations, "Commands translations should exist"
    assert "unitTypes" in translations, "Unit types translations should exist"


def test_translations_parity():
    """Test that Japanese and English translations have the same keys."""
    ja_path = Path(__file__).parent.parent.parent / "frontend" / "public" / "locales" / "ja" / "translation.json"
    en_path = Path(__file__).parent.parent.parent / "frontend" / "public" / "locales" / "en" / "translation.json"

    with open(ja_path, 'r', encoding='utf-8') as f:
        ja = json.load(f)

    with open(en_path, 'r', encoding='utf-8') as f:
        en = json.load(f)

    def get_all_keys(obj, prefix=""):
        keys = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_prefix = f"{prefix}.{k}" if prefix else k
                keys.add(new_prefix)
                if isinstance(v, dict):
                    keys.update(get_all_keys(v, new_prefix))
        return keys

    ja_keys = get_all_keys(ja)
    en_keys = get_all_keys(en)

    # Check that English has at least the same keys as Japanese
    missing_in_en = ja_keys - en_keys
    assert not missing_in_en, f"Missing keys in English translations: {missing_in_en}"


def test_language_switcher_exists():
    """Test that LanguageSwitcher component exists."""
    component_path = Path(__file__).parent.parent.parent / "frontend" / "app" / "lib" / "language-switcher.tsx"
    assert component_path.exists(), "LanguageSwitcher component should exist"


def test_i18n_provider_exists():
    """Test that I18nProvider component exists."""
    provider_path = Path(__file__).parent.parent.parent / "frontend" / "app" / "lib" / "i18n-provider.tsx"
    assert provider_path.exists(), "I18nProvider component should exist"


def test_use_i18n_hook_exists():
    """Test that useI18n hook exists."""
    hook_path = Path(__file__).parent.parent.parent / "frontend" / "app" / "lib" / "i18n.ts"
    assert hook_path.exists(), "useI18n hook should exist"
