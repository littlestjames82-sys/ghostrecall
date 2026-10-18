"""Secrets carry-over guard, compatible in spirit with GhostSlice v0.4:
findings record path + line + type ONLY, never the value. An item with
any finding is blocked from export by default."""
from __future__ import annotations
import re
from dataclasses import dataclass

_PATTERNS = [
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("openai-or-anthropic-key", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_\-]{16,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b")),
    ("generic-secret-assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*[\"']?[A-Za-z0-9_\-/+=]{20,}")),
]
_PLACEHOLDERS = ("example", "xxx", "your-", "changeme", "placeholder", "dummy",
                 "sample", "fixture", "redacted", "not-a-real", "fake", "test-key")

@dataclass
class Finding:
    path: str
    line: int
    type: str
    def to_dict(self): return {"path": self.path, "line": self.line, "type": self.type}

def scan_text(text: str, path: str) -> list[Finding]:
    out: list[Finding] = []
    for i, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        for name, pat in _PATTERNS:
            m = pat.search(line)
            if not m:
                continue
            if any(p in low for p in _PLACEHOLDERS):
                continue
            out.append(Finding(path, i, name))
            break
    return out
