"use strict";

const STORAGE_KEY = "event-countdown.v1";

const eventNameEl = document.getElementById("event-name");
const targetDateEl = document.getElementById("target-date");
const formEl = document.getElementById("countdown-form");
const titleEl = document.getElementById("event-title");
const daysEl = document.getElementById("days");
const hoursEl = document.getElementById("hours");
const minutesEl = document.getElementById("minutes");
const secondsEl = document.getElementById("seconds");
const messageEl = document.getElementById("message");
const errorEl = document.getElementById("error");

let current = null;
let timerId = null;

function pad2(value) {
  return String(value).padStart(2, "0");
}

function toLocalInput(date) {
  return (
    date.getFullYear() +
    "-" +
    pad2(date.getMonth() + 1) +
    "-" +
    pad2(date.getDate()) +
    "T" +
    pad2(date.getHours()) +
    ":" +
    pad2(date.getMinutes())
  );
}

function nextNewYear() {
  const now = new Date();
  return new Date(now.getFullYear() + 1, 0, 1, 0, 0, 0, 0);
}

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
}

function clearError() {
  errorEl.textContent = "";
  errorEl.hidden = true;
}

function saveEvent() {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
      name: current.name,
      target: current.target.toISOString()
    }));
  } catch (error) {
    /* Storage can be unavailable; the countdown still runs for this visit. */
  }
}

function loadEvent() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed.name !== "string" || typeof parsed.target !== "string") return null;
    const target = new Date(parsed.target);
    if (!Number.isFinite(target.getTime())) return null;
    return { name: parsed.name.slice(0, 40), target };
  } catch (error) {
    return null;
  }
}

function updateClock() {
  if (!current) return;

  const diff = current.target.getTime() - Date.now();
  if (diff <= 0) {
    window.clearInterval(timerId);
    daysEl.textContent = "00";
    hoursEl.textContent = "00";
    minutesEl.textContent = "00";
    secondsEl.textContent = "00";
    messageEl.textContent = current.name + " has arrived.";
    document.title = current.name + " - now";
    return;
  }

  const totalSeconds = Math.floor(diff / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  daysEl.textContent = String(days).padStart(2, "0");
  hoursEl.textContent = pad2(hours);
  minutesEl.textContent = pad2(minutes);
  secondsEl.textContent = pad2(seconds);

  messageEl.textContent = "Counting down to " + current.target.toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }) + ".";

  document.title = days + "d " + pad2(hours) + ":" + pad2(minutes) + ":" + pad2(seconds) + " - " + current.name;
}

function setEvent(name, target, persist) {
  current = { name, target };
  titleEl.textContent = name;
  targetDateEl.value = toLocalInput(target);

  window.clearInterval(timerId);
  if (persist) saveEvent();
  updateClock();

  if (current.target.getTime() > Date.now()) {
    timerId = window.setInterval(updateClock, 250);
  }
}

const saved = loadEvent();
const initial = saved || { name: "New Year", target: nextNewYear() };

eventNameEl.value = initial.name;
targetDateEl.min = toLocalInput(new Date());
setEvent(initial.name, initial.target, false);

formEl.addEventListener("submit", (event) => {
  event.preventDefault();
  clearError();

  const name = eventNameEl.value.trim() || "Untitled event";
  const target = new Date(targetDateEl.value);

  if (!targetDateEl.value || !Number.isFinite(target.getTime())) {
    showError("Pick a date and time for the countdown.");
    return;
  }

  if (target.getTime() <= Date.now()) {
    showError("Pick a date and time in the future.");
    return;
  }

  setEvent(name.slice(0, 40), target, true);
});

[eventNameEl, targetDateEl].forEach((input) => {
  input.addEventListener("input", clearError);
});
