// slide-forge — vanilla JS presentation editor
// Single source of truth: state object mirrors the Pydantic model.

const state = {
  projects: [],          // [{id, name, slide_count}]
  currentProject: null,  // full Presentation object
  currentSlideIdx: -1,
  dirty: false,
  saving: false,
};

let saveTimer = null;
const SAVE_DELAY = 2000;

// ── API layer ────────────────────────────────────────────────────────────────

const api = {
  async listProjects() {
    const r = await fetch("/api/projects");
    return r.json();
  },
  async createProject(name) {
    const r = await fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    return r.json();
  },
  async getProject(id) {
    const r = await fetch(`/api/projects/${id}`);
    if (!r.ok) return null;
    return r.json();
  },
  async saveProject(pres) {
    const r = await fetch(`/api/projects/${pres.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pres),
    });
    return r.json();
  },
  async deleteProject(id) {
    await fetch(`/api/projects/${id}`, { method: "DELETE" });
  },
  async getLayouts() {
    const r = await fetch("/api/layouts");
    return r.json();
  },
  exportUrl(id) {
    return `/api/projects/${id}/export`;
  },
};

// ── Rendering ────────────────────────────────────────────────────────────────

function renderApp() {
  renderToolbar();
  renderSlideList();
  renderEditor();
}

function renderToolbar() {
  const nameInput = document.getElementById("project-name");
  const indicator = document.getElementById("save-indicator");

  if (state.currentProject) {
    nameInput.value = state.currentProject.name;
    nameInput.disabled = false;
  } else {
    nameInput.value = "";
    nameInput.disabled = true;
  }

  if (!state.currentProject) {
    indicator.textContent = "";
  } else if (state.saving) {
    indicator.textContent = "Saving...";
  } else if (state.dirty) {
    indicator.textContent = "Unsaved";
  } else {
    indicator.textContent = "Saved";
  }
}

function renderSlideList() {
  const list = document.getElementById("slide-list");
  list.innerHTML = "";

  if (!state.currentProject) return;

  state.currentProject.slides.forEach((slide, idx) => {
    const div = document.createElement("div");
    div.className = "slide-thumb" + (idx === state.currentSlideIdx ? " selected" : "");
    div.draggable = true;
    div.dataset.idx = idx;

    const titleText = slide.title || "(untitled)";
    const layoutShort = slide.layout.replace("SP_", "");

    div.innerHTML = `
      <span class="drag-handle" title="Drag to reorder">&#x2807;</span>
      <span class="slide-num">${idx + 1}</span>
      <span class="slide-title">${escHtml(titleText)}</span>
      <span class="slide-layout-tag">${layoutShort}</span>
    `;

    div.addEventListener("click", () => selectSlide(idx));

    // Drag-and-drop
    div.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", String(idx));
      e.dataTransfer.effectAllowed = "move";
    });
    div.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      div.classList.add("drag-over");
    });
    div.addEventListener("dragleave", () => div.classList.remove("drag-over"));
    div.addEventListener("drop", (e) => {
      e.preventDefault();
      div.classList.remove("drag-over");
      const fromIdx = parseInt(e.dataTransfer.getData("text/plain"), 10);
      const toIdx = idx;
      if (fromIdx !== toIdx) moveSlide(fromIdx, toIdx);
    });

    list.appendChild(div);
  });
}

function renderEditor() {
  const empty = document.getElementById("editor-empty");
  const form = document.getElementById("editor-form");
  const bodyGroup = document.getElementById("body-group");

  const slide = currentSlide();

  if (!slide) {
    empty.classList.remove("hidden");
    form.classList.add("hidden");
    return;
  }

  empty.classList.add("hidden");
  form.classList.remove("hidden");

  document.getElementById("layout-select").value = slide.layout;
  document.getElementById("slide-title").value = slide.title;
  document.getElementById("slide-notes").value = slide.notes;

  // Hide body for SectionBreak
  if (slide.layout === "SP_SectionBreak") {
    bodyGroup.classList.add("hidden");
  } else {
    bodyGroup.classList.remove("hidden");
    renderBulletList();
  }
}

// ── Bullet list rendering ────────────────────────────────────────────────────

function getBullets() {
  const slide = currentSlide();
  if (!slide) return [];
  // null/undefined → no bullets yet; empty string → one empty bullet
  if (slide.body == null) return [];
  return slide.body.split("\n");
}

function setBullets(bullets) {
  const slide = currentSlide();
  if (!slide) return;
  // Filter out trailing empty bullets to keep the model clean,
  // but always keep at least one if the user is actively editing.
  slide.body = bullets.join("\n");
  markDirty();
}

function renderBulletList() {
  const container = document.getElementById("bullet-list");
  const bullets = getBullets();
  container.innerHTML = "";

  bullets.forEach((text, idx) => {
    const row = document.createElement("div");
    row.className = "bullet-row";
    row.draggable = true;
    row.dataset.idx = idx;

    const drag = document.createElement("span");
    drag.className = "bullet-drag";
    drag.textContent = "\u2807";
    drag.title = "Drag to reorder";

    const input = document.createElement("input");
    input.type = "text";
    input.value = text;
    input.placeholder = `Bullet ${idx + 1}`;
    input.addEventListener("input", () => {
      const b = getBullets();
      b[idx] = input.value;
      setBullets(b);
    });
    // Enter → add new bullet below, Backspace on empty → remove
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        insertBulletAt(idx + 1);
      } else if (e.key === "Backspace" && input.value === "" && bullets.length > 1) {
        e.preventDefault();
        removeBulletAt(idx);
      } else if (e.key === "ArrowDown" && idx < bullets.length - 1) {
        e.preventDefault();
        focusBulletInput(idx + 1);
      } else if (e.key === "ArrowUp" && idx > 0) {
        e.preventDefault();
        focusBulletInput(idx - 1);
      }
    });

    const removeBtn = document.createElement("button");
    removeBtn.className = "bullet-remove";
    removeBtn.innerHTML = "&times;";
    removeBtn.title = "Remove bullet";
    removeBtn.addEventListener("click", () => removeBulletAt(idx));

    // Drag-and-drop for bullet reorder
    row.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", String(idx));
      e.dataTransfer.effectAllowed = "move";
    });
    row.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      row.classList.add("drag-over");
    });
    row.addEventListener("dragleave", () => row.classList.remove("drag-over"));
    row.addEventListener("drop", (e) => {
      e.preventDefault();
      row.classList.remove("drag-over");
      const fromIdx = parseInt(e.dataTransfer.getData("text/plain"), 10);
      if (fromIdx !== idx) moveBullet(fromIdx, idx);
    });

    row.appendChild(drag);
    row.appendChild(input);
    row.appendChild(removeBtn);
    container.appendChild(row);
  });

  // If no bullets yet, seed one empty bullet without re-rendering
  if (bullets.length === 0) {
    const slide = currentSlide();
    if (slide) {
      slide.body = "";
      markDirty();
      renderBulletList();
    }
  }
}

function insertBulletAt(idx) {
  const b = getBullets();
  b.splice(idx, 0, "");
  setBullets(b);
  renderBulletList();
  focusBulletInput(idx);
}

function removeBulletAt(idx) {
  const b = getBullets();
  b.splice(idx, 1);
  setBullets(b);
  renderBulletList();
  // Focus the previous bullet, or the first one
  const focusIdx = Math.min(idx, b.length - 1);
  if (focusIdx >= 0) focusBulletInput(focusIdx);
}

function moveBullet(fromIdx, toIdx) {
  const b = getBullets();
  const [moved] = b.splice(fromIdx, 1);
  b.splice(toIdx, 0, moved);
  setBullets(b);
  renderBulletList();
  focusBulletInput(toIdx);
}

function addBullet() {
  const b = getBullets();
  b.push("");
  setBullets(b);
  renderBulletList();
  focusBulletInput(b.length - 1);
}

function focusBulletInput(idx) {
  const rows = document.querySelectorAll("#bullet-list .bullet-row input");
  if (rows[idx]) rows[idx].focus();
}

// ── State mutations ──────────────────────────────────────────────────────────

function currentSlide() {
  if (!state.currentProject || state.currentSlideIdx < 0) return null;
  return state.currentProject.slides[state.currentSlideIdx] || null;
}

function selectSlide(idx) {
  state.currentSlideIdx = idx;
  renderApp();
}

function markDirty() {
  state.dirty = true;
  renderToolbar();
  scheduleSave();
}

function scheduleSave() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => saveProject(), SAVE_DELAY);
}

async function saveProject() {
  if (!state.currentProject || !state.dirty) return;
  state.saving = true;
  renderToolbar();

  try {
    await api.saveProject(state.currentProject);
    state.dirty = false;
  } catch (e) {
    console.error("Save failed:", e);
  }

  state.saving = false;
  renderToolbar();
}

async function createProject() {
  const name = prompt("Presentation name:", "Untitled");
  if (!name) return;

  const pres = await api.createProject(name);
  state.currentProject = pres;
  state.currentSlideIdx = -1;
  state.dirty = false;
  renderApp();
}

async function openProjectModal() {
  state.projects = await api.listProjects();
  const overlay = document.getElementById("modal-overlay");
  const list = document.getElementById("project-list");

  list.innerHTML = "";
  if (state.projects.length === 0) {
    list.innerHTML = "<p style='color:#888;font-size:14px'>No projects yet.</p>";
  } else {
    state.projects.forEach((p) => {
      const div = document.createElement("div");
      div.className = "project-item";
      div.innerHTML = `
        <div>
          <strong>${escHtml(p.name)}</strong>
          <span class="project-meta">${p.slide_count} slides</span>
        </div>
        <button class="project-delete" data-id="${p.id}" title="Delete project">&times;</button>
      `;
      div.addEventListener("click", (e) => {
        if (e.target.classList.contains("project-delete")) return;
        loadProject(p.id);
        overlay.classList.add("hidden");
      });
      div.querySelector(".project-delete").addEventListener("click", async (e) => {
        e.stopPropagation();
        if (!confirm(`Delete "${p.name}"?`)) return;
        await api.deleteProject(p.id);
        if (state.currentProject && state.currentProject.id === p.id) {
          state.currentProject = null;
          state.currentSlideIdx = -1;
          renderApp();
        }
        openProjectModal(); // refresh list
      });
      list.appendChild(div);
    });
  }

  overlay.classList.remove("hidden");
}

async function loadProject(id) {
  // Save current project first if dirty
  if (state.dirty && state.currentProject) {
    await saveProject();
  }

  const pres = await api.getProject(id);
  if (!pres) {
    alert("Project not found.");
    return;
  }
  state.currentProject = pres;
  state.currentSlideIdx = pres.slides.length > 0 ? 0 : -1;
  state.dirty = false;
  renderApp();
}

function addSlide() {
  if (!state.currentProject) return;
  const slide = {
    id: randomId(),
    layout: "SP_Content",
    title: "",
    body: "",
    notes: "",
  };
  const insertAt = state.currentSlideIdx >= 0 ? state.currentSlideIdx + 1 : state.currentProject.slides.length;
  state.currentProject.slides.splice(insertAt, 0, slide);
  state.currentSlideIdx = insertAt;
  markDirty();
  renderApp();
  document.getElementById("slide-title").focus();
}

function duplicateSlide() {
  const slide = currentSlide();
  if (!slide) return;
  const copy = { ...slide, id: randomId() };
  state.currentProject.slides.splice(state.currentSlideIdx + 1, 0, copy);
  state.currentSlideIdx += 1;
  markDirty();
  renderApp();
}

function deleteSlide() {
  if (!currentSlide()) return;
  if (!confirm("Delete this slide?")) return;
  state.currentProject.slides.splice(state.currentSlideIdx, 1);
  if (state.currentSlideIdx >= state.currentProject.slides.length) {
    state.currentSlideIdx = state.currentProject.slides.length - 1;
  }
  markDirty();
  renderApp();
}

function moveSlide(fromIdx, toIdx) {
  const slides = state.currentProject.slides;
  const [moved] = slides.splice(fromIdx, 1);
  slides.splice(toIdx, 0, moved);

  // Update selection to follow the moved slide
  if (state.currentSlideIdx === fromIdx) {
    state.currentSlideIdx = toIdx;
  } else if (fromIdx < state.currentSlideIdx && toIdx >= state.currentSlideIdx) {
    state.currentSlideIdx -= 1;
  } else if (fromIdx > state.currentSlideIdx && toIdx <= state.currentSlideIdx) {
    state.currentSlideIdx += 1;
  }

  markDirty();
  renderApp();
}

function moveSlideUp() {
  if (state.currentSlideIdx <= 0) return;
  moveSlide(state.currentSlideIdx, state.currentSlideIdx - 1);
}

function moveSlideDown() {
  if (!state.currentProject) return;
  if (state.currentSlideIdx >= state.currentProject.slides.length - 1) return;
  moveSlide(state.currentSlideIdx, state.currentSlideIdx + 1);
}

async function exportPptx() {
  if (!state.currentProject) return;
  // Save first
  if (state.dirty) await saveProject();
  window.open(api.exportUrl(state.currentProject.id), "_blank");
}

async function approveProject() {
  if (!state.currentProject) return;
  if (state.dirty) await saveProject();
  await fetch(`/api/projects/${state.currentProject.id}/approve`, { method: "POST" });
  const btn = document.getElementById("btn-approve");
  btn.textContent = "Gesendet \u2713";
  btn.disabled = true;
}

// ── Editor field handlers ────────────────────────────────────────────────────

function onLayoutChange(e) {
  const slide = currentSlide();
  if (!slide) return;
  slide.layout = e.target.value;
  markDirty();
  renderEditor(); // update body visibility
}

function onTitleChange(e) {
  const slide = currentSlide();
  if (!slide) return;
  slide.title = e.target.value;
  markDirty();
  renderSlideList(); // update sidebar preview
}

function onNotesChange(e) {
  const slide = currentSlide();
  if (!slide) return;
  slide.notes = e.target.value;
  markDirty();
}

function onProjectNameChange(e) {
  if (!state.currentProject) return;
  state.currentProject.name = e.target.value;
  markDirty();
}

// ── Keyboard shortcuts ──────────────────────────────────────────────────────

function handleKeyboard(e) {
  const ctrl = e.ctrlKey || e.metaKey;

  if (ctrl && e.key === "s") {
    e.preventDefault();
    saveProject();
  } else if (ctrl && e.key === "n") {
    e.preventDefault();
    addSlide();
  } else if (ctrl && e.key === "d") {
    e.preventDefault();
    duplicateSlide();
  } else if (ctrl && e.key === "Enter") {
    e.preventDefault();
    exportPptx();
  } else if (e.altKey && e.key === "ArrowUp") {
    e.preventDefault();
    moveSlideUp();
  } else if (e.altKey && e.key === "ArrowDown") {
    e.preventDefault();
    moveSlideDown();
  }
}

// ── Utilities ────────────────────────────────────────────────────────────────

function randomId() {
  return Math.random().toString(36).substring(2, 10);
}

function escHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ── Populate layout dropdown ─────────────────────────────────────────────────

const LAYOUT_LABELS = {
  SP_Title: "Title — opening slide",
  SP_Content: "Content — bullets / prose",
  SP_Intro: "Intro — section opener",
  SP_Closing: "Closing — summary",
  SP_Sources: "Sources — references",
  SP_SectionBreak: "Section Break — divider (title only)",
  SP_Code: "Code — monospace content",
};

async function populateLayouts() {
  const select = document.getElementById("layout-select");
  let layouts;
  try {
    layouts = await api.getLayouts();
  } catch {
    layouts = Object.keys(LAYOUT_LABELS);
  }
  select.innerHTML = "";
  layouts.forEach((l) => {
    const opt = document.createElement("option");
    opt.value = l;
    opt.textContent = LAYOUT_LABELS[l] || l;
    select.appendChild(opt);
  });
}

// ── Init ─────────────────────────────────────────────────────────────────────

async function init() {
  await populateLayouts();

  // Wire up toolbar buttons
  document.getElementById("btn-new-project").addEventListener("click", createProject);
  document.getElementById("btn-open").addEventListener("click", openProjectModal);
  document.getElementById("btn-save").addEventListener("click", () => saveProject());
  document.getElementById("btn-export").addEventListener("click", exportPptx);
  document.getElementById("btn-approve").addEventListener("click", approveProject);
  document.getElementById("btn-add-slide").addEventListener("click", addSlide);
  document.getElementById("btn-dup-slide").addEventListener("click", duplicateSlide);
  document.getElementById("btn-del-slide").addEventListener("click", deleteSlide);
  document.getElementById("btn-modal-close").addEventListener("click", () => {
    document.getElementById("modal-overlay").classList.add("hidden");
  });

  // Wire up editor fields
  document.getElementById("layout-select").addEventListener("change", onLayoutChange);
  document.getElementById("slide-title").addEventListener("input", onTitleChange);
  document.getElementById("slide-notes").addEventListener("input", onNotesChange);
  document.getElementById("project-name").addEventListener("input", onProjectNameChange);
  document.getElementById("btn-add-bullet").addEventListener("click", addBullet);

  // Keyboard shortcuts
  document.addEventListener("keydown", handleKeyboard);

  // Close modal on overlay click
  document.getElementById("modal-overlay").addEventListener("click", (e) => {
    if (e.target.id === "modal-overlay") {
      e.target.classList.add("hidden");
    }
  });

  // Auto-load project from URL hash (e.g. #project=<id>)
  const hashMatch = location.hash.match(/project=([^&]+)/);
  if (hashMatch) {
    await loadProject(hashMatch[1]);
  }

  renderApp();
}

init();
