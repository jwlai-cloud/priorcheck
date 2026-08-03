// Sceneroom — the marked-up page.
//
// The page renders the scene with flagged spans underlined; each flag gets a
// margin note carrying its sources and the three-way decision. Hovering either
// highlights both, so the note and the text it refers to stay connected.

const $ = (id) => document.getElementById(id);

let scene = null;
let busy = false;

// --- status -----------------------------------------------------------------

function setStatus(text, working = false) {
  $("statusText").textContent = text;
  $("status").classList.toggle("working", working);
}

function setError(msg) {
  $("err").innerHTML = msg ? `<div class="err">${esc(msg)}</div>` : "";
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// --- api --------------------------------------------------------------------

async function api(path, opts) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try { detail = (await res.json()).detail || detail; } catch {}
    throw new Error(detail);
  }
  return res.json();
}

// --- rendering --------------------------------------------------------------

// Underline each flagged excerpt where it appears in the scene text. Longest
// excerpts first so a short one nested inside a longer one can't split it.
function renderPage() {
  const rev = scene.revision > 1 ? `Rev. ${scene.revision}` : "First draft";
  const head = `<div class="sluglinerow"><span>${esc(scene.setting || scene.project)}</span>` +
               `<span class="rev">${esc(rev)}</span></div>`;

  const marks = scene.claims
    .filter((c) => c.excerpt && scene.text.includes(c.excerpt))
    .sort((a, b) => b.excerpt.length - a.excerpt.length);

  const taken = [];
  let html = esc(scene.text);

  // Work on the escaped text: escape excerpts the same way so indexes line up.
  for (const c of marks) {
    const needle = esc(c.excerpt);
    const at = html.indexOf(needle);
    if (at === -1) continue;
    if (taken.some(([s, e]) => at < e && at + needle.length > s)) continue; // overlap
    taken.push([at, at + needle.length]);
  }

  // Rebuild with spans, right-to-left so earlier indexes stay valid.
  taken.sort((a, b) => b[0] - a[0]);
  for (const [start, end] of taken) {
    const frag = html.slice(start, end);
    const claim = marks.find((c) => esc(c.excerpt) === frag);
    if (!claim) continue;
    const cls = claim.disposition !== "pending" ? "resolved" : (claim.verdict || "");
    html = html.slice(0, start) +
      `<span class="flagged ${cls}" data-claim="${claim.id}">${frag}</span>` +
      html.slice(end);
  }

  $("page").innerHTML = head + html;
  $("page").querySelectorAll(".flagged").forEach((el) => {
    el.onmouseenter = () => highlight(el.dataset.claim, true);
    el.onmouseleave = () => highlight(el.dataset.claim, false);
    el.onclick = () => {
      const note = document.querySelector(`.note[data-claim="${el.dataset.claim}"]`);
      note?.scrollIntoView({ block: "center", behavior: "smooth" });
    };
  });
}

function highlight(claimId, on) {
  document.querySelectorAll(`[data-claim="${claimId}"]`).forEach((el) =>
    el.classList.toggle("active", on));
}

const VERDICT_LABEL = {
  verified: "verified",
  contradicted: "contradicted",
  contested: "contested",
  unverifiable: "no sources",
};

function renderMargin() {
  const notes = scene.claims.filter(
    (c) => c.verdict !== "verified" || c.disposition !== "pending" || c.kind === "fandom"
  );

  if (!notes.length) {
    $("margin").innerHTML = `<div class="empty">Nothing flagged. Every claim checked out against its sources.</div>`;
    return;
  }

  $("margin").innerHTML = notes.map((c) => {
    const decided = c.disposition !== "pending";
    const cls = decided ? "decided" : (c.verdict || "");

    const sources = c.sources?.length
      ? `<div class="sources">${c.sources.map((s) =>
          `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>`).join("")}</div>`
      : "";

    const precedent = c.precedent
      ? `<div class="precedent"><b>Precedent</b>${esc(c.precedent)}</div>` : "";

    const acts = decided ? "" : `
      <div class="acts">
        <button class="fix"  data-act="fixed"           data-claim="${c.id}">Fix it</button>
        <button class="keep" data-act="keep_deliberate" data-claim="${c.id}">Keep — deliberate</button>
        <button class="esc"  data-act="escalated"       data-claim="${c.id}">Escalate</button>
      </div>`;

    const mark = decided ? `
      <div class="decided-mark">
        <b>${esc(c.disposition.replace(/_/g, " "))}</b>
        ${esc(c.rationale || "—")}
      </div>` : "";

    return `<div class="note ${cls}" data-claim="${c.id}">
      <div class="kind"><span>${esc(c.kind)}</span>
        <span class="verdict">${esc(VERDICT_LABEL[c.verdict] || c.verdict || "")}</span></div>
      <div class="claim">${esc(c.text)}</div>
      <div class="why">${esc(c.reasoning)}</div>
      ${precedent}${sources}${acts}${mark}
    </div>`;
  }).join("");

  $("margin").querySelectorAll("[data-act]").forEach((b) => {
    b.onclick = () => decide(b.dataset.claim, b.dataset.act);
  });
  $("margin").querySelectorAll(".note").forEach((n) => {
    n.onmouseenter = () => highlight(n.dataset.claim, true);
    n.onmouseleave = () => highlight(n.dataset.claim, false);
  });
}

