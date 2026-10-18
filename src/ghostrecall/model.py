"""Provenance model and memory items.

Every recallable item MUST carry provenance (source file + line, or a
git commit). Items without provenance are dropped by the walkers and
are never exported: that is the anti-hallucination rule in PLAN.md.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict

SOURCE_TYPES = ("decision", "note", "doc", "commit", "session_note")

@dataclass
class Provenance:
    path: str            # project-relative path, or "git:<short-hash>"
    line: int | None = None
    commit: str | None = None
    date: str | None = None
    def is_valid(self) -> bool:
        if self.commit:
            return True
        return bool(self.path) and self.line is not None and self.line >= 1
    def to_dict(self): return asdict(self)

@dataclass
class Item:
    id: str
    title: str
    text: str
    source_type: str
    provenance: Provenance
    tags: list[str] = field(default_factory=list)
    status: str = "active"          # active | superseded
    supersedes: str | None = None   # title/id this decision supersedes
    superseded_by: str | None = None
    pinned: bool = False
    secret_findings: list[dict] = field(default_factory=list)
    @property
    def blocked(self) -> bool:
        return bool(self.secret_findings)
    @property
    def date(self) -> str | None:
        return self.provenance.date
    def to_dict(self, include_text: bool = True):
        d = {
            "id": self.id, "title": self.title, "source_type": self.source_type,
            "provenance": self.provenance.to_dict(), "tags": list(self.tags),
            "status": self.status, "supersedes": self.supersedes,
            "superseded_by": self.superseded_by, "pinned": self.pinned,
            "blocked": self.blocked, "secret_findings": list(self.secret_findings),
        }
        if include_text:
            d["text"] = self.text
        return d
