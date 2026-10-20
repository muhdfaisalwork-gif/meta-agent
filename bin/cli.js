#!/usr/bin/env node
/**
 * CLI Entrypoint for @muhdfaisalwork-gif/meta-agent
 */

const path = require("path");
const { spawn } = require("child_process");

const args = process.argv.slice(2);
const targetScript = args.includes("--studio") || args.length === 0 ? "run.py" : "main_agent.py";
const filteredArgs = args.filter(a => a !== "--studio");

const child = spawn("python", [path.join(__dirname, "..", targetScript), ...filteredArgs], {
  stdio: "inherit"
});

child.on("exit", (code) => {
  process.exit(code || 0);
});
