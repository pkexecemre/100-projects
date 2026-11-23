"use strict";

const STORAGE_KEY = "things-to-do.v1";

const formEl = document.getElementById("todo-form");
const inputEl = document.getElementById("todo-input");
const listEl = document.getElementById("todo-list");
const countEl = document.getElementById("item-count");
const clearBtn = document.getElementById("clear-done");
const todayEl = document.getElementById("today");
const filterButtons = Array.from(document.querySelectorAll("[data-filter]"));

let filter = "all";
let todos = loadTodos();

function loadTodos() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((item) => item && typeof item.text === "string")
      .map((item, index) => ({
        id: typeof item.id === "string" ? item.id : "restored-" + index,
        text: item.text.slice(0, 120),
        done: Boolean(item.done)
      }));
  } catch (error) {
    return [];
  }
}

function saveTodos() {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
  } catch (error) {
    /* Private browsing can block storage; the list still works for this visit. */
  }
}

function makeId() {
  return "task-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 7);
}

function visibleTodos() {
  if (filter === "active") return todos.filter((todo) => !todo.done);
  if (filter === "done") return todos.filter((todo) => todo.done);
  return todos;
}

function render() {
  listEl.textContent = "";

  const items = visibleTodos();
  if (items.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty";
    if (todos.length === 0) empty.textContent = "Nothing here yet. Add your first task above.";
    else if (filter === "active") empty.textContent = "All clear - nothing left to do.";
    else if (filter === "done") empty.textContent = "No completed tasks yet.";
    else empty.textContent = "No tasks yet.";
    listEl.append(empty);
  } else {
    items.forEach((todo) => {
      const li = document.createElement("li");
      li.className = "item" + (todo.done ? " done" : "");

      const label = document.createElement("label");
      label.className = "item-main";

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = todo.done;
      checkbox.dataset.id = todo.id;
      checkbox.setAttribute("aria-label", (todo.done ? "Mark not done: " : "Mark done: ") + todo.text);

      const text = document.createElement("span");
      text.className = "text";
      text.textContent = todo.text;

      label.append(checkbox, text);

      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "delete";
      remove.dataset.action = "delete";
      remove.dataset.id = todo.id;
      remove.textContent = "Delete";
      remove.setAttribute("aria-label", "Delete task: " + todo.text);

      li.append(label, remove);
      listEl.append(li);
    });
  }

  const left = todos.filter((todo) => !todo.done).length;
  countEl.textContent = todos.length === 0
    ? "No tasks"
    : left + " left / " + todos.length + " total";

  clearBtn.disabled = !todos.some((todo) => todo.done);
  filterButtons.forEach((button) => {
    const active = button.dataset.filter === filter;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function addTodo(rawText) {
  const clean = rawText.trim().replace(/\s+/g, " ");
  if (!clean) return;
  todos.unshift({
    id: makeId(),
    text: clean.slice(0, 120),
    done: false
  });
  saveTodos();
  render();
  inputEl.value = "";
  inputEl.focus();
}

formEl.addEventListener("submit", (event) => {
  event.preventDefault();
  addTodo(inputEl.value);
});

listEl.addEventListener("change", (event) => {
  const checkbox = event.target.closest('input[type="checkbox"]');
  if (!checkbox) return;
  const todo = todos.find((item) => item.id === checkbox.dataset.id);
  if (!todo) return;
  todo.done = checkbox.checked;
  saveTodos();
  render();
});

listEl.addEventListener("click", (event) => {
  const button = event.target.closest('button[data-action="delete"]');
  if (!button) return;
  todos = todos.filter((todo) => todo.id !== button.dataset.id);
  saveTodos();
  render();
});

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    filter = button.dataset.filter;
    render();
  });
});

clearBtn.addEventListener("click", () => {
  todos = todos.filter((todo) => !todo.done);
  saveTodos();
  render();
});

todayEl.textContent = new Date().toLocaleDateString(undefined, {
  weekday: "long",
  month: "long",
  day: "numeric"
});

render();
