"""ArchFlow CLI — entry point for all subcommands."""

from __future__ import annotations

import argparse
import sys

from archflow import __version__


def main() -> None:
    """Main CLI dispatcher."""
    parser = argparse.ArgumentParser(
        prog="archflow",
        description="ArchFlow - Context Hub MCP Server (Jira + GitHub + Draw.io)",
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"archflow {__version__}",
    )

    sub = parser.add_subparsers(dest="command")

    # archflow init
    sub.add_parser("init", help="Interactive setup wizard")

    # archflow doctor
    sub.add_parser("doctor", help="Check connection status and configuration")

    # archflow serve (explicit)
    sub.add_parser("serve", help="Start the MCP server (default when no command given)")

    args = parser.parse_args()

    if args.command == "init":
        from archflow.cli_init import run_init
        run_init()
    elif args.command == "doctor":
        from archflow.cli_doctor import run_doctor
        run_doctor()
    elif args.command == "serve":
        _run_server()
    elif args.command is None:
        # No subcommand → start MCP server (backward compatible)
        _run_server()
    else:
        parser.print_help()
        sys.exit(1)


def _run_server() -> None:
    """Start the MCP server."""
    from archflow.server import main as server_main
    server_main()
