(function () {
  const vscode = acquireVsCodeApi();
  const state = vscode.getState() || {
    lane: "local",
    model: "",
    agent: "",
    log: [],
  };

  const PLACEHOLDERS = {
    local: "Ask anything…",
    agent: "Task for this agent…",
    cline: "Describe a coding task…",
    openclaw: "Message to hand off…",
  };
  const LANE_SUB = {
    local: "Local model on this machine",
    agent: "Personal agent, still local",
    cline: "Cline via ezra serve",
    openclaw: "Hand-off to OpenClaw",
  };
  const WHO = {
    you: "You",
    local: "EZRA",
    agent: "Agent",
    cline: "Cline",
    openclaw: "Claw",
    sys: "Grid",
  };

  const lanesEl = document.getElementById("lanes");
  const logEl = document.getElementById("log");
  const noteEl = document.getElementById("note");
  const pillEl = document.getElementById("pill");
  const subEl = document.getElementById("sub");
  const modelSel = document.getElementById("model");
  const agentSel = document.getElementById("agent");
  const promptEl = document.getElementById("prompt");
  const sendBtn = document.getElementById("send");
  const refreshBtn = document.getElementById("refresh");
  const modelWrap = document.getElementById("model-wrap");
  const agentWrap = document.getElementById("agent-wrap");

  let probe = { lanes: {} };
  let busy = false;

  function persist() {
    vscode.setState(state);
  }

  function canSend() {
    return !busy && !!(promptEl.value || "").trim();
  }

  function syncSend() {
    sendBtn.disabled = !canSend();
    sendBtn.classList.toggle("busy", busy);
  }

  function resizePrompt() {
    promptEl.style.height = "auto";
    promptEl.style.height = Math.min(Math.max(promptEl.scrollHeight, 44), 160) + "px";
  }

  function append(role, text, lane) {
    const item = { role, text, lane: lane || state.lane };
    state.log.push(item);
    if (state.log.length > 80) {
      state.log = state.log.slice(-80);
    }
    persist();
    renderLog();
  }

  function renderEmpty() {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.innerHTML =
      '<div class="empty-mark" aria-hidden="true"><i></i><i></i><i></i><i></i></div>' +
      "<h2>What should we work on?</h2>" +
      "<p>Pick a lane, then ask. Local models stay on this machine.</p>";
    logEl.appendChild(empty);
  }

  function renderLog() {
    logEl.innerHTML = "";
    if (!state.log.length && !busy) {
      renderEmpty();
      return;
    }
    for (const item of state.log) {
      const div = document.createElement("div");
      const kind = item.role === "you" ? "you" : item.role === "sys" ? "sys" : item.lane || "sys";
      div.className = "msg " + kind;
      const who = document.createElement("span");
      who.className = "who";
      who.textContent =
        item.role === "you" ? WHO.you : WHO[item.lane] || item.lane || WHO.sys;
      div.appendChild(who);
      div.appendChild(document.createTextNode(item.text));
      logEl.appendChild(div);
    }
    if (busy) {
      const last = state.log[state.log.length - 1];
      if (!last || last.role === "you" || last.role === "sys") {
        const think = document.createElement("div");
        think.className = "msg thinking " + (state.lane || "local");
        const who = document.createElement("span");
        who.className = "who";
        who.textContent = WHO[state.lane] || "EZRA";
        const dots = document.createElement("span");
        dots.className = "dots";
        dots.setAttribute("aria-label", "Thinking");
        dots.innerHTML = "<i></i><i></i><i></i>";
        think.appendChild(who);
        think.appendChild(dots);
        logEl.appendChild(think);
      }
    }
    logEl.scrollTop = logEl.scrollHeight;
  }

  function fillSelect(sel, values, current) {
    const keep = current || "";
    sel.innerHTML = "";
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = values.length ? "Select…" : "(none)";
    sel.appendChild(blank);
    for (const value of values) {
      const opt = document.createElement("option");
      opt.value = value;
      opt.textContent = value;
      sel.appendChild(opt);
    }
    if (keep && values.indexOf(keep) !== -1) {
      sel.value = keep;
    }
  }

  function laneReady(id) {
    const lane = probe.lanes && probe.lanes[id];
    return !!(lane && lane.ready);
  }

  function applyLane() {
    const offGrid = state.lane !== "openclaw";
    pillEl.textContent = offGrid ? "off grid" : "hand-off";
    pillEl.className = "pill " + (offGrid ? "off" : "on-grid");
    if (subEl) {
      subEl.textContent = LANE_SUB[state.lane] || LANE_SUB.local;
    }
    promptEl.placeholder = PLACEHOLDERS[state.lane] || PLACEHOLDERS.local;
    for (const btn of lanesEl.querySelectorAll(".lane")) {
      btn.setAttribute("aria-pressed", btn.dataset.lane === state.lane ? "true" : "false");
    }
    modelWrap.hidden = !(state.lane === "local" || state.lane === "cline");
    agentWrap.hidden = state.lane !== "agent";
    const lane = (probe.lanes && probe.lanes[state.lane]) || {};
    const note = lane.note || "";
    noteEl.textContent = note;
    noteEl.hidden = !note;
  }

  function applyProbe(next) {
    probe = next || { lanes: {} };
    const local = (probe.lanes && probe.lanes.local) || {};
    const agent = (probe.lanes && probe.lanes.agent) || {};
    const models = local.models_installed || [];
    const agents = (agent.agents || []).map((a) => a.name);
    fillSelect(modelSel, models, state.model);
    fillSelect(agentSel, agents, state.agent);
    if (!state.model && models.length) {
      state.model = models[0];
      modelSel.value = state.model;
    }
    if (!state.agent && agents.length) {
      state.agent = agents[0];
      agentSel.value = state.agent;
    }
    for (const btn of lanesEl.querySelectorAll(".lane")) {
      const id = btn.dataset.lane;
      const st = btn.querySelector(".lane-state");
      const ready = laneReady(id);
      if (st) {
        st.classList.toggle("ready", ready);
      }
      const base = btn.dataset.title || btn.title;
      btn.title = base + (ready ? " · ready" : " · not ready");
    }
    applyLane();
    persist();
  }

  lanesEl.addEventListener("click", (ev) => {
    const btn = ev.target.closest(".lane");
    if (!btn) {
      return;
    }
    state.lane = btn.dataset.lane;
    persist();
    applyLane();
    vscode.postMessage({ type: "lane", lane: state.lane });
  });

  modelSel.addEventListener("change", () => {
    state.model = modelSel.value;
    persist();
  });
  agentSel.addEventListener("change", () => {
    state.agent = agentSel.value;
    persist();
  });

  sendBtn.addEventListener("click", send);
  promptEl.addEventListener("input", () => {
    resizePrompt();
    syncSend();
  });
  promptEl.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      send();
    }
  });
  refreshBtn.addEventListener("click", () => {
    vscode.postMessage({ type: "refresh" });
  });

  function send() {
    const text = (promptEl.value || "").trim();
    if (!text || busy) {
      return;
    }
    busy = true;
    append("you", text, state.lane);
    promptEl.value = "";
    resizePrompt();
    syncSend();
    vscode.postMessage({
      type: "send",
      lane: state.lane,
      text,
      model: state.model,
      agent: state.agent,
    });
  }

  window.addEventListener("message", (ev) => {
    const msg = ev.data || {};
    if (msg.type === "probe") {
      applyProbe(msg.probe);
    } else if (msg.type === "chunk") {
      const last = state.log[state.log.length - 1];
      if (last && last.role === "bot" && last.lane === msg.lane) {
        last.text += msg.text;
        renderLog();
      } else {
        append("bot", msg.text, msg.lane);
      }
    } else if (msg.type === "done") {
      busy = false;
      syncSend();
      if (msg.text) {
        append("bot", msg.text, msg.lane || state.lane);
      } else {
        renderLog();
      }
    } else if (msg.type === "sys") {
      append("sys", msg.text, "sys");
      busy = false;
      syncSend();
    }
  });

  applyLane();
  renderLog();
  resizePrompt();
  syncSend();
  vscode.postMessage({ type: "ready" });
})();
