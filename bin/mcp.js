#!/usr/bin/env node
/**
 * MCP Stdio Bridge for @muhdfaisalwork-gif/meta-agent
 */

const path = require("path");
const { spawn } = require("child_process");

const child = spawn("python", [path.join(__dirname, "..", "run_mcp.py")], {
  stdio: "inherit"
});

child.on("exit", (code) => {
  process.exit(code || 0);
});
