/**
 * @muhdfaisalwork-gif/meta-agent
 * Node.js SDK & MCP Bridge for Meta Nexus Agent (Zero-API Facebook & Instagram Autonomous Studio)
 */

const { spawn } = require("child_process");
const path = require("path");

const PACKAGE_NAME = "@muhdfaisalwork-gif/meta-agent";
const VERSION = "1.0.0";
const DEFAULT_STUDIO_URL = process.env.META_AGENT_URL || "http://127.0.0.1:8005";

class MetaNexusClient {
  constructor(baseUrl = DEFAULT_STUDIO_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async getStatus() {
    const res = await fetch(`${this.baseUrl}/api/status`);
    return res.json();
  }

  async getMasterSheet(platform = null, status = null) {
    const params = new URLSearchParams();
    if (platform) params.set("platform", platform);
    if (status) params.set("status", status);
    const qs = params.toString() ? `?${params.toString()}` : "";
    const res = await fetch(`${this.baseUrl}/api/sheet${qs}`);
    return res.json();
  }

  async extractSavedVideo(url, platform = "Instagram") {
    const res = await fetch(`${this.baseUrl}/api/extract`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, platform })
    });
    return res.json();
  }

  async mixMedia(options = { scenario: "batch" }) {
    const res = await fetch(`${this.baseUrl}/api/mixer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(options)
    });
    return res.json();
  }

  async publishReel({ platform = "Instagram", video_id = 1, caption = null, dry_run = false } = {}) {
    const res = await fetch(`${this.baseUrl}/api/publish`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ platform, video_id, caption, dry_run })
    });
    return res.json();
  }

  static launchPythonScript(scriptName, args = []) {
    const scriptPath = path.join(__dirname, scriptName);
    return spawn("python", [scriptPath, ...args], { stdio: "inherit" });
  }
}

module.exports = {
  PACKAGE_NAME,
  VERSION,
  DEFAULT_STUDIO_URL,
  MetaNexusClient
};
