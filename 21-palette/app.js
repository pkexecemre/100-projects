"use strict";

const paletteEl = document.getElementById("palette");
const generateBtn = document.getElementById("generate-btn");
const toastEl = document.getElementById("toast");

const COUNT = 5;

const SCHEMES = [
  { hue: [0, 26, 52, 78, 104], light: [8, -2, 10, -8, 2] },
  { hue: [0, 30, 150, 180, 210], light: [0, 10, -10, 4, 12] },
  { hue: [0, 120, 240, 60, 180], light: [8, -6, 4, -10, 10] },
  { hue: [0, 0, 0, 0, 0], light: [-22, -11, 0, 11, 22] },
  { hue: [0, 44, 168, 212, 300], light: [10, 0, -8, 6, -12] }
];

let colors = Array.from({ length: COUNT }, () => ({ hex: "#cccccc", locked: false }));
let toastTimer = 0;

function rand(min, max) {
  return min + Math.random() * (max - min);
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function hslToHex(hue, sat, light) {
  const h = ((hue % 360) + 360) % 360;
  const s = clamp(sat, 0, 100) / 100;
  const l = clamp(light, 0, 100) / 100;
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = l - c / 2;
  let rgb;

  if (h < 60) rgb = [c, x, 0];
  else if (h < 120) rgb = [x, c, 0];
  else if (h < 180) rgb = [0, c, x];
  else if (h < 240) rgb = [0, x, c];
  else if (h < 300) rgb = [x, 0, c];
  else rgb = [c, 0, x];

  const toHex = (value) => Math.round((value + m) * 255).toString(16).padStart(2, "0");
  return "#" + rgb.map(toHex).join("");
}

function generate() {
  const scheme = SCHEMES[Math.floor(Math.random() * SCHEMES.length)];
  const baseHue = rand(0, 360);
  const baseSat = rand(52, 78);
  const baseLight = rand(42, 58);

  colors = colors.map((color, index) => {
    if (color.locked) return color;
    return {
      hex: hslToHex(
        baseHue + scheme.hue[index] + rand(-6, 6),
        baseSat + rand(-9, 9),
        baseLight + scheme.light[index]
      ),
      locked: false
    };
  });
  render();
}

function render() {
  paletteEl.textContent = "";

  colors.forEach((color, index) => {
    const card = document.createElement("article");
    card.className = "card" + (color.locked ? " is-locked" : "");

    const swatch = document.createElement("button");
    swatch.type = "button";
    swatch.className = "swatch";
    swatch.style.background = color.hex;
    swatch.dataset.action = "copy";
    swatch.dataset.index = String(index);
    swatch.setAttribute("aria-label", "Copy " + color.hex);
    swatch.title = "Copy " + color.hex;

    const meta = document.createElement("div");
    meta.className = "meta";

    const hex = document.createElement("button");
    hex.type = "button";
    hex.className = "hex";
    hex.textContent = color.hex.toUpperCase();
    hex.dataset.action = "copy";
    hex.dataset.index = String(index);
    hex.setAttribute("aria-label", "Copy " + color.hex);

    const lock = document.createElement("button");
    lock.type = "button";
    lock.className = "lock";
    lock.textContent = color.locked ? "Locked" : "Lock";
    lock.dataset.action = "lock";
    lock.dataset.index = String(index);
    lock.setAttribute("aria-pressed", String(color.locked));
    lock.setAttribute("aria-label", (color.locked ? "Unlock " : "Lock ") + color.hex);

    meta.append(hex, lock);
    card.append(swatch, meta);
    paletteEl.append(card);
  });
}

function showToast(message) {
  toastEl.textContent = message;
  toastEl.classList.add("show");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => {
    toastEl.classList.remove("show");
  }, 1600);
}

function fallbackCopy(text) {
  const area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.append(area);
  area.select();
  try {
    document.execCommand("copy");
  } catch (error) {
    showToast("Copy failed - select the hex manually");
  }
  area.remove();
}

async function copyHex(hex) {
  try {
    await navigator.clipboard.writeText(hex);
    showToast("Copied " + hex.toUpperCase());
  } catch (error) {
    fallbackCopy(hex);
    showToast("Copied " + hex.toUpperCase());
  }
}

paletteEl.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;

  const index = Number(button.dataset.index);
  if (!Number.isInteger(index) || !colors[index]) return;

  if (button.dataset.action === "lock") {
    colors[index].locked = !colors[index].locked;
    render();
  } else {
    copyHex(colors[index].hex);
  }
});

generateBtn.addEventListener("click", generate);

document.addEventListener("keydown", (event) => {
  const tag = document.activeElement ? document.activeElement.tagName : "";
  const typing = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
  const onControl = tag === "BUTTON" || tag === "A";

  if (event.code === "Space" && !event.repeat && !typing && !onControl) {
    event.preventDefault();
    generate();
  }
});

generate();
