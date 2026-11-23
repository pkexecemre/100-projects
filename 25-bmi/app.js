"use strict";

const heightEl = document.getElementById("height");
const weightEl = document.getElementById("weight");
const heightUnitEl = document.getElementById("height-unit");
const weightUnitEl = document.getElementById("weight-unit");
const formEl = document.getElementById("bmi-form");
const errorEl = document.getElementById("error");
const resultEl = document.getElementById("result");
const valueEl = document.getElementById("bmi-value");
const categoryEl = document.getElementById("bmi-category");
const rangeEl = document.getElementById("healthy-range");
const markerEl = document.getElementById("scale-marker");
const unitMetric = document.getElementById("unit-metric");
const unitImperial = document.getElementById("unit-imperial");

const LIMITS = {
  metric: { minH: 50, maxH: 260, minW: 10, maxW: 500, hUnit: "cm", wUnit: "kg" },
  imperial: { minH: 20, maxH: 102, minW: 22, maxW: 1100, hUnit: "in", wUnit: "lb" }
};

let unit = "metric";

function round1(value) {
  return String(Math.round(value * 10) / 10);
}

function hideResult() {
  resultEl.hidden = true;
}

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
  hideResult();
}

function clearError() {
  errorEl.hidden = true;
  errorEl.textContent = "";
}

function updateUnitFields() {
  const limits = LIMITS[unit];
  heightUnitEl.textContent = limits.hUnit;
  weightUnitEl.textContent = limits.wUnit;
  heightEl.placeholder = unit === "metric" ? "175" : "69";
  weightEl.placeholder = unit === "metric" ? "70" : "154";
  heightEl.setAttribute("aria-label", "Height in " + (unit === "metric" ? "centimetres" : "inches"));
  weightEl.setAttribute("aria-label", "Weight in " + (unit === "metric" ? "kilograms" : "pounds"));
}

function switchUnit(next) {
  if (next === unit) return;

  const height = Number(heightEl.value);
  const weight = Number(weightEl.value);

  if (heightEl.value.trim() && Number.isFinite(height)) {
    heightEl.value = round1(next === "imperial" ? height / 2.54 : height * 2.54);
  }
  if (weightEl.value.trim() && Number.isFinite(weight)) {
    weightEl.value = round1(next === "imperial" ? weight * 2.2046226218 : weight / 2.2046226218);
  }

  unit = next;
  updateUnitFields();
  clearError();
  hideResult();
}

function classify(bmi) {
  if (bmi < 18.5) return { label: "Underweight", key: "under" };
  if (bmi < 25) return { label: "Normal weight", key: "normal" };
  if (bmi < 30) return { label: "Overweight", key: "over" };
  return { label: "Obese", key: "obese" };
}

function calculate() {
  const limits = LIMITS[unit];
  const height = Number(heightEl.value);
  const weight = Number(weightEl.value);

  if (!heightEl.value.trim() || !weightEl.value.trim() || !Number.isFinite(height) || !Number.isFinite(weight)) {
    showError("Enter both a height and a weight.");
    return;
  }

  if (height < limits.minH || height > limits.maxH) {
    showError("Enter a height between " + limits.minH + " and " + limits.maxH + " " + limits.hUnit + ".");
    return;
  }

  if (weight < limits.minW || weight > limits.maxW) {
    showError("Enter a weight between " + limits.minW + " and " + limits.maxW + " " + limits.wUnit + ".");
    return;
  }

  const metres = unit === "metric" ? height / 100 : height * 0.0254;
  const kilograms = unit === "metric" ? weight : weight * 0.45359237;
  const bmi = kilograms / (metres * metres);

  if (!Number.isFinite(bmi) || bmi <= 0) {
    showError("Those values do not produce a valid BMI.");
    return;
  }

  const info = classify(bmi);

  valueEl.textContent = bmi.toFixed(1);
  categoryEl.textContent = info.label;
  categoryEl.className = "badge " + info.key;

  const lowKg = 18.5 * metres * metres;
  const highKg = 24.9 * metres * metres;

  if (unit === "metric") {
    rangeEl.textContent = "Healthy weight for this height: " + lowKg.toFixed(1) + " to " + highKg.toFixed(1) + " kg.";
  } else {
    rangeEl.textContent = "Healthy weight for this height: " + (lowKg * 2.2046226218).toFixed(1) + " to " + (highKg * 2.2046226218).toFixed(1) + " lb.";
  }

  const clamped = Math.min(40, Math.max(14, bmi));
  markerEl.style.left = ((clamped - 14) / 26) * 100 + "%";

  clearError();
  resultEl.hidden = false;
}

formEl.addEventListener("submit", (event) => {
  event.preventDefault();
  calculate();
});

unitMetric.addEventListener("change", () => {
  if (unitMetric.checked) switchUnit("metric");
});

unitImperial.addEventListener("change", () => {
  if (unitImperial.checked) switchUnit("imperial");
});

[heightEl, weightEl].forEach((input) => {
  input.addEventListener("input", () => {
    clearError();
    hideResult();
  });
});

updateUnitFields();
