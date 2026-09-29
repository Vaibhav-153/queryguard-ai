"""Fail when likely committed API secrets are found in project text files."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", "data/workspaces"}
TEXT_SUFFIXES = {".py", ".md", ".toml", ".yaml", ".yml", ".json", ".txt", ".example"}
PATTERNS = {
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    "Groq key": re.compile(r"\bgsk_[A-Za-z0-9]{20,}\b"),
    "Private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def should_scan(path: Path) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    if any(part in relative for part in SKIP_PARTS):
        return False
    return path.suffix.lower() in TEXT_SUFFIXES or path.name == ".env.example"


def main() -> int:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or not should_scan(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path.relative_to(ROOT)}: possible {label}")
    if findings:
        print("Potential secrets found:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("No likely committed secrets found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
