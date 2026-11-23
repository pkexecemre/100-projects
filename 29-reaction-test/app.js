"use strict";

const MAX_ATTEMPTS = 5;

const arenaEl = document.getElementById("arena");
const arenaLabelEl = document.getElementById("arena-label");
const messageEl = document.getElementById("message");
const startBtn = document.getElementById("start");
const resetBtn = document.getElementById("reset");
const lastEl = document.getElementById("last");
const bestEl = document.getElementById("best");
const averageEl = document.getElementById("average");
const attemptsEl = document.getElementById("attempts");

let phase = "idle";
let times = [];
let waitTimer = 0;
let readyAt = 0;

function setArena(stateName, label, message) {
  arenaEl.dataset.state = stateName;
  arenaLabelEl.textContent = label;
  messageEl.textContent = message;
}

function renderStats() {
  const count = times.length;
  const best = count > 0 ? Math.min.apply(null, times) : null;
  const average = count > 0
    ? Math.round(times.reduce((total, value) => total + value, 0) / count)
    : null;

  bestEl.textContent = best === null ? "--" : String(best);
  averageEl.textContent = average === null ? "--" : String(average);
  attemptsEl.textContent = count + " / " + MAX_ATTEMPTS;
}

function updateStartButton() {
  const busy = phase === "waiting" || phase === "ready";
  const complete = times.length >= MAX_ATTEMPTS;

  startBtn.disabled = busy || complete;
  if (complete) startBtn.textContent = "Round complete";
  else if (times.length > 0) startBtn.textContent = "Next attempt";
  else startBtn.textContent = "Start";
}

function startRound() {
  if (phase === "waiting" || phase === "ready") return;
  if (times.length >= MAX_ATTEMPTS) return;

  window.clearTimeout(waitTimer);
  phase = "waiting";
  setArena("waiting", "Wait for green", "Not yet...");
  updateStartButton();
  arenaEl.focus();

  const delay = 1400 + Math.random() * 2600;
  waitTimer = window.setTimeout(() => {
    if (phase !== "waiting") return;
    phase = "ready";
    readyAt = performance.now();
    setArena("ready", "Click!", "Now!");
  }, delay);
}

function earlyClick() {
  window.clearTimeout(waitTimer);
  phase = "idle";
  setArena("early", "Too soon", "You clicked before green. Press Start to try again.");
  updateStartButton();
}

function recordReaction() {
  const elapsed = Math.max(1, Math.round(performance.now() - readyAt));
  times.push(elapsed);
  phase = "idle";

  lastEl.textContent = String(elapsed);
  renderStats();

  const complete = times.length >= MAX_ATTEMPTS;
  if (complete) {
    setArena("done", elapsed + " ms", "Five attempts done. Best and average are above.");
  } else {
    setArena(
      "result",
      elapsed + " ms",
      "Attempt " + times.length + " of " + MAX_ATTEMPTS + ". Press Start for the next one."
    );
  }
  updateStartButton();

  if (!complete) arenaEl.focus();
}

function resetStats() {
  window.clearTimeout(waitTimer);
  phase = "idle";
  times = [];
  lastEl.textContent = "--";
  renderStats();
  updateStartButton();
  setArena("idle", "Ready when you are", "Click Start, then wait for green.");
}

arenaEl.addEventListener("click", () => {
  if (phase === "waiting") {
    earlyClick();
    return;
  }
  if (phase === "ready") {
    recordReaction();
    return;
  }
  if (times.length >= MAX_ATTEMPTS) {
    setArena("done", "Round complete", "Press Reset stats to run five more.");
    return;
  }
  startRound();
});

startBtn.addEventListener("click", startRound);
resetBtn.addEventListener("click", resetStats);

renderStats();
updateStartButton();
