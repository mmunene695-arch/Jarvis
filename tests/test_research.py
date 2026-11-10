"""Web research: parsing, citations and the explicit save path."""

from __future__ import annotations

import urllib.error

import pytest

from jarvis import research
from jarvis.errors import NetworkError, ValidationError

SAMPLE_HTML = """
<html><body>
<div class="result">
  <a class="result__a" href="https://example.com/a">Solid state batteries explained</a>
  <a class="result__snippet" href="https://example.com/a">A solid electrolyte replaces the liquid one.</a>
</div>
<div class="result">
  <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Fb&amp;rut=abc">Energy density</a>
  <a class="result__snippet" href="#">Higher energy density is possible &amp; cheaper.</a>
</div>
</body></html>
"""


def test_parse_results_extracts_sources():
    sources = research.parse_results(SAMPLE_HTML)
    assert len(sources) == 2
    assert sources[0].title == "Solid state batteries explained"
    assert sources[0].url == "https://example.com/a"
    assert "solid electrolyte" in sources[0].snippet
    assert sources[1].url == "https://example.org/b"


def test_parse_results_respects_limit():
    assert len(research.parse_results(SAMPLE_HTML, limit=1)) == 1


def test_parse_empty_page():
    assert research.parse_results("<html></html>") == []


def test_search_requires_a_query():
    with pytest.raises(ValidationError):
        research.search("   ")


def test_search_offline_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JARVIS_OFFLINE", "1")
    with pytest.raises(NetworkError):
        research.search("batteries")


def test_search_handles_url_error(monkeypatch: pytest.MonkeyPatch):
    def boom(*_a, **_k):
        raise urllib.error.URLError("no network")

    with pytest.raises(NetworkError):
        research.search("batteries", opener=boom)


def test_search_parses_injected_response():
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return SAMPLE_HTML.encode()

    sources = research.search("batteries", opener=lambda *a, **k: FakeResponse())
    assert len(sources) == 2


def test_summary_adds_citations_without_model():
    sources = research.parse_results(SAMPLE_HTML)
    result = research.build_summary("batteries", sources)
    assert "[1]" in result["summary"]
    assert result["cited"] is True
    assert len(result["sources"]) == 2


def test_summary_uses_summariser():
    sources = research.parse_results(SAMPLE_HTML)
    result = research.build_summary("batteries", sources, summariser=lambda prompt: "Short answer [1].")
    assert result["summary"] == "Short answer [1]."


def test_summary_survives_failing_summariser():
    sources = research.parse_results(SAMPLE_HTML)

    def boom(_prompt):
        raise RuntimeError("model down")

    result = research.build_summary("batteries", sources, summariser=boom)
    assert result["summary"]
    assert "[1]" in result["summary"]
