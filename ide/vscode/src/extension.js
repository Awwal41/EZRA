/* eslint-disable no-undef */
"use strict";

const cp = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const vscode = require("vscode");

const LANES = [
  { id: "local", label: "Local", heights: [8, 12, 16, 10] },
  { id: "agent", label: "Agent", heights: [10, 16, 12, 8] },
  { id: "cline", label: "Cline", heights: [12, 8, 16, 10] },
  { id: "openclaw", label: "Claw", heights: [8, 10, 12, 16] },
];

function cfg() {
  return vscode.workspace.getConfiguration("ezra");
}

function workspaceFolder() {
  const folders = vscode.workspace.workspaceFolders;
  return folders && folders.length ? folders[0].uri.fsPath : os.homedir();
}

function whichOnPath(name) {
  const envPath = process.env.PATH || "";
  const parts = envPath.split(path.delimiter);
  const exts =
    process.platform === "win32"
      ? (process.env.PATHEXT || ".EXE;.CMD;.BAT").split(";").filter(Boolean)
      : [""];
  for (const dir of parts) {
    for (const ext of exts) {
      const candidate = path.join(dir, name + ext.toLowerCase());
      const alt = path.join(dir, name + ext);
      for (const file of [candidate, alt]) {
        try {
          if (fs.existsSync(file)) {
            return file;
          }
        } catch {
          /* ignore */
        }
      }
    }
  }
  return "";
}

function resolveEzraInvocation() {
  const cli = (cfg().get("cliPath") || "").trim();
  if (cli) {
    return { cmd: cli, prefix: [] };
  }
  const found = whichOnPath("ezra");
  if (found) {
    return { cmd: found, prefix: [] };
  }
  const py = (cfg().get("pythonPath") || "").trim();
  if (py) {
    return { cmd: py, prefix: ["-m", "ezra"] };
  }
  const pyFound = whichOnPath("python") || whichOnPath("python3");
  if (pyFound) {
    return { cmd: pyFound, prefix: ["-m", "ezra"] };
  }
  return null;
}

function runEzra(args, { timeoutMs } = {}) {
  const inv = resolveEzraInvocation();
  if (!inv) {
    return Promise.reject(
      new Error(
        "ezra CLI not found. Set ezra.cliPath or ezra.pythonPath, or put ezra on PATH."
      )
    );
  }
  return new Promise((resolve, reject) => {
    const child = cp.spawn(inv.cmd, inv.prefix.concat(args), {
      cwd: workspaceFolder(),
      env: process.env,
      windowsHide: true,
    });
    let out = "";
    let err = "";
    const timer =
      timeoutMs &&
      setTimeout(() => {
        child.kill();
        reject(new Error("ezra timed out"));
      }, timeoutMs);
    child.stdout.on("data", (d) => {
      out += d.toString();
    });
    child.stderr.on("data", (d) => {
      err += d.toString();
    });
    child.on("error", (e) => {
      if (timer) {
        clearTimeout(timer);
      }
      reject(e);
    });
    child.on("close", (code) => {
      if (timer) {
        clearTimeout(timer);
      }
      if (code === 0) {
        resolve(out);
      } else {
        reject(new Error((err || out || "ezra failed").trim()));
      }
    });
  });
}

function parseProbe(text) {
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start < 0 || end <= start) {
    throw new Error("ezra ide probe did not return JSON");
  }
  return JSON.parse(text.slice(start, end + 1));
}

function quoteForShell(value) {
  if (process.platform === "win32") {
    return `"${String(value).replace(/"/g, '\\"')}"`;
  }
  return `'${String(value).replace(/'/g, `'\\''`)}'`;
}

function argvFromProbe(lane, probe) {
  const info = probe && probe.lanes && probe.lanes[lane];
  if (info && Array.isArray(info.argv) && info.argv.length) {
    return info.argv;
  }
  if (info && info.cli) {
    return [info.cli];
  }
  return [lane];
}

function clineRunArgs(probe, model, text) {
  const info = (probe && probe.lanes && probe.lanes.cline) || {};
  const flags = Array.isArray(info.run_flags)
    ? info.run_flags.slice()
    : ["-P", "openai-compatible", "-k", "ezra-local"];
  if (model) {
    const idx = flags.indexOf("-m");
    if (idx >= 0) {
      flags[idx + 1] = model;
    } else {
      flags.push("-m", model);
    }
  }
  flags.push(text);
  return flags;
}

function html(webview, nonce, extUri) {
  const css = webview.asWebviewUri(vscode.Uri.joinPath(extUri, "media", "grid.css"));
  const js = webview.asWebviewUri(vscode.Uri.joinPath(extUri, "media", "grid.js"));
  const tiles = LANES.map((lane) => {
    const bars = lane.heights
      .map((h) => `<span style="height:${h}px"></span>`)
      .join("");
    return `<button class="lane" type="button" data-lane="${lane.id}" aria-pressed="false">
      <div class="cols">${bars}</div>
      <div class="lane-name">${lane.label}</div>
      <div class="lane-state">…</div>
    </button>`;
  }).join("");
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${nonce}';"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <link rel="stylesheet" href="${css}"/>
  <title>EZRA Grid</title>
</head>
<body>
  <div class="wrap">
    <div class="head">
      <div class="brand">
        <div class="word">EZRA Grid</div>
        <div class="sub">Pick a lane. Stay local unless you hand off.</div>
      </div>
      <div id="pill" class="pill off">off grid</div>
    </div>
    <div id="lanes" class="lanes">${tiles}</div>
    <div class="bind">
      <label id="model-wrap">Model
        <select id="model"></select>
      </label>
      <label id="agent-wrap" hidden>Agent
        <select id="agent"></select>
      </label>
      <div id="note" class="note"></div>
    </div>
    <div id="log" class="log"></div>
    <div class="composer">
      <textarea id="prompt" placeholder="Ctrl+Enter to send on the selected lane"></textarea>
      <div class="row">
        <button class="ghost" id="refresh" type="button">Refresh</button>
        <button class="act" id="send" type="button">Send</button>
      </div>
    </div>
  </div>
  <script nonce="${nonce}" src="${js}"></script>
</body>
</html>`;
}

