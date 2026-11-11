"""Local knowledge base plus explicit web research."""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .. import research as research_module
from ..config import JarvisConfig
from ..storage import JsonFileStore


@dataclass
class KnowledgeBase:
    config: JarvisConfig
    audit: Any = None

    def __post_init__(self) -> None:
        self._store = JsonFileStore(self.config.data_dir / "knowledge.json", default_factory=list)
        self.last_research: dict[str, Any] | None = None

    # ------------------------------------------------------------------
    def _load(self) -> list[dict[str, Any]]:
        data = self._store.read()
        return data if isinstance(data, list) else []

    def add(self, title: str, text: str, *, sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        entry = {
            "id": f"know-{uuid.uuid4().hex[:8]}",
            "title": (title or "Saved note").strip()[:200],
            "text": (text or "").strip()[:8000],
            "sources": sources or [],
            "created": time.time(),
            "created_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        entries = self._load()
        entries.append(entry)
        self._store.write(entries)
        if self.audit is not None:
            self.audit.record("knowledge.created", entry_id=entry["id"])
        return entry

    def all(self) -> list[dict[str, Any]]:
        return self._load()

    def search(self, query: str) -> list[dict[str, Any]]:
        terms = [t for t in re.split(r"\W+", (query or "").lower()) if t]
        if not terms:
            return []
        scored: list[tuple[int, dict[str, Any]]] = []
        for entry in self._load():
            haystack = f"{entry.get('title', '')} {entry.get('text', '')}".lower()
            score = sum(haystack.count(term) for term in terms if term in haystack)
            if score:
                scored.append((score, entry))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [entry for _, entry in scored]

    def describe(self, entries: list[dict[str, Any]], query: str = "") -> str:
        if not entries:
            return f"I have nothing saved about {query}." if query else "My knowledge base is empty."
        lines = [f"I have {len(entries)} saved item(s)" + (f" about {query}:" if query else ":")]
        for entry in entries[:10]:
            text = re.sub(r"\s+", " ", entry.get("text", ""))[:280]
            lines.append(f"• [{entry.get('id')}] {entry.get('title')}: {text}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def research(self, query: str) -> dict[str, Any]:
        """Search the web and summarise the results with citations."""
        from .. import cloud

        sources = research_module.search(query, limit=5)
        summariser = None
        if cloud.available():

            def summariser(prompt: str) -> str:  # noqa: F811 - intentional local definition
                return cloud.complete(
                    prompt,
                    system=(
                        "You summarise web search results for a spoken answer. Be factual, cite "
                        "sources with bracketed numbers, and never invent details."
                    ),
                )
        result = research_module.build_summary(query, sources, summariser=summariser)
        self.last_research = result
        if self.audit is not None:
            self.audit.record("research.performed", query=query, sources=len(sources))
        return result
