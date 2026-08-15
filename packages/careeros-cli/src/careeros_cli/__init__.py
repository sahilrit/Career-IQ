"""careeros_cli: the CareerOS command-line interface — Career Brain
management, job search, and application package generation, wired
against the same pipeline a scheduled Runtime job uses.
"""

from careeros_cli.context import CLIContext, build_context
from careeros_cli.main import build_parser, main

__all__ = ["CLIContext", "build_context", "build_parser", "main"]