class GridViewProvider {
  constructor(context) {
    this._context = context;
    this._view = undefined;
    this._probe = { lanes: {} };
    this._status = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      80
    );
    this._status.command = "ezra.grid.focus";
    this._status.text = "$(debug-disconnect) EZRA";
    this._status.tooltip = "EZRA Grid — sideload only, off grid";
    this._status.show();
  }

  resolveWebviewView(webviewView) {
    this._view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [
        vscode.Uri.joinPath(this._context.extensionUri, "media"),
      ],
    };
    const nonce = Math.random().toString(36).slice(2);
    webviewView.webview.html = html(webviewView.webview, nonce, this._context.extensionUri);
    webviewView.webview.onDidReceiveMessage((msg) => this._onMessage(msg));
    this.refresh();
  }

  post(msg) {
    if (this._view) {
      this._view.webview.postMessage(msg);
    }
  }

  async refresh() {
    try {
      const out = await runEzra(["ide", "probe", "--json"], { timeoutMs: 45000 });
      this._probe = parseProbe(out);
      this.post({ type: "probe", probe: this._probe });
    } catch (err) {
      this.post({
        type: "sys",
        text: String(err && err.message ? err.message : err),
      });
    }
  }

  async send(payload) {
    const lane = payload.lane || "local";
    const text = payload.text || "";
    if (!text.trim()) {
      return;
    }
    if (lane === "cline" || lane === "openclaw") {
      const argv = argvFromProbe(lane, this._probe);
      const extra =
        lane === "cline"
          ? clineRunArgs(this._probe, payload.model || cfg().get("model") || "", text)
          : [text];
      const term = vscode.window.createTerminal({
        name: lane === "cline" ? "EZRA → Cline" : "EZRA → OpenClaw",
        cwd: workspaceFolder(),
      });
      term.show();
      const line = argv.concat(extra).map(quoteForShell).join(" ");
      term.sendText(line);
      const info = (this._probe.lanes && this._probe.lanes.cline) || {};
      const hint =
        lane === "cline"
          ? ` Uses ezra serve at ${info.base_url || "http://127.0.0.1:8000/v1"} (no cloud API key). Start: ezra serve --model <name>. Once: ezra cline use-local --auth.`
          : "";
      this.post({
        type: "done",
        lane,
        text:
          `Opened a terminal for ${lane}. EZRA does not auto-start this agent — confirm the command there.` +
          hint,
      });
      return;
    }
    const args = ["chat", "--backend", cfg().get("backend") || "auto", "--no-stream"];
    if (lane === "agent") {
      const agent = payload.agent || cfg().get("agent") || "";
      if (!agent) {
        this.post({ type: "sys", text: "Pick a personal agent, or run ezra agents init." });
        return;
      }
      args.push("--agent", agent);
    } else {
      const model = payload.model || cfg().get("model") || "";
      if (!model) {
        this.post({
          type: "sys",
          text: "Pick an installed gallery model, or ezra models download <name>.",
        });
        return;
      }
      args.push("--model", model);
    }
    args.push("-p", text);
    try {
      const out = await runEzra(args, { timeoutMs: 10 * 60 * 1000 });
      this.post({ type: "done", lane, text: out.trim() || "(empty reply)" });
    } catch (err) {
      this.post({
        type: "sys",
        text: String(err && err.message ? err.message : err),
      });
    }
  }

  async doctor() {
    try {
      const out = await runEzra(["doctor"], { timeoutMs: 30000 });
      this.post({ type: "sys", text: out.trim() });
    } catch (err) {
      this.post({
        type: "sys",
        text: String(err && err.message ? err.message : err),
      });
    }
  }

  _onMessage(msg) {
    if (!msg || !msg.type) {
      return;
    }
    if (msg.type === "ready" || msg.type === "refresh") {
      this.refresh();
    } else if (msg.type === "send") {
      this.send(msg);
    } else if (msg.type === "lane") {
      const off = msg.lane !== "openclaw";
      this._status.text = off
        ? "$(debug-disconnect) EZRA OFF GRID"
        : "$(debug-disconnect) EZRA " + String(msg.lane).toUpperCase();
    }
  }

  dispose() {
    this._status.dispose();
  }
}

async function activate(context) {
  const provider = new GridViewProvider(context);
  context.subscriptions.push(provider);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("ezra.gridView", provider, {
      webviewOptions: { retainContextWhenHidden: true },
    })
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("ezra.grid.focus", () =>
      vscode.commands.executeCommand("ezra.gridView.focus")
    )
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("ezra.probeRefresh", () => provider.refresh())
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("ezra.doctor", () => provider.doctor())
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("ezra.selectLane", async () => {
      const pick = await vscode.window.showQuickPick(
        [
          { label: "EZRA local", description: "Gallery model on this machine", id: "local" },
          { label: "Personal agent", description: "agents/<name>/ prompt + models", id: "agent" },
          { label: "Cline", description: "Coding agent — terminal hand-off", id: "cline" },
          { label: "OpenClaw", description: "Gateway — terminal hand-off", id: "openclaw" },
        ],
        { title: "EZRA Grid lane" }
      );
      if (pick) {
        provider.post({ type: "probe", probe: provider._probe });
        await vscode.commands.executeCommand("ezra.gridView.focus");
        provider.post({ type: "sys", text: "Lane: " + pick.id });
      }
    })
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
