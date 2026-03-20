#!/bin/bash
# MCP server wrapper with absolute paths
# Suppress Python warnings that could confuse MCP client
export PYTHONWARNINGS="ignore"
exec /home/nissim/.local/bin/uv run --directory /home/nissim/Documents/dev/parseltongue-claude parseltongue-mcp
