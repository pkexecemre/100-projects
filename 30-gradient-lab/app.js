"use strict";

const previewEl = document.getElementById("preview");
const cssOutputEl = document.getElementById("css-output");
const color1El = document.getElementById("color1");
const color2El = document.getElementById("color2");
const color3El = document.getElementById("color3");
const thirdToggle = document.getElementById("use-third");
const angleEl = document.getElementById("angle");
const angleValueEl = document.getElementById("angle-value");
const copyBtn = document.getElementById("copy");
const copyStatusEl = document.getElementById("copy-status");
const randomizeBtn = document.getElementById("randomize");

let copyTimer = 0;

function hslToHex(hue, saturation, lightness) {
  const h = ((hue % 360) + 360) % 360;
  const s = Math.max(0, Math.min(100, saturation)) / 100;
  const l = Math.max(0, Math.min(100, lightness)) / 100;
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

function activeColors() {
  const colors = [color1El.value, color2El.value];
  if (thirdToggle.checked) colors.push(color3El.value);
  return colors;
}

function gradientCss() {
  const colors = activeColors();
  const stops = colors.map((color, index) => {
    const position = Math.round((index / (colors.length - 1)) * 100);
    return color.toLowerCase() + " " + position + "%";
  });
  return "linear-gradient(" + angleEl.value + "deg, " + stops.join(", ") + ")";
}

function update() {
  const css = gradientCss();
  previewEl.style.background = css;
  previewEl.setAttribute("aria-label", "Gradient preview: " + css);
  cssOutputEl.textContent = css;
  angleValueEl.textContent = angleEl.value;

  color3El.disabled = !thirdToggle.checked;
  color3El.closest(".stop").classList.toggle("is-off", !thirdToggle.checked);
}

function fallbackCopy(text) {
  const area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.append(area);
  area.select();
  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch (error) {
    copied = false;
  }
  area.remove();
  return copied;
}

async function copyCss() {
  const text = "background: " + gradientCss() + ";";
  let copied = true;

  try {
    await navigator.clipboard.writeText(text);
  } catch (error) {
    copied = fallbackCopy(text);
  }

  copyBtn.textContent = copied ? "Copied" : "Copy failed";
  copyStatusEl.textContent = copied
    ? "Gradient CSS copied to the clipboard."
    : "Could not copy automatically. Select the CSS text instead.";

  window.clearTimeout(copyTimer);
  copyTimer = window.setTimeout(() => {
    copyBtn.textContent = "Copy CSS";
  }, 1600);
}

function randomize() {
  const base = Math.random() * 360;
  const useWarm = Math.random() < 0.5;
  const hues = useWarm ? [0, 42, 318] : [0, 150, 205];
  const saturation = 58 + Math.random() * 26;

  color1El.value = hslToHex(base + hues[0], saturation, 54);
  color2El.value = hslToHex(base + hues[1], saturation - 6, 48);
  color3El.value = hslToHex(base + hues[2], saturation, 62);
  angleEl.value = String(Math.floor(Math.random() * 24) * 15);
  update();
}

[color1El, color2El, color3El].forEach((input) => {
  input.addEventListener("input", update);
});

thirdToggle.addEventListener("change", update);
angleEl.addEventListener("input", update);
copyBtn.addEventListener("click", copyCss);
randomizeBtn.addEventListener("click", randomize);

update();
