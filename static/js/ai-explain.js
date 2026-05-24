/* ai-explain.js
   Frontend responsibility: open an SSE connection to /api/explain/<module>,
   receive streamed text chunks from Python/Claude, render them into the panel.
   Zero AI logic here — all prompting and model calls are in ai_explainer.py.
*/

// Simple markdown → HTML renderer (bold, bullets, headers only)
function _mdToHtml(text) {
  return text
    .replace(/^### (.+)$/gm, "<h4>$1</h4>")
    .replace(/^## (.+)$/gm, "<h3>$1</h3>")
    .replace(/^# (.+)$/gm, "<h2>$1</h2>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/^(?!<[hul]|<\/[hul]|<p|<\/p)(.+)$/gm, "<p>$1</p>");
}

async function runExplainer(module, data) {
  const panel = document.getElementById("ai-explain-panel");
  const output = document.getElementById("ai-explain-output");
  const btn = document.getElementById("btn-explain");

  if (!panel || !output) return;

  // Show panel, reset content
  panel.style.display = "block";
  output.innerHTML =
    '<div class="ai-explain-loading"><span class="loading-spinner"></span> Claude is analysing the computation…</div>';
  if (btn) {
    btn.disabled = true;
    btn.textContent = "⏳ Thinking…";
  }

  let buffer = "";

  try {
    const res = await fetch(`/api/explain/${module}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      output.innerHTML =
        '<p class="ai-explain-error">Failed to reach the AI explainer.</p>';
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    output.innerHTML = '<div class="ai-explain-text"></div>';
    const textEl = output.querySelector(".ai-explain-text");

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const raw = decoder.decode(value, { stream: true });
      // Parse SSE lines: "data: <json>\n\n"
      for (const line of raw.split("\n")) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6).trim();
        if (payload === "[DONE]") break;
        try {
          const chunk = JSON.parse(payload);
          buffer += chunk;
          // Re-render incrementally
          textEl.innerHTML = _mdToHtml(buffer);
          output.scrollTop = output.scrollHeight;
        } catch {}
      }
    }
  } catch (e) {
    output.innerHTML = `<p class="ai-explain-error">Stream error: ${e.message}</p>`;
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "✦ Explain with AI";
    }
  }
}


