"use strict";

const DURATION = 30;
const PASSAGES = [
  "Small steps taken every day add up to a distance you can see. Start before you feel ready, then keep moving when the path bends.",
  "The best debugger is still a clear head and a short break. Read the error twice, name the assumption, and test one change at a time.",
  "A quiet morning, a warm cup, and a list of three things. Finish the first before you touch the second, and the day stays light.",
  "Practice does not make perfect; practice makes permanent. Slow down enough to notice what your hands are learning to do.",
  "Good interfaces feel obvious after the fact. The work is in removing the small frictions nobody can name until they are gone."
];

const timeEl = document.getElementById("time");
const wpmEl = document.getElementById("wpm");
const accuracyEl = document.getElementById("accuracy");
const passageEl = document.getElementById("passage");
const inputEl = document.getElementById("input");
const startBtn = document.getElementById("start");
const resultEl = document.getElementById("result");

let passage = "";
let charSpans = [];
let started = false;
let finished = false;
let startedAt = 0;
let timerId = null;

function choosePassage() {
  let next = PASSAGES[Math.floor(Math.random() * PASSAGES.length)];
  if (PASSAGES.length > 1 && next === passage) {
    next = PASSAGES[(PASSAGES.indexOf(next) + 1) % PASSAGES.length];
  }
  return next;
}

function renderPassage() {
  passageEl.textContent = "";
  charSpans = [];

  Array.from(passage).forEach((character) => {
    const span = document.createElement("span");
    span.className = "char";
    span.textContent = character;
    passageEl.append(span);
    charSpans.push(span);
  });
}

function paint() {
  const typed = inputEl.value;

  charSpans.forEach((span, index) => {
    const hasTyped = index < typed.length;
    const correct = hasTyped && typed[index] === passage[index];
    span.classList.toggle("correct", correct);
    span.classList.toggle("wrong", hasTyped && !correct);
    span.classList.toggle("current", !finished && !inputEl.disabled && index === typed.length);
  });
}

function computeStats(elapsedSeconds) {
  const typed = inputEl.value;
  let correct = 0;

  for (let index = 0; index < typed.length; index += 1) {
    if (typed[index] === passage[index]) correct += 1;
  }

  const safeElapsed = Math.max(1, elapsedSeconds);
  const minutes = safeElapsed / 60;
  const rawWpm = (correct / 5) / minutes;
  const wpm = Math.min(999, Math.round(rawWpm));
  const accuracy = typed.length > 0 ? Math.round((correct / typed.length) * 100) : 100;

  return { wpm, accuracy, correct, typed: typed.length };
}

function showStats(stats) {
  wpmEl.textContent = String(stats.wpm);
  accuracyEl.textContent = String(stats.accuracy);
}

function prepare(enableInput, pickNewPassage = true) {
  window.clearInterval(timerId);
  started = false;
  finished = false;
  startedAt = 0;
  if (pickNewPassage || !passage) passage = choosePassage();
  inputEl.value = "";
  inputEl.disabled = !enableInput;
  timeEl.textContent = String(DURATION);
  wpmEl.textContent = "0";
  accuracyEl.textContent = "100";
  resultEl.textContent = enableInput
    ? "Type the passage. The clock starts on your first keystroke."
    : "Press Start, then type. The clock starts on your first keystroke.";
  resultEl.classList.remove("done");
  startBtn.textContent = enableInput ? "Restart" : "Start test";
  renderPassage();
  paint();

  if (enableInput) inputEl.focus();
}

function finish(expired) {
  if (finished) return;
  finished = true;
  window.clearInterval(timerId);
  inputEl.disabled = true;

  const elapsed = expired
    ? DURATION
    : Math.min(DURATION, Math.max(0.1, (performance.now() - startedAt) / 1000));
  const stats = computeStats(elapsed);

  timeEl.textContent = String(Math.max(0, Math.ceil(DURATION - elapsed)));
  showStats(stats);
  paint();

  const verdict = stats.wpm >= 60 ? "Fast hands." : stats.wpm >= 35 ? "Solid pace." : "Keep the rhythm.";
  const lead = expired ? "Time. " : "Passage complete. ";
  resultEl.textContent = lead + stats.wpm + " WPM, " + stats.accuracy + "% accuracy. " + verdict;
  resultEl.classList.add("done");
  startBtn.textContent = "Try again";
}

function tick() {
  if (!started || finished) return;

  const elapsed = (performance.now() - startedAt) / 1000;
  const remaining = Math.max(0, DURATION - elapsed);
  timeEl.textContent = String(Math.ceil(remaining));
  showStats(computeStats(elapsed));

  if (remaining <= 0) finish(true);
}

inputEl.addEventListener("input", () => {
  if (finished) return;

  if (!started) {
    started = true;
    startedAt = performance.now();
    timerId = window.setInterval(tick, 100);
  }

  if (inputEl.value.length > passage.length) {
    inputEl.value = inputEl.value.slice(0, passage.length);
  }

  paint();
  showStats(computeStats((performance.now() - startedAt) / 1000));

  if (inputEl.value.length >= passage.length) {
    finish(false);
  }
});

inputEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter") event.preventDefault();
});

inputEl.addEventListener("paste", (event) => {
  event.preventDefault();
});

inputEl.addEventListener("drop", (event) => {
  event.preventDefault();
});

startBtn.addEventListener("click", () => {
  const firstStart = inputEl.disabled && !started && !finished;
  prepare(true, !firstStart);
});

prepare(false);
