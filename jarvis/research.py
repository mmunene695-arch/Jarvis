"""Explicit web research with citations.

Research only runs when the user asks for it. Results are *not* saved
automatically; callers must use the knowledge base's explicit save action.

The default backend uses DuckDuckGo's HTML endpoint, which needs no API key.
Everything goes through :func:`urllib` so there is no extra dependency.
"""

from __future__ import annotations

import html
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .errors import NetworkError, ValidationError

USER_AGENT = "JARVIS/0.2 (+local desktop assistant)"
SEARCH_URL = "https://html.duckduckgo.com/html/"


@dataclass(frozen=True)
class Source:
    index: int
    title: str
    url: str
    snippet: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"index": self.index, "title": self.title, "url": self.url, "snippet": self.snippet}


_RESULT_RE = re.compile(
    r'<a[^>]+class="[^"]*result__a[^"]*"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_SNIPPET_RE = re.compile(
    r'class="[^"]*result__snippet[^"]*"[^>]*>(?P<snippet>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG_RE.sub("", fragment or ""))).strip()


def _clean_href(href: str) -> str:
    if href.startswith("//"):
        href = "https:" + href
    parsed = urllib.parse.urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        query = urllib.parse.parse_qs(parsed.query)
        if "uddg" in query:
            return query["uddg"][0]
    return href


def parse_results(payload: str, limit: int = 5) -> list[Source]:
    """Parse a DuckDuckGo HTML results page into sources."""
    payload = payload or ""
    matches = list(_RESULT_RE.finditer(payload))
    snippets = [_text(m.group("snippet")) for m in _SNIPPET_RE.finditer(payload)]
    sources: list[Source] = []
    for index, match in enumerate(matches):
        url = _clean_href(html.unescape(match.group("href")))
        if not url.startswith(("http://", "https://")):
            continue
        title = _text(match.group("title")) or url
        snippet = snippets[index][:400] if index < len(snippets) else ""
        sources.append(Source(len(sources) + 1, title[:200], url, snippet))
        if len(sources) >= limit:
            break
    return sources


def search(
    query: str,
    *,
    limit: int = 5,
    timeout: float = 12.0,
    env: Mapping[str, str] | None = None,
    opener: Any = None,
) -> list[Source]:
    """Search the web. Raises :class:`NetworkError` when offline."""
    cleaned = (query or "").strip()
    if not cleaned:
        raise ValidationError("I need something to search for")
    if os.environ.get("JARVIS_OFFLINE", "").lower() in {"1", "true", "yes"}:
        raise NetworkError("Web research needs an internet connection, and I am in offline mode.")
    data = urllib.parse.urlencode({"q": cleaned, "kl": "wt-wt"}).encode()
    request = urllib.request.Request(SEARCH_URL, data=data, method="POST")
    request.add_header("User-Agent", USER_AGENT)
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    opener = opener or urllib.request.urlopen
    try:
        with opener(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise NetworkError(f"The search service returned HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise NetworkError("I cannot reach the search service. Check your internet connection.") from exc
    except TypeError:  # injected opener without timeout support
        with opener(request) as response:
            payload = response.read().decode("utf-8", errors="replace")
    sources = parse_results(payload, limit=limit)
    if not sources:
        raise NetworkError("The search returned no usable results.")
    return sources


def build_summary(query: str, sources: list[Source], *, summariser=None, target: float = 4.0) -> dict[str, Any]:
    """Summarise sources, preferring the language model when it is available."""
    citations = " ".join(f"[{s.index}]" for s in sources)
    if summariser is not None:
        prompt = (
            "Summarise the web results below in at most three sentences for a spoken reply. "
            "Cite sources with bracketed numbers such as [1]. Do not invent facts.\n\n"
            + "\n\n".join(
                f"[{s.index}] {s.title} ({s.url})\n{s.snippet}" for s in sources
            )
        )
        try:
            summary = summariser(prompt)
        except Exception:
            summary = ""
    else:
        summary = ""
    if not summary:
        bullets = " ".join(f"[{s.index}] {s.title} — {s.snippet}".strip() for s in sources[:3])
        summary = f"Here is what I found about {query}. {bullets}".strip()
    if "[" not in summary:
        summary = f"{summary} Sources: {citations}"
    return {
        "query": query,
        "summary": summary,
        "sources": [s.as_dict() for s in sources],
        "cited": True,
    }
