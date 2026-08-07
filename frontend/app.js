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

const MARKS = { running: "▸", done: "✓", skipped: "–", failed: "✕", pending: "○" };
let crewOrder = [];
const crewState = new Map();

function resetCrew(agents) {
  crewOrder = agents;
  crewState.clear();
  agents.forEach((a) => crewState.set(a, { agent: a, status: "pending", detail: "", ms: 0 }));
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

function renderCrew() {
  if (!crewOrder.length) { $("crew").innerHTML = ""; return; }
  $("crew").innerHTML = crewOrder
    .map((name) => {
      const s = crewState.get(name) || { status: "pending" };
      const time = s.status === "running" ? "" : s.ms ? `${(s.ms / 1000).toFixed(1)}s` : "";
      return `
        <li class="${s.status}">
          <span class="mark">${MARKS[s.status] || "○"}</span>
          <span class="name">${esc(name)}</span>
          <span class="time">${esc(time)}</span>
          ${s.detail ? `<span class="detail">${esc(s.detail)}</span>` : ""}
        </li>`;
    })
    .join("");

  const done = crewOrder.filter((n) => ["done", "skipped"].includes(crewState.get(n)?.status));
  const total = crewOrder.reduce((n, a) => n + (crewState.get(a)?.ms || 0), 0);
  $("runSummary").textContent = done.length === crewOrder.length && total
    ? `· ${(total / 1000).toFixed(1)}s`
    : "";
}

// --- streaming --------------------------------------------------------------

function run(url, { onScene, working }) {
  if (busy) return;
  setBusy(true);
  $("crewNote").textContent = working;
  if (stream) stream.close();
  stream = new EventSource(url);

  stream.addEventListener("crew", (e) => resetCrew(JSON.parse(e.data).agents));
  stream.addEventListener("step", (e) => applyStep(JSON.parse(e.data)));

  stream.addEventListener("scene", (e) => {
    stream.close(); stream = null; setBusy(false);
    $("crewNote").textContent = "Every claim is on the record. Decide what you want to keep.";
    onScene(JSON.parse(e.data));
  });

  stream.addEventListener("error", (e) => {
    stream.close(); stream = null; setBusy(false);
    let message = "The run stopped. Check the service logs.";
    try { message = JSON.parse(e.data).message || message; } catch { /* transport error */ }
    $("crewNote").textContent = "The run stopped before it finished.";
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

  renderScript();
  renderMargin();
  renderLedger();

  // The counter must agree with the Adjudicator, not with a second rule
  // invented in the browser.
  const open = scene.claims.filter((c) => c.needs_human && c.disposition === "pending").length;
  const counter = $("counter");
  counter.textContent = open
    ? `${open} flag${open > 1 ? "s" : ""} need${open > 1 ? "" : "s"} a decision`
    : "every claim is on the record";
  counter.classList.toggle("clear", open === 0);
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
    out += `<span class="span ${h.claim.verdict || ""}${decided ? " decided" : ""}"
                  data-claim="${h.claim.id}">${esc(text.slice(h.start, h.end))}<sup>${h.n}</sup></span>`;
    cursor = h.end;
  }
  out += esc(text.slice(cursor));
  $("script").innerHTML = out || esc(text);

  $("script").querySelectorAll("[data-claim]").forEach((el) => {
    el.onclick = () => select(el.dataset.claim);
  });
}

function sourceList(sources) {
  if (!sources?.length) return "";
  return `<ul class="sources">${sources
    .map(
      (s) => `<li><span>↗</span><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>
              <span class="host">${esc(host(s.url))}</span></li>`,
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
             ${c.handoff ? `<p>${esc(c.handoff)}</p>` : ""}
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
          ${c.precedent ? `<div class="reasoning"><em>${esc(c.precedent)}</em></div>` : ""}
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
}

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

$("demoBtn").onclick = async () => {
  if (busy) return;
  setBusy(true);
  // The sample scene is pinned, so no agent runs for it. Showing a crew list
  // here would imply work that did not happen.
  resetCrew([]);
  $("crewNote").textContent = "Loading the pinned sample scene.";
  try {
    const res = await fetch("/api/scenes/demo", { method: "POST" });
    if (!res.ok) throw new Error(`Sample scene failed (${res.status})`);
    renderScene(await res.json());
    $("crewNote").textContent =
      "Pinned sample scene, checked against fixed sources. Run the crew to see it work live.";
  } catch (err) {
    toast(err.message, true);
  } finally {
    setBusy(false);
  }
};

document.querySelectorAll(".example").forEach((b) => {
  b.onclick = () => {
    $("intent").value = b.dataset.intent;
    $("setting").value = b.dataset.setting;
  };
});

// Health drives the Parallel badge. A demo must never pass fixture data off as
// live search, so this is stated in the bar at all times.
fetch("/api/health")
  .then((r) => r.json())
  .then((h) => {
    const pill = $("parallelPill");
    pill.classList.add(h.parallel_live ? "live" : "offline");
    $("parallelText").textContent = h.parallel_live ? "Parallel live" : "Parallel offline — sample sources";
    $("ledgerTarget").textContent = h.ledger === "bigquery"
      ? "bigquery://sceneroom.claims"
      : "in-memory ledger — set BIGQUERY_DATASET to persist";
  })
  .catch(() => { $("parallelText").textContent = "status unknown"; });
