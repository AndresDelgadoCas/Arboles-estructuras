const state = { selectedId: null, pedigree: null, foundName: null };
const $ = (selector) => document.querySelector(selector);

async function api(url, method = "GET", body) {
  const response = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Ocurrió un error.");
  return data;
}

function showMessage(selector, text, ok = false) {
  const el = $(selector);
  el.textContent = text;
  el.classList.toggle("ok", ok);
}

/* ---------- generic tree drawing (SVG) ---------- */
const NODE_W = 132, NODE_H = 46, GAP_X = 20, GAP_Y = 56;

function drawTree(svg, root, selectedKey, onSelect) {
  svg.innerHTML = "";
  if (!root) {
    svg.setAttribute("width", 300);
    svg.setAttribute("height", 80);
    svg.innerHTML = '<text x="150" y="45" text-anchor="middle" fill="#5c6b61">El árbol está vacío.</text>';
    return;
  }
  let column = 0, maxDepth = 0;
  // In-order layout: each node gets the next free column.
  (function layout(node, depth) {
    if (!node) return;
    layout(node.left, depth + 1);
    node.x = column++ * (NODE_W + GAP_X) + NODE_W / 2 + 10;
    node.y = depth * (NODE_H + GAP_Y) + NODE_H / 2 + 10;
    maxDepth = Math.max(maxDepth, depth);
    layout(node.right, depth + 1);
  })(root, 0);

  const width = column * (NODE_W + GAP_X) + 20;
  const height = (maxDepth + 1) * (NODE_H + GAP_Y) + 10;
  svg.setAttribute("width", width);
  svg.setAttribute("height", height);

  let links = "", nodes = "";
  (function render(node) {
    if (!node) return;
    for (const child of [node.left, node.right]) {
      if (child) {
        const midY = (node.y + child.y) / 2;
        links += `<path class="link" d="M${node.x},${node.y + NODE_H / 2} C${node.x},${midY} ${child.x},${midY} ${child.x},${child.y - NODE_H / 2}"/>`;
      }
    }
    const selected = String(node.id) === String(selectedKey) ? " selected" : "";
    nodes += `<g class="node ${node.side}${selected}" data-id="${node.id}" tabindex="0">
      <rect x="${node.x - NODE_W / 2}" y="${node.y - NODE_H / 2}" width="${NODE_W}" height="${NODE_H}" rx="8"/>
      <text class="t1" x="${node.x}" y="${node.y - 3}">${escapeHtml(node.label)}</text>
      <text class="t2" x="${node.x}" y="${node.y + 13}">${escapeHtml(truncate(node.sub, 22))}</text></g>`;
    render(node.left);
    render(node.right);
  })(root);

  svg.innerHTML = links + nodes;
  svg.querySelectorAll(".node").forEach((g) => {
    g.addEventListener("click", () => onSelect(g.dataset.id));
    g.addEventListener("keydown", (e) => { if (e.key === "Enter") onSelect(g.dataset.id); });
  });
}

const escapeHtml = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const truncate = (s, n) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

/* ---------- tabs ---------- */
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab, .panel").forEach((el) => el.classList.remove("active"));
    tab.classList.add("active");
    $("#" + tab.dataset.tab).classList.add("active");
  });
});

/* ---------- pedigree ---------- */
function findNode(node, id) {
  if (!node) return null;
  if (String(node.id) === String(id)) return node;
  return findNode(node.left, id) || findNode(node.right, id);
}

function renderPedigree(data) {
  state.pedigree = data;
  if (state.selectedId && !findNode(data.tree, state.selectedId)) state.selectedId = null;
  drawTree($("#pedigree-svg"), data.tree, state.selectedId, selectHorse);
  const a = data.analysis;
  $("#p-size").textContent = a.size;
  $("#p-height").textContent = a.height;
  $("#p-pre").textContent = a.preorder.join(" → ");
  $("#p-in").textContent = a.inorder.join(" → ");
  $("#p-post").textContent = a.postorder.join(" → ");
  $("#p-level").textContent = a.level_order.join(" → ");
  $("#p-repeated").innerHTML = a.repeated.length
    ? a.repeated.map((r) => `<li><strong>${escapeHtml(r.name)}</strong> aparece ${r.times} veces (generación ${r.generations.join(" y ")}).</li>`).join("")
    : '<li class="hint">No hay ancestros repetidos.</li>';
  updateSelection();
}

async function selectHorse(id) {
  state.selectedId = id;
  drawTree($("#pedigree-svg"), state.pedigree.tree, id, selectHorse);
  updateSelection();
}

