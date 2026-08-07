// Sceneroom UI.
//
// Two ideas carry the whole file:
//
// 1. Runs are streamed, not awaited. A pass takes ~30s, and the crew list is
//    the only thing on screen during it. Every step shown is a real agent
//    reporting a real timing — nothing here is simulated.
// 2. A flag lives in two places at once: underlined in the script and as a note
//    in the margin. Selecting either selects both, because the reviewer's
//    question is always "where in the scene is this?".

const $ = (id) => document.getElementById(id);

// Who contested claims are routed to. A real deployment reads this from the
// production's standards desk; the demo names a role so the handoff is concrete
// rather than "a human somewhere".
const ROUTED_TO = "Standards desk";

let scene = null;
let busy = false;
let selected = null;
let stream = null;

// --- small helpers ----------------------------------------------------------

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]),
  );

function toast(message, bad = false) {
  const el = $("toast");
  el.textContent = message;
  el.classList.toggle("bad", bad);
  el.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove("show"), bad ? 6000 : 3000);
}

function host(url) {
  try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return ""; }
}

function setBusy(on) {
  busy = on;
  $("go").disabled = on;
  $("demoBtn").disabled = on;
}

// --- the crew ---------------------------------------------------------------

const MARKS = { running: "", done: "✓", skipped: "–", failed: "✕", pending: "○" };

// The roster, so the panel is never empty and the reader can see the whole
// pipeline before any of it has run.
const CREW = ["writer", "extractor", "continuity", "verifier", "fandom", "rights", "adjudicator"];

let crewOrder = CREW;
let runNo = 0;
const crewState = new Map();

function resetCrew(agents = CREW, { status = "pending", detail = "", counted = true } = {}) {
  crewOrder = agents;
  crewState.clear();
  agents.forEach((a) => crewState.set(a, { agent: a, status, detail, ms: 0 }));
  if (counted) runNo += 1;
  $("runLabel").textContent = counted ? `/ run ${String(runNo).padStart(2, "0")}` : "";
  renderCrew();
}

function applyStep(step) {
  const prev = crewState.get(step.agent) || {};
  // A note() carries progress with no timing; it must not blank the detail or
  // reset a step that has already finished.
  crewState.set(step.agent, {
    ...prev,
    ...step,
    detail: step.detail || prev.detail || "",
    ms: step.ms || prev.ms || 0,
  });
  renderCrew();
}

