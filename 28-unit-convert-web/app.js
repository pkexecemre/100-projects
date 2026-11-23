"use strict";

const CATEGORIES = {
  length: {
    defaults: ["m", "ft"],
    units: {
      m: { label: "Meters", factor: 1 },
      km: { label: "Kilometers", factor: 1000 },
      cm: { label: "Centimeters", factor: 0.01 },
      mm: { label: "Millimeters", factor: 0.001 },
      mi: { label: "Miles", factor: 1609.344 },
      yd: { label: "Yards", factor: 0.9144 },
      ft: { label: "Feet", factor: 0.3048 },
      in: { label: "Inches", factor: 0.0254 }
    }
  },
  weight: {
    defaults: ["kg", "lb"],
    units: {
      kg: { label: "Kilograms", factor: 1 },
      g: { label: "Grams", factor: 0.001 },
      mg: { label: "Milligrams", factor: 0.000001 },
      lb: { label: "Pounds", factor: 0.45359237 },
      oz: { label: "Ounces", factor: 0.028349523125 },
      st: { label: "Stone", factor: 6.35029318 }
    }
  },
  temperature: {
    defaults: ["c", "f"],
    units: {
      c: { label: "Celsius" },
      f: { label: "Fahrenheit" },
      k: { label: "Kelvin" }
    }
  }
};

const UNIT_SYMBOLS = {
  m: "m", km: "km", cm: "cm", mm: "mm", mi: "mi", yd: "yd", ft: "ft", in: "in",
  kg: "kg", g: "g", mg: "mg", lb: "lb", oz: "oz", st: "st",
  c: "C", f: "F", k: "K"
};

const tabs = Array.from(document.querySelectorAll("[data-category]"));
const inputEl = document.getElementById("input-value");
const outputEl = document.getElementById("output-value");
const fromEl = document.getElementById("from-unit");
const toEl = document.getElementById("to-unit");
const swapBtn = document.getElementById("swap");
const formulaEl = document.getElementById("formula");

const lastPairs = {
  length: ["m", "ft"],
  weight: ["kg", "lb"],
  temperature: ["c", "f"]
};

let category = "length";

function formatNumber(value) {
  if (!Number.isFinite(value)) return "";
  const rounded = Number(value.toPrecision(9));
  if (Object.is(rounded, -0)) return "0";
  if (rounded !== 0 && (Math.abs(rounded) >= 1e12 || Math.abs(rounded) < 1e-6)) {
    return rounded.toExponential(4).replace(/\.?0+e/, "e");
  }
  return String(rounded);
}

function toCelsius(value, unit) {
  if (unit === "c") return value;
  if (unit === "f") return (value - 32) * 5 / 9;
  return value - 273.15;
}

function fromCelsius(value, unit) {
  if (unit === "c") return value;
  if (unit === "f") return value * 9 / 5 + 32;
  return value + 273.15;
}

function populate(select, keys, selected) {
  select.textContent = "";
  keys.forEach((key) => {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = CATEGORIES[category].units[key].label;
    select.append(option);
  });
  select.value = selected;
}

function convert() {
  const units = CATEGORIES[category].units;
  const raw = inputEl.value.trim();
  const fromKey = fromEl.value;
  const toKey = toEl.value;
  const fromUnit = units[fromKey];
  const toUnit = units[toKey];

  if (!fromUnit || !toUnit) return;

  if (raw === "") {
    outputEl.value = "";
    formulaEl.textContent = "Enter a value to convert.";
    return;
  }

  const value = Number(raw);
  if (!Number.isFinite(value)) {
    outputEl.value = "";
    formulaEl.textContent = "That is not a valid number.";
    return;
  }

  let result;
  if (category === "temperature") {
    result = fromCelsius(toCelsius(value, fromKey), toKey);
  } else {
    result = value * fromUnit.factor / toUnit.factor;
  }

  outputEl.value = formatNumber(result);
  formulaEl.textContent =
    formatNumber(value) + " " + UNIT_SYMBOLS[fromKey] +
    " = " + outputEl.value + " " + UNIT_SYMBOLS[toKey];
}

function setCategory(next) {
  category = next;

  tabs.forEach((tab) => {
    const active = tab.dataset.category === category;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  });

  const pair = lastPairs[category];
  populate(fromEl, Object.keys(CATEGORIES[category].units), pair[0]);
  populate(toEl, Object.keys(CATEGORIES[category].units), pair[1]);
  convert();
}

function rememberPair() {
  lastPairs[category] = [fromEl.value, toEl.value];
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => {
    setCategory(tab.dataset.category);
  });

  tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;

    event.preventDefault();
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    else if (event.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
    else if (event.key === "Home") next = 0;
    else next = tabs.length - 1;

    setCategory(tabs[next].dataset.category);
    tabs[next].focus();
  });
});

fromEl.addEventListener("change", () => {
  rememberPair();
  convert();
});

toEl.addEventListener("change", () => {
  rememberPair();
  convert();
});

inputEl.addEventListener("input", convert);

swapBtn.addEventListener("click", () => {
  const previousOutput = outputEl.value;
  const previousFrom = fromEl.value;
  fromEl.value = toEl.value;
  toEl.value = previousFrom;

  if (previousOutput !== "") inputEl.value = previousOutput;

  rememberPair();
  convert();
});

setCategory("length");