async function updateSelection() {
  const node = state.selectedId && findNode(state.pedigree.tree, state.selectedId);
  if (!node) {
    $("#selected-info").textContent = "Selecciona un caballo en el árbol.";
    $("#p-path").textContent = "Selecciona un caballo.";
    return;
  }
  $("#selected-info").innerHTML = `Seleccionado: <strong>${escapeHtml(node.label)}</strong>`;
  const { path } = await api(`/api/pedigree/${node.id}/path`);
  $("#p-path").textContent = path.join(" → ");
}

async function addAncestor(role) {
  const form = $("#pedigree-form");
  if (!state.selectedId) return showMessage("#pedigree-msg", "Primero selecciona un caballo en el árbol.");
  if (!form.reportValidity()) return;
  try {
    const payload = Object.fromEntries(new FormData(form));
    renderPedigree(await api("/api/pedigree", "POST", { ...payload, parent_id: state.selectedId, role }));
    form.reset();
    showMessage("#pedigree-msg", "Ancestro agregado.", true);
  } catch (err) {
    showMessage("#pedigree-msg", translateError(err.message));
  }
}

$("#add-sire").addEventListener("click", () => addAncestor("sire"));
$("#add-dam").addEventListener("click", () => addAncestor("dam"));
$("#remove-node").addEventListener("click", async () => {
  if (!state.selectedId) return showMessage("#pedigree-msg", "Selecciona el caballo que quieres eliminar.");
  try {
    renderPedigree(await api(`/api/pedigree/${state.selectedId}`, "DELETE"));
    showMessage("#pedigree-msg", "Caballo eliminado.", true);
  } catch (err) {
    showMessage("#pedigree-msg", translateError(err.message));
  }
});
$("#reset-pedigree").addEventListener("click", async () => {
  state.selectedId = null;
  renderPedigree(await api("/api/pedigree/reset", "POST"));
  showMessage("#pedigree-msg", "Ejemplo restaurado.", true);
});

/* Backend messages are in English (code language); show them in Spanish. */
function translateError(message) {
  const known = [
    [/already has a sire/, "Ese caballo ya tiene padre."],
    [/already has a dam/, "Ese caballo ya tiene madre."],
    [/root horse cannot be removed/, "El caballo principal no se puede eliminar."],
    [/already exists with the same points/, "Ese caballo ya está inscrito con los mismos puntos."],
    [/Horse not found/, "No se encontró el caballo."],
  ];
  const match = known.find(([regex]) => regex.test(message));
  return match ? match[1] : message;
}

/* ---------- ranking ---------- */
function renderRanking(data) {
  drawTree($("#ranking-svg"), data.tree, state.foundName, () => {});
  if (state.foundName) {
    document.querySelectorAll("#ranking-svg .node").forEach((g) => {
      if (g.dataset.id === state.foundName) g.classList.add("found");
    });
  }
  $("#r-best").textContent = data.highest || "–";
  $("#r-worst").textContent = data.lowest || "–";
  $("#r-height").textContent = data.height;
  $("#r-table").innerHTML = data.ranking
    .map((r) => `<tr><td>${r.position}</td><td>${escapeHtml(r.name)}</td><td>${r.points}</td><td>${escapeHtml(r.discipline)}</td></tr>`)
    .join("");
}

$("#ranking-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    state.foundName = null;
    renderRanking(await api("/api/ranking", "POST", Object.fromEntries(new FormData(e.target))));
    e.target.reset();
    showMessage("#ranking-msg", "Caballo inscrito.", true);
  } catch (err) {
    showMessage("#ranking-msg", translateError(err.message));
  }
});

$("#search-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = new FormData(e.target).get("name");
  try {
    const horse = await api(`/api/ranking/search?name=${encodeURIComponent(name)}`);
    state.foundName = horse.name;
    renderRanking(await api("/api/ranking"));
    showMessage("#ranking-msg", `${horse.name}: ${horse.points} puntos (${horse.discipline || "sin modalidad"}).`, true);
  } catch (err) {
    showMessage("#ranking-msg", "No se encontró el caballo.");
  }
});

$("#delete-horse").addEventListener("click", async () => {
  const name = $("#search-form [name=name]").value.trim();
  if (!name) return showMessage("#ranking-msg", "Escribe el nombre del caballo que quieres retirar.");
  try {
    state.foundName = null;
    renderRanking(await api(`/api/ranking/${encodeURIComponent(name)}`, "DELETE"));
    showMessage("#ranking-msg", "Caballo retirado del concurso.", true);
  } catch (err) {
    showMessage("#ranking-msg", "No se encontró el caballo.");
  }
});

/* ---------- start ---------- */
(async () => {
  renderPedigree(await api("/api/pedigree"));
  renderRanking(await api("/api/ranking"));
})();
