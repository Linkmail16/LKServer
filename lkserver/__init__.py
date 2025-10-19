"""
LKServer - Expose your local Python servers to the internet instantly!

A simple and powerful framework for exposing local HTTP servers through WebSocket tunnels.
Perfect for testing webhooks, sharing demos, or accessing local services remotely.
"""

from .server import LKServer, Request, send_file, redirect, render_template

__version__ = "1.0.1"
__author__ = "Linkmail16"
__all__ = ["LKServer", "Request", "send_file", "redirect", "render_template"]

# Note: When updating version, also update:
# - lkserver/server.py: UpdateChecker.CURRENT_VERSION
# - setup.py: version
# - https://geometryamerica.xyz/updates/version.txt
