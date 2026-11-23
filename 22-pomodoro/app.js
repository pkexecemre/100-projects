"use strict";

const WORK_SECONDS = 25 * 60;
const BREAK_SECONDS = 5 * 60;
const RADIUS = 112;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

const cardEl = document.getElementById("timer-card");
const modeEl = document.getElementById("mode");
const timeEl = document.getElementById("time");
const startBtn = document.getElementById("start");
const pauseBtn = document.getElementById("pause");
const resetBtn = document.getElementById("reset");
const sessionEl = document.getElementById("session-count");
const ringEl = document.getElementById("ring-progress");

let phase = "work";
let remaining = WORK_SECONDS;
let running = false;
let endAt = 0;
let sessions = 0;
let timerId = null;

ringEl.style.strokeDasharray = String(CIRCUMFERENCE);
ringEl.style.strokeDashoffset = "0";

function totalSeconds() {
  return phase === "work" ? WORK_SECONDS : BREAK_SECONDS;
}

function formatTime(total) {
  const safe = Math.max(0, total);
  const minutes = Math.floor(safe / 60);
  const seconds = safe % 60;
  return String(minutes).padStart(2, "0") + ":" + String(seconds).padStart(2, "0");
}

function update() {
  const total = totalSeconds();
  timeEl.textContent = formatTime(remaining);
  modeEl.textContent = phase === "work" ? "Focus" : "Break";
  cardEl.dataset.phase = phase;

  const progress = total > 0 ? remaining / total : 0;
  ringEl.style.strokeDashoffset = String(CIRCUMFERENCE * (1 - progress));

  startBtn.disabled = running;
  pauseBtn.disabled = !running;
  sessionEl.textContent = String(sessions);
  document.title = formatTime(remaining) + " - " + (phase === "work" ? "Focus" : "Break");
}

function startTimer() {
  if (running) return;
  if (remaining <= 0) remaining = totalSeconds();
  endAt = Date.now() + remaining * 1000;
  running = true;
  window.clearInterval(timerId);
  timerId = window.setInterval(tick, 200);
  update();
}

function pauseTimer() {
  if (!running) return;
  remaining = Math.max(0, Math.ceil((endAt - Date.now()) / 1000));
  running = false;
  window.clearInterval(timerId);
  update();
}

function resetTimer() {
  running = false;
  window.clearInterval(timerId);
  phase = "work";
  remaining = WORK_SECONDS;
  update();
}

function chime() {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return;

  try {
    const context = new AudioContextClass();
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    const now = context.currentTime;

    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(640, now);
    oscillator.frequency.setValueAtTime(860, now + 0.18);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.18, now + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 1);

    oscillator.connect(gain).connect(context.destination);
    oscillator.start(now);
    oscillator.stop(now + 1.05);
    oscillator.addEventListener("ended", () => context.close());
  } catch (error) {
    /* Audio is optional; the phase change still happens without it. */
  }
}

function finishPhase() {
  running = false;
  window.clearInterval(timerId);

  if (phase === "work") {
    sessions += 1;
    phase = "break";
  } else {
    phase = "work";
  }

  remaining = totalSeconds();
  update();
  chime();
}

function tick() {
  const left = Math.max(0, Math.ceil((endAt - Date.now()) / 1000));
  if (left === remaining) return;

  remaining = left;
  if (left === 0) {
    finishPhase();
    return;
  }
  update();
}

startBtn.addEventListener("click", startTimer);
pauseBtn.addEventListener("click", pauseTimer);
resetBtn.addEventListener("click", resetTimer);

document.addEventListener("keydown", (event) => {
  if (event.code !== "Space" || event.repeat) return;
  if (document.activeElement && document.activeElement.tagName === "BUTTON") return;
  event.preventDefault();
  if (running) pauseTimer();
  else startTimer();
});

update();
