"use strict";

const editorEl = document.getElementById("editor");
const previewEl = document.getElementById("preview");
const charCountEl = document.getElementById("char-count");

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (character) => {
    if (character === "&") return "&amp;";
    if (character === "<") return "&lt;";
    if (character === ">") return "&gt;";
    if (character === '"') return "&quot;";
    return "&#39;";
  });
}

function renderInline(raw) {
  let text = escapeHtml(raw);
  const codeSlots = [];

  text = text.replace(/`([^`]+)`/g, (match, code) => {
    codeSlots.push("<code>" + code + "</code>");
    return "\u0000" + (codeSlots.length - 1) + "\u0000";
  });

  text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  text = text.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");
  text = text.replace(/(^|[^_])_([^_\n]+)_/g, "$1<em>$2</em>");

  text = text.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (match, label, url) => {
    const isSafe = /^(https?:\/\/|mailto:|#|\/)/i.test(url);
    if (!isSafe) return label;
    return '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + label + "</a>";
  });

  return text.replace(/\u0000(\d+)\u0000/g, (match, index) => codeSlots[Number(index)]);
}

function renderMarkdown(source) {
  const lines = source.replace(/\r\n?/g, "\n").split("\n");
  const html = [];
  let inCode = false;
  let codeLines = [];
  let listType = "";
  let paragraph = [];

  const flushParagraph = () => {
    if (paragraph.length) {
      html.push("<p>" + renderInline(paragraph.join(" ")) + "</p>");
      paragraph = [];
    }
  };

  const closeList = () => {
    if (listType) {
      html.push("</" + listType + ">");
      listType = "";
    }
  };

  const closeBlocks = () => {
    flushParagraph();
    closeList();
  };

  lines.forEach((line) => {
    if (inCode) {
      if (line.trim().startsWith("```")) {
        html.push("<pre><code>" + codeLines.map(escapeHtml).join("\n") + "</code></pre>");
        inCode = false;
        codeLines = [];
      } else {
        codeLines.push(line);
      }
      return;
    }

    if (line.trim().startsWith("```")) {
      closeBlocks();
      inCode = true;
      codeLines = [];
      return;
    }

    if (line.trim() === "") {
      closeBlocks();
      return;
    }

    const heading = line.match(/^(#{1,3})\s+(.*)$/);
    if (heading) {
      closeBlocks();
      const level = heading[1].length;
      html.push("<h" + level + ">" + renderInline(heading[2]) + "</h" + level + ">");
      return;
    }

    if (/^(---+|\*\*\*+)\s*$/.test(line.trim())) {
      closeBlocks();
      html.push("<hr>");
      return;
    }

    const quote = line.match(/^>\s?(.*)$/);
    if (quote) {
      closeBlocks();
      html.push("<blockquote>" + renderInline(quote[1]) + "</blockquote>");
      return;
    }

    const unordered = line.match(/^\s*[-*+]\s+(.*)$/);
    if (unordered) {
      flushParagraph();
      if (listType !== "ul") {
        closeList();
        html.push("<ul>");
        listType = "ul";
      }
      html.push("<li>" + renderInline(unordered[1]) + "</li>");
      return;
    }

    const ordered = line.match(/^\s*\d+\.\s+(.*)$/);
    if (ordered) {
      flushParagraph();
      if (listType !== "ol") {
        closeList();
        html.push("<ol>");
        listType = "ol";
      }
      html.push("<li>" + renderInline(ordered[1]) + "</li>");
      return;
    }

    closeList();
    paragraph.push(line);
  });

  if (inCode) {
    html.push("<pre><code>" + codeLines.map(escapeHtml).join("\n") + "</code></pre>");
  }
  closeBlocks();

  return html.join("");
}

function update() {
  const source = editorEl.value;
  const html = renderMarkdown(source);

  if (html) {
    previewEl.innerHTML = html;
    previewEl.classList.remove("is-empty");
  } else {
    previewEl.textContent = "Nothing to preview yet.";
    previewEl.classList.add("is-empty");
  }

  const count = source.length;
  charCountEl.textContent = count + (count === 1 ? " char" : " chars");
}

editorEl.addEventListener("input", update);

editorEl.addEventListener("keydown", (event) => {
  if (event.key !== "Tab") return;
  event.preventDefault();
  const start = editorEl.selectionStart;
  const end = editorEl.selectionEnd;
  editorEl.setRangeText("  ", start, end, "end");
  update();
});

update();
