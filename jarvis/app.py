"""Backwards/forwards compatible entry points.

``python -m jarvis.cli`` and the ``jarvis`` console script both land here.
"""

from __future__ import annotations

import sys

from .cli import build_parser, main  # noqa: F401

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
