"""CLI entry point for KiboFlow Studio server and GitHub Pages static exporter."""

from __future__ import annotations

import argparse
from pathlib import Path

from kiboflow.exporter import export_static_site
from kiboflow.server import create_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="kiboflow",
        description="KiboFlow Studio — Public Agency Storefront, Client Demos & Founder Command Center",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="TCP port (default: 8000)")
    parser.add_argument(
        "--export-static",
        metavar="DIR",
        help="Export standalone static site for free GitHub Pages / Cloudflare Pages hosting",
    )
    args = parser.parse_args(argv)

    if args.export_static:
        out = export_static_site(Path(args.export_static))
        print(f"Exported static KiboFlow Studio site to {out}")
        return 0

    server = create_server(host=args.host, port=args.port)
    actual_host, actual_port = server.server_address[:2]
    print(
        f"KiboFlow Studio live on http://{actual_host}:{actual_port} "
        f"(Storefront: / | Founder Ops: /ops | Demos: /demos/hospitality, /demos/clinic, /demos/hardware)",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
