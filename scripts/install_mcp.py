#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
1-Click MCP Auto-Installer for Claude Desktop & Cursor (scripts/install_mcp.py)
Registers Meta Nexus Agent (`run_mcp.py`) in claude_desktop_config.json.
"""

import os
import sys
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_MCP_PATH = os.path.join(ROOT_DIR, "run_mcp.py")


def install_claude_mcp() -> dict:
    appdata = os.getenv("APPDATA") or os.path.expanduser("~")
    claude_dir = os.path.join(appdata, "Claude")
    os.makedirs(claude_dir, exist_ok=True)
    config_file = os.path.join(claude_dir, "claude_desktop_config.json")

    data = {"mcpServers": {}}
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"mcpServers": {}}

    if "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
        data["mcpServers"] = {}

    data["mcpServers"]["meta-nexus"] = {
        "command": sys.executable,
        "args": [RUN_MCP_PATH]
    }

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return {
        "status": "success",
        "config_file": config_file,
        "mcp_server": "meta-nexus",
        "entrypoint": RUN_MCP_PATH
    }


if __name__ == "__main__":
    res = install_claude_mcp()
    print(json.dumps(res, indent=2))
