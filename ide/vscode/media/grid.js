(function () {
  const vscode = acquireVsCodeApi();
  const state = vscode.getState() || {
    lane: "local",
    model: "",
    agent: "",
    log: [],
  };

  const lanesEl = document.getElementById("lanes");
  const logEl = document.getElementById("log");
  const noteEl = document.getElementById("note");
  const pillEl = document.getElementById("pill");
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

  function append(role, text, lane) {
    const item = { role, text, lane: lane || state.lane };
    state.log.push(item);
    if (state.log.length > 80) {
      state.log = state.log.slice(-80);
    }
    persist();
    renderLog();
  }

  function renderLog() {
    logEl.innerHTML = "";
    for (const item of state.log) {
      const div = document.createElement("div");
      div.className = "msg " + (item.role === "you" ? "you" : item.lane || "sys");
      const who = document.createElement("span");
      who.className = "who";
      who.textContent = item.role === "you" ? "you" : item.lane || "grid";
      div.appendChild(who);
      div.appendChild(document.createTextNode(item.text));
      logEl.appendChild(div);
    }
    logEl.scrollTop = logEl.scrollHeight;
  }

  function fillSelect(sel, values, current) {
    const keep = current || "";
    sel.innerHTML = "";
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = values.length ? "—" : "(none)";
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
    for (const btn of lanesEl.querySelectorAll(".lane")) {
      btn.setAttribute("aria-pressed", btn.dataset.lane === state.lane ? "true" : "false");
    }
    modelWrap.hidden = !(state.lane === "local" || state.lane === "cline");
    agentWrap.hidden = state.lane !== "agent";
    const lane = (probe.lanes && probe.lanes[state.lane]) || {};
    noteEl.textContent = lane.note || "";
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
      if (st) {
        st.textContent = laneReady(id) ? "ready" : "not ready";
      }
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
  promptEl.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" && (ev.ctrlKey || ev.metaKey)) {
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
    sendBtn.disabled = true;
    append("you", text, state.lane);
    promptEl.value = "";
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
      sendBtn.disabled = false;
      if (msg.text) {
        append("bot", msg.text, msg.lane || state.lane);
      }
    } else if (msg.type === "sys") {
      append("sys", msg.text, "sys");
      busy = false;
      sendBtn.disabled = false;
    }
  });

  applyLane();
  renderLog();
  vscode.postMessage({ type: "ready" });
})();