// mm:ss, because a reviewer reads elapsed time, not a decimal. Under a minute
// still shows the minute field so the column stays aligned as it ticks past 60.
function clock(ms) {
  const s = Math.round(ms / 1000);
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

function renderCrew() {
  $("crew").innerHTML = crewOrder
    .map((name) => {
      const s = crewState.get(name) || { status: "pending" };
      // A running agent shows LIVE rather than a timing: the number is not
      // final yet, and a counter racing upward reads as a stopwatch, not work.
      const time = s.status === "running" ? "LIVE" : s.ms ? clock(s.ms) : "";
      return `
        <li class="${s.status}">
          <span class="mark">${MARKS[s.status] ?? "○"}</span>
          <span class="name">${esc(name)}</span>
          <span class="time">${esc(time)}</span>
          ${s.detail ? `<span class="detail">${esc(s.detail)}</span>` : ""}
        </li>`;
    })
    .join("");

  const settled = crewOrder.filter((n) => ["done", "skipped"].includes(crewState.get(n)?.status));
  // Wall clock, not the sum: the three checking agents run concurrently, so
  // adding their timings would overstate how long the pass actually took.
  const wall = Math.max(0, ...crewOrder.map((a) => crewState.get(a)?.ms || 0));
  const serial = ["writer", "extractor"].reduce((n, a) => n + (crewState.get(a)?.ms || 0), 0);
  $("runSummary").textContent =
    settled.length === crewOrder.length && wall ? `· ${clock(serial + wall)} total` : "";
}

// --- streaming --------------------------------------------------------------

function run(url, { onScene, working }) {
  if (busy) return;
  setBusy(true);
  $("crewHead").textContent = "While the crew runs";
  $("crewNote").textContent = working;
  if (stream) stream.close();
  stream = new EventSource(url);

  stream.addEventListener("crew", (e) => resetCrew(JSON.parse(e.data).agents));
  stream.addEventListener("step", (e) => applyStep(JSON.parse(e.data)));

  stream.addEventListener("scene", (e) => {
    stream.close(); stream = null; setBusy(false);
    $("crewHead").textContent = "The pass is done";
    $("crewNote").textContent = "Every claim is on the record. Decide what you want to keep.";
    onScene(JSON.parse(e.data));
    renderRecent();
  });

  stream.addEventListener("error", (e) => {
    stream.close(); stream = null; setBusy(false);
    let message = "The run stopped. Check the service logs.";
    try { message = JSON.parse(e.data).message || message; } catch { /* transport error */ }
    $("crewHead").textContent = "The run stopped";
    $("crewNote").textContent = "Nothing was recorded. The brief is still in the rail — run it again.";
    toast(message, true);
  });
}

// --- rendering the scene ----------------------------------------------------

function renderScene(next) {
  scene = next;
  $("crumb").textContent =
    `${scene.setting || scene.project} · ${scene.mode} · ${scene.claims.length} claims`;
  $("pageSlug").textContent = scene.setting || scene.project || "untitled scene";
  $("pageRev").textContent = scene.revision > 1 ? `rev. ${scene.revision}` : "first draft";
  $("sceneLabel").textContent = scene.intent || "Scene";

  // The setting, set enormous behind the page, and stamped on the file tab.
  // Split on the comma so "Seoul, 1963" stacks place over year.
  const where = scene.setting || scene.project || "";
  $("watermark").textContent = where.split(/,\s*/).join("\n");
  $("page").dataset.tab = `${where || "untitled"} · ${scene.mode}`.toUpperCase();

  renderScript();
  renderMargin();
  renderLedger();

  const record = $("recordBtn");
  record.href = `/api/scenes/${scene.id}/record.md`;
  record.hidden = false;

  // The counter must agree with the Adjudicator, not with a second rule
  // invented in the browser.
  const open = scene.claims.filter((c) => c.needs_human && c.disposition === "pending").length;
  const counter = $("counter");
  counter.textContent = open
    ? `${open} flag${open > 1 ? "s" : ""} need${open > 1 ? "" : "s"} a decision`
    : "every claim is on the record";
  counter.classList.toggle("clear", open === 0);

  // The frame is of the scene that was signed off, so it is only offered once
  // nothing is still waiting on a person.
  const settled = scene.claims.length > 0 && open === 0;
  $("frameBtn").hidden = !settled;
  if (!settled) { $("frameWrap").hidden = true; }
}

// Wrap each claim's excerpt where it appears in the scene. Excerpts come back
// verbatim from the extractor, but a revise can move text, so a miss is normal
// and simply means the note has no anchor — never an error.
function renderScript() {
  const text = scene.text || "";
  const hits = [];
  scene.claims.forEach((claim, i) => {
    const needle = (claim.excerpt || "").trim();
    if (!needle) return;
    const at = text.indexOf(needle);
    if (at === -1) return;
    if (hits.some((h) => at < h.end && at + needle.length > h.start)) return; // overlap
    hits.push({ start: at, end: at + needle.length, claim, n: i + 1 });
  });
  hits.sort((a, b) => a.start - b.start);

  let out = "";
  let cursor = 0;
  for (const h of hits) {
    const decided = h.claim.disposition !== "pending";
    out += esc(text.slice(cursor, h.start));
    // A button, not a span: a flagged line is an actionable control and must be
    // reachable by keyboard.
    out += `<button type="button" class="span ${h.claim.verdict || ""}${decided ? " decided" : ""}"
                  data-claim="${h.claim.id}"
                  aria-label="Flag ${h.n}: ${esc(h.claim.verdict || "pending")}"
            >${esc(text.slice(h.start, h.end))}<sup>${h.n}</sup></button>`;
    cursor = h.end;
  }
  out += esc(text.slice(cursor));
  $("script").innerHTML = out || esc(text);

  $("script").querySelectorAll("[data-claim]").forEach((el) => {
    el.onclick = () => select(el.dataset.claim);
  });
}

// The Fandom agent writes at length when it finds a real controversy, which is
// exactly when you want it — but an 80-line note swamps every other flag in the
// margin. Long text collapses to its first sentences and opens on demand.
const LONG = 240;

function longText(label, text, italic) {
  const body = String(text || "").trim();
  if (!body) return "";
  const cls = italic ? "reasoning long-body em" : "reasoning long-body";
  if (body.length <= LONG) return `<div class="${cls}">${esc(body)}</div>`;
  const head = body.slice(0, LONG).replace(/\s+\S*$/, "");
  return `<details class="long">
      <summary><span class="${cls}">${esc(head)}…</span>
        <span class="more">${esc(label || "Read")} in full</span></summary>
      <div class="${cls}">${esc(body)}</div>
    </details>`;
}

function sourceList(sources) {
  if (!sources?.length) return "";
  return `<ul class="sources">${sources
    .map(
      (s) => `<li><span>↗</span
              ><a class="title" href="${esc(s.url)}" target="_blank" rel="noopener"
                 title="${esc(s.title)}">${esc(s.title)}</a
              ><span class="host">${esc(host(s.url))}</span></li>`,
    )
    .join("")}</ul>`;
}

function renderMargin() {
  const flagged = scene.claims.filter((c) => c.verdict && c.verdict !== "verified");
  const shown = flagged.length ? flagged : scene.claims;

  $("margin").innerHTML = shown
    .map((c) => {
      const n = scene.claims.indexOf(c) + 1;
      const decided = c.disposition !== "pending";

      const handoff = c.verdict === "contested"
        ? `<div class="handoff">
             <span class="eyebrow">Sources disagree — the crew will not pick a side</span>
             ${longText("", c.handoff, false)}
             <p class="routed">Routed to <strong>${esc(ROUTED_TO)}</strong> for a human ruling.</p>
           </div>`
        : "";

      const rights = c.rights_action
        ? `<div class="handoff"><span class="eyebrow">Clearance — ${esc(c.rights_status)}</span>
             <p>${esc(c.rights_action)}</p></div>`
        : "";

      const bible = c.bible_says
        ? `<div class="handoff"><span class="eyebrow">The bible says</span>
             <p>${esc(c.bible_says)}</p></div>`
        : "";

      // Only claims the Adjudicator actually routed to a human get buttons.
      // Asking for a decision on everything trains people to click through,
      // which is how the one claim that mattered gets waved past.
      const acts = decided
        ? `<div class="decided-mark">
             <span class="eyebrow">${esc(c.disposition.replace(/_/g, " "))}</span>
             <p>${esc(c.rationale || "—")}</p>
           </div>`
        : c.needs_human
          ? `<div class="acts">
               <button class="btn fix" data-act="fixed" data-claim="${c.id}">Fix it</button>
               <button class="btn keep" data-act="keep_deliberate" data-claim="${c.id}">Keep — deliberate</button>
               <button class="btn esc" data-act="escalated" data-claim="${c.id}">Escalate</button>
             </div>
             <div class="rationale" id="r-${c.id}" hidden></div>`
          : `<p class="hint routed-note">${esc(c.escalation_reason || "No decision needed.")}</p>`;

      return `
        <div class="note ${c.verdict || ""}" data-note="${c.id}">
          <div class="note-head">
            <span class="kind">${n} · ${esc(c.kind)}</span>
            <span class="verdict ${c.verdict || ""}">${esc(c.verdict || "pending")}</span>
          </div>
          <div class="claim-text">${esc(c.text)}</div>
          <div class="reasoning">${esc(c.reasoning)}</div>
          ${longText("Precedent", c.precedent, true)}
          ${sourceList(c.sources)}
          ${bible}${rights}${handoff}
          ${acts}
        </div>`;
    })
    .join("");

  $("marginNote").textContent = flagged.length
    ? "One note per flagged span, with its sources and what you decided."
    : "Nothing flagged. Every claim checked out.";

  $("margin").querySelectorAll("[data-note]").forEach((el) => {
    el.onclick = (ev) => { if (!ev.target.closest("button, a, textarea")) select(el.dataset.note); };
  });
  $("margin").querySelectorAll("[data-act]").forEach((b) => {
    b.onclick = () => askThenDecide(b.dataset.claim, b.dataset.act);
  });
}

function select(claimId) {
  selected = selected === claimId ? null : claimId;
  document.querySelectorAll(".span").forEach((el) =>
    el.classList.toggle("selected", el.dataset.claim === selected));
  document.querySelectorAll(".note").forEach((el) =>
    el.classList.toggle("selected", el.dataset.note === selected));
  if (selected) {
    document.querySelector(`.note[data-note="${selected}"]`)
      ?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
  drawBridge();
}

// The bridge: a line from the flagged sentence to the note that judges it.
// Drawn in viewport coordinates against a fixed SVG, so it survives scrolling
// and resizing without any layout maths of its own.
function drawBridge() {
  const svg = $("bridge");
  const path = svg.querySelector("path");
  const span = selected && document.querySelector(`.span[data-claim="${selected}"]`);
  const note = selected && document.querySelector(`.note[data-note="${selected}"]`);

  if (!span || !note || window.innerWidth <= 1180) {
    svg.classList.remove("active");
    return;
  }

  const a = span.getBoundingClientRect();
  const b = note.getBoundingClientRect();
  const x1 = a.right + 2, y1 = a.top + a.height / 2;
  const x2 = b.left - 2,  y2 = b.top + 18;
  // A flat-ish S-curve: it should read as a drawn annotation, not a wire.
  const mid = x1 + (x2 - x1) * 0.55;
  path.setAttribute("d", `M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`);
  svg.classList.add("active");
}

addEventListener("resize", drawBridge);
addEventListener("scroll", drawBridge, true);

function renderLedger() {
  fetch(`/api/scenes/${scene.id}/provenance`)
    .then((r) => r.json())
    .then((rows) => {
      $("ledger").innerHTML = rows
        .map(
          (r) => `<div class="entry">
                    <span class="rev">rev. ${r.revision}${r.disposition ? ` · ${esc(r.disposition.replace(/_/g, " "))}` : ""}</span>
                    <span><span class="what">${esc(r.what_changed)}</span><br>
                          <span class="why">${esc(r.why)}</span></span>
                  </div>`,
        )
        .join("");
    })
    .catch(() => { /* the ledger is a view; a failed read must not break the room */ });
}

// --- decisions --------------------------------------------------------------

// "Keep — deliberate" requires a rationale, so it asks inline rather than in a
// browser prompt: the rationale is the artefact this product exists to produce,
// and it deserves a real field.
function askThenDecide(claimId, disposition) {
  if (busy) return;
  if (disposition === "fixed") return decide(claimId, disposition, "Corrected against the cited sources.");

  const box = $(`r-${claimId}`);
  if (!box) return;
  const keep = disposition === "keep_deliberate";
  box.hidden = false;
  box.innerHTML = `
    <label class="field">
      <span>${keep ? "Why keep it — this goes on the record" : "Who is this going to, and why?"}</span>
      <textarea rows="2" id="rt-${claimId}" placeholder="${keep
        ? "Deliberate anachronism — the scene needs the beat."
        : "Standards desk — contested historiography."}"></textarea>
    </label>
    <div class="acts">
      <button class="btn primary" id="rc-${claimId}">${keep ? "Record it" : "Escalate"}</button>
      <button class="btn" id="rx-${claimId}">Cancel</button>
    </div>`;
  const input = $(`rt-${claimId}`);
  input.focus();
  $(`rx-${claimId}`).onclick = () => { box.hidden = true; box.innerHTML = ""; };
  $(`rc-${claimId}`).onclick = () => {
    const rationale = input.value.trim();
    if (keep && !rationale) { toast("A rationale is required to keep this deliberately.", true); input.focus(); return; }
    decide(claimId, disposition, rationale || `Routed to ${ROUTED_TO}.`);
  };
}

function decide(claimId, disposition, rationale) {
  const q = new URLSearchParams({ claim_id: claimId, disposition, rationale });
  run(`/api/stream/scenes/${scene.id}/decide?${q}`, {
    working: disposition === "fixed"
      ? "Revising the scene, then checking it again — a fix must not introduce a new error."
      : "Recording the decision.",
    onScene: (next) => {
      renderScene(next);
      toast(disposition === "fixed" ? "Scene revised and re-checked." : "Recorded in the ledger.");
    },
  });
}

// --- entry points -----------------------------------------------------------

$("go").onclick = () => {
  const intent = $("intent").value.trim();
  if (!intent) { toast("Give the crew a brief first.", true); $("intent").focus(); return; }
  const q = new URLSearchParams({
    intent,
    setting: $("setting").value.trim(),
    mode: $("mode").value,
    bible: $("bible").value.trim(),
    project: $("setting").value.trim() || "untitled",
  });
  run(`/api/stream/scene?${q}`, {
    working: "Drafting, then checking every claim in it. About half a minute.",
    onScene: renderScene,
  });
};

$("frameBtn").onclick = async () => {
  if (!scene || busy) return;
  const btn = $("frameBtn");
  btn.disabled = true;
  btn.textContent = "Rendering…";
  try {
    const res = await fetch(`/api/scenes/${scene.id}/frame`, { method: "POST" });
    if (!res.ok) throw new Error((await res.json()).detail || "The frame could not be rendered.");
    const { frame } = await res.json();
    $("frameImg").src = frame;
    $("frameWrap").hidden = false;
    btn.hidden = true;
    $("frameImg").scrollIntoView({ block: "nearest", behavior: "smooth" });
  } catch (err) {
    toast(err.message, true);
    btn.disabled = false;
    btn.textContent = "Render the frame";
  }
};

$("demoBtn").onclick = async () => {
  if (busy) return;
  setBusy(true);
  // The sample scene is pinned, so no agent runs for it. Showing a crew list
  // here would imply work that did not happen.
  // The sample scene is pinned, so no agent runs for it. The roster still shows
  // — an empty panel reads as a missing feature — but every row says skipped,
  // never done, because claiming work that did not happen is the one thing this
  // product cannot do.
  resetCrew(CREW, { status: "skipped", detail: "pinned sample — not run", counted: false });
  $("crewHead").textContent = "Sample scene";
  $("crewNote").textContent = "Loading the pinned sample scene.";
  try {
    const res = await fetch("/api/scenes/demo", { method: "POST" });
    if (!res.ok) throw new Error(`Sample scene failed (${res.status})`);
    renderScene(await res.json());
    $("crewHead").textContent = "The crew did not run for this";
    $("crewNote").textContent =
      "Pinned sample with fixed sources, so the loop works without an API key. Give a brief and run the crew to watch it live.";
  } catch (err) {
    toast(err.message, true);
  } finally {
    setBusy(false);
  }
};

// Draw the roster before anything has run, so the pipeline is legible at rest
// and the panel never looks like a feature that failed to load.
resetCrew(CREW, { status: "pending", detail: "", counted: false });

// --- room lighting ----------------------------------------------------------
// Persisted, because a reviewer who chose daylight once meant it. Falls back to
// the operating system's preference on a first visit rather than assuming dark.

function setTheme(name) {
  document.documentElement.dataset.theme = name;
  document.querySelectorAll(".theme-btn").forEach((b) =>
    b.setAttribute("aria-pressed", String(b.dataset.theme === name)));
  try { localStorage.setItem("sceneroom-theme", name); } catch { /* private mode */ }
  drawBridge();
}

document.querySelectorAll(".theme-btn").forEach((b) => {
  b.onclick = () => setTheme(b.dataset.theme);
});

// Night by default, regardless of the operating system's preference: the room
// is the designed state, and a first-time visitor should see it. A saved choice
// always wins, because choosing daylight once meant it.
setTheme(
  (() => {
    try { return localStorage.getItem("sceneroom-theme") || "night"; }
    catch { return "night"; }
  })(),
);

document.querySelectorAll(".example").forEach((b) => {
  b.onclick = () => {
    $("intent").value = b.dataset.intent;
    $("setting").value = b.dataset.setting;
    // Only the bible example ships one; the others must clear it, or a stale
    // bible from a previous click would be checked against the wrong scene.
    $("bible").value = b.dataset.bible || "";
    if (b.dataset.bible) $("bible").closest("details").open = true;
  };
});

// --- recent scenes ----------------------------------------------------------
// The ledger is durable, so work done yesterday — or on another instance — is
// still here. Without this the product forgets everything the moment you
// reload, which is what makes a demo feel like a demo.

async function renderRecent() {
  try {
    const scenes = await (await fetch("/api/scenes")).json();
    const list = scenes.filter((s) => s.text).slice(0, 8);
    $("recentCount").textContent = list.length ? `· ${list.length}` : "";
    $("recentEmpty").hidden = list.length > 0;
    $("recent").innerHTML = list
      .map((s) => {
        const open = s.claims.filter((c) => c.needs_human && c.disposition === "pending").length;
        return `<li><button data-scene="${esc(s.id)}">${esc(s.setting || s.project)}
          <span class="when">${s.claims.length} claims · ${open ? `${open} open` : "all decided"}</span>
        </button></li>`;
      })
      .join("");
    $("recent").querySelectorAll("[data-scene]").forEach((b) => {
      b.onclick = async () => {
        if (busy) return;
        const res = await fetch(`/api/scenes/${b.dataset.scene}`);
        if (res.ok) { resetCrew(CREW, { status: "skipped", detail: "reopened from the ledger", counted: false });
                      $("crewHead").textContent = "Reopened from the ledger";
                      $("crewNote").textContent = "This scene was checked earlier. Its decisions are on the record below.";
                      renderScene(await res.json()); }
      };
    });
  } catch { /* the list is a convenience; never block the room on it */ }
}

renderRecent();

// --- the door ---------------------------------------------------------------
// The gate only appears when the deployment sets an access code. Nothing else
// in the UI knows about it: unlocking sets a cookie the browser sends on every
// later request, including the SSE stream.

async function checkAccess() {
  try {
    const state = await (await fetch("/api/access")).json();
    if (state.required && !state.unlocked) $("gate").hidden = false;
  } catch { /* if this fails the API calls will say so themselves */ }
}

$("gateForm").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const code = $("gateCode").value.trim();
  const err = $("gateError");
  if (!code) return;
  const res = await fetch("/api/access", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  if (res.ok) {
    $("gate").hidden = true;
    err.hidden = true;
  } else {
    err.textContent = "That code was not recognised. Check the submission page.";
    err.hidden = false;
    $("gateCode").select();
  }
});

checkAccess();

// Health drives the Parallel badge. A demo must never pass fixture data off as
// live search, so this is stated in the bar at all times.
fetch("/api/health")
  .then((r) => r.json())
  .then((h) => {
    const pill = $("parallelPill");
    pill.classList.add(h.parallel_live ? "live" : "offline");
    $("parallelText").textContent = h.parallel_live ? "Parallel live" : "Parallel offline — sample sources";
    // The real target, reported by the service — never a hardcoded string that
    // could claim durability the deployment does not have.
    $("ledgerTarget").textContent = h.ledger_target || h.ledger;
  })
  .catch(() => { $("parallelText").textContent = "status unknown"; });