async function renderProvenance() {
  if (!scene) return;
  const entries = await api(`/api/scenes/${scene.id}/provenance`);
  if (!entries.length) return;
  $("provWrap").hidden = false;
  $("prov").innerHTML = entries.map((e) => `
    <li>
      <span class="revno">Rev. ${e.revision}</span>
      <span><div>${esc(e.what_changed)}</div><div class="why">${esc(e.why)}</div></span>
    </li>`).join("");
}

function render() {
  $("slug").textContent = scene
    ? `${scene.setting || scene.project} · ${scene.mode} · ${scene.claims.length} claims`
    : "no scene yet";
  renderPage();
  renderMargin();
  renderProvenance();
}

// --- actions ----------------------------------------------------------------

async function write() {
  const intent = $("intent").value.trim();
  if (!intent || busy) return;
  busy = true; $("go").disabled = true; setError("");
  setStatus("Drafting the scene, then checking every claim in it…", true);
  try {
    scene = await api("/api/scenes", {
      method: "POST",
      body: JSON.stringify({
        intent,
        setting: $("setting").value.trim(),
        mode: $("mode").value,
        project: $("setting").value.trim() || "untitled",
      }),
    });
    const open = scene.claims.filter(
      (c) => ["contradicted", "contested"].includes(c.verdict) && c.disposition === "pending").length;
    setStatus(open
      ? `${open} flag${open > 1 ? "s" : ""} need a decision.`
      : `Checked ${scene.claims.length} claims. Nothing flagged.`);
    render();
  } catch (e) {
    setStatus("Stopped.");
    setError(e.message);
  } finally {
    busy = false; $("go").disabled = false;
  }
}

async function decide(claimId, disposition) {
  if (busy) return;
  let rationale = "";

  if (disposition === "keep_deliberate") {
    rationale = prompt(
      "Keeping this deliberately. Why?\n\n" +
      "This is recorded as an intentional creative choice, with the real fact beside it."
    ) || "";
    if (!rationale.trim()) return;  // required — the rationale is the point
  } else if (disposition === "escalated") {
    rationale = prompt("Escalate to whom, and why?") || "Routed for expert review.";
  } else {
    rationale = "Corrected against the cited sources.";
  }

  busy = true; setError("");
  setStatus(disposition === "fixed"
    ? "Revising the scene, then re-checking it…" : "Recording the decision…", true);
  try {
    scene = await api(`/api/scenes/${scene.id}/decide`, {
      method: "POST",
      body: JSON.stringify({ claim_id: claimId, disposition, rationale }),
    });
    const open = scene.claims.filter(
      (c) => ["contradicted", "contested"].includes(c.verdict) && c.disposition === "pending").length;
    setStatus(open ? `${open} flag${open > 1 ? "s" : ""} still open.` : "Scene is clear. Every claim is on the record.");
    render();
  } catch (e) {
    setStatus("Stopped.");
    setError(e.message);
  } finally {
    busy = false;
  }
}

// --- boot -------------------------------------------------------------------

$("go").onclick = write;

$("demoBtn").onclick = async () => {
  if (busy) return;
  busy = true; setError("");
  setStatus("Loading the sample scene and checking it…", true);
  try {
    scene = await api("/api/scenes/demo", { method: "POST" });
    const open = scene.claims.filter(
      (c) => ["contradicted", "contested"].includes(c.verdict) && c.disposition === "pending").length;
    setStatus(`Sample scene — ${open} flag${open === 1 ? "" : "s"} need a decision.`);
    render();
  } catch (e) { setStatus("Stopped."); setError(e.message); }
  finally { busy = false; }
};
document.querySelectorAll(".example[data-intent]").forEach((b) => {
  b.onclick = () => {
    $("intent").value = b.dataset.intent;
    $("setting").value = b.dataset.setting;
  };
});

api("/api/health").then((h) => {
  const live = h.parallel_live;
  $("live").classList.toggle("on", live);
  $("liveLabel").textContent = live ? "Parallel live" : "Parallel offline — sample sources";
}).catch(() => {
  $("liveLabel").textContent = "backend unreachable";
});
