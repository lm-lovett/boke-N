const state = {
  token: localStorage.getItem("admin_token") || "",
  user: null,
  currentSection: "roles",
};

const sections = {
  roles: { title: "角色管理", endpoint: "/api/admin/roles" },
  users: { title: "用户管理", endpoint: "/api/admin/users" },
  resources: { title: "资源管理", endpoint: "/api/admin/resources" },
  articles: { title: "文章管理", endpoint: "/api/admin/articles" },
  bannedWords: { title: "违禁词管理", endpoint: "/api/admin/banned-words" },
  comments: { title: "评论记录管理", endpoint: "/api/admin/comments" },
};

const els = {
  userText: document.getElementById("adminCurrentUser"),
  logoutBtn: document.getElementById("adminLogoutBtn"),
  loginPanel: document.getElementById("adminLoginPanel"),
  dataPanel: document.getElementById("adminDataPanel"),
  loginForm: document.getElementById("adminLoginForm"),
  sectionTitle: document.getElementById("sectionTitle"),
  entityForm: document.getElementById("entityForm"),
  tableHead: document.getElementById("tableHead"),
  tableBody: document.getElementById("tableBody"),
  refreshBtn: document.getElementById("refreshBtn"),
  sectionButtons: Array.from(document.querySelectorAll("[data-section]")),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function parseIds(text) {
  return String(text || "")
    .split(",")
    .map((v) => Number(v.trim()))
    .filter((v) => Number.isInteger(v) && v > 0);
}

function setSectionActive(section) {
  state.currentSection = section;
  els.sectionButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.section === section);
  });
}

function setAuthedUI() {
  const authed = Boolean(state.token);
  els.loginPanel.classList.toggle("hidden", authed);
  els.dataPanel.classList.toggle("hidden", !authed);
  els.logoutBtn.classList.toggle("hidden", !authed);
  els.userText.textContent = authed && state.user ? `当前用户：${state.user.username}` : "";
}

async function api(url, options = {}, includeAuth = true) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (includeAuth && state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  const response = await fetch(url, { ...options, headers });
  const raw = await response.text();
  const data = raw ? JSON.parse(raw) : {};
  if (!response.ok) {
    throw new Error(data.message || "请求失败");
  }
  return data;
}

function buildFormHtml(section, extra = {}) {
  if (section === "roles") {
    return `
      <label>角色名<input name="name" required /></label>
      <label>描述<input name="description" /></label>
      <label>资源ID(英文逗号分隔)<input name="resourceIds" placeholder="1,2,3" /></label>
      <div class="muted">资源参考：${extra.resourceHint || "-"}</div>
      <button type="submit">新增角色</button>
    `;
  }
  if (section === "users") {
    return `
      <label>用户名<input name="username" required /></label>
      <label>昵称<input name="nickname" /></label>
      <label>密码<input name="password" type="password" required /></label>
      <label>角色ID(英文逗号分隔)<input name="roleIds" placeholder="1,2" /></label>
      <div class="muted">角色参考：${extra.roleHint || "-"}</div>
      <button type="submit">新增用户</button>
    `;
  }
  if (section === "resources") {
    return `
      <label>资源编码<input name="code" placeholder="article:manage" required /></label>
      <label>资源名称<input name="name" required /></label>
      <button type="submit">新增资源</button>
    `;
  }
  if (section === "articles") {
    return `
      <label>标题<input name="title" required /></label>
      <label>摘要<input name="summary" /></label>
      <label>作者<input name="author" /></label>
      <label>内容<textarea name="content" rows="5" required></textarea></label>
      <label><input name="published" type="checkbox" checked /> 立即发布</label>
      <button type="submit">新增文章</button>
    `;
  }
  if (section === "bannedWords") {
    return `
      <label>违禁词<input name="word" required /></label>
      <button type="submit">新增违禁词</button>
    `;
  }
  return `<div class="muted">评论记录仅支持查看与删除。</div>`;
}

function renderTable(section, list) {
  if (section === "roles") {
    els.tableHead.innerHTML = "<tr><th>ID</th><th>角色名</th><th>描述</th><th>资源IDs</th><th>操作</th></tr>";
    els.tableBody.innerHTML = list
      .map(
        (row) => `
          <tr>
            <td>${row.id}</td>
            <td>${escapeHtml(row.name)}</td>
            <td>${escapeHtml(row.description)}</td>
            <td>${(row.resourceIds || []).join(",")}</td>
            <td><button data-delete-id="${row.id}" class="danger">删除</button></td>
          </tr>
        `
      )
      .join("");
    return;
  }
  if (section === "users") {
    els.tableHead.innerHTML = "<tr><th>ID</th><th>用户名</th><th>昵称</th><th>角色IDs</th><th>操作</th></tr>";
    els.tableBody.innerHTML = list
      .map(
        (row) => `
          <tr>
            <td>${row.id}</td>
            <td>${escapeHtml(row.username)}</td>
            <td>${escapeHtml(row.nickname)}</td>
            <td>${(row.roleIds || []).join(",")}</td>
            <td><button data-delete-id="${row.id}" class="danger">删除</button></td>
          </tr>
        `
      )
      .join("");
    return;
  }
  if (section === "resources") {
    els.tableHead.innerHTML = "<tr><th>ID</th><th>编码</th><th>名称</th><th>操作</th></tr>";
    els.tableBody.innerHTML = list
      .map(
        (row) => `
          <tr>
            <td>${row.id}</td>
            <td>${escapeHtml(row.code)}</td>
            <td>${escapeHtml(row.name)}</td>
            <td><button data-delete-id="${row.id}" class="danger">删除</button></td>
          </tr>
        `
      )
      .join("");
    return;
  }
  if (section === "articles") {
    els.tableHead.innerHTML =
      "<tr><th>ID</th><th>标题</th><th>作者</th><th>浏览量</th><th>状态</th><th>操作</th></tr>";
    els.tableBody.innerHTML = list
      .map(
        (row) => `
          <tr>
            <td>${row.id}</td>
            <td>${escapeHtml(row.title)}</td>
            <td>${escapeHtml(row.author)}</td>
            <td>${row.views || 0}</td>
            <td>${row.published ? "已发布" : "草稿"}</td>
            <td><button data-delete-id="${row.id}" class="danger">删除</button></td>
          </tr>
        `
      )
      .join("");
    return;
  }
  if (section === "bannedWords") {
    els.tableHead.innerHTML = "<tr><th>ID</th><th>词汇</th><th>操作</th></tr>";
    els.tableBody.innerHTML = list
      .map(
        (row) => `
          <tr>
            <td>${row.id}</td>
            <td>${escapeHtml(row.word)}</td>
            <td><button data-delete-id="${row.id}" class="danger">删除</button></td>
          </tr>
        `
      )
      .join("");
    return;
  }
  els.tableHead.innerHTML = "<tr><th>ID</th><th>文章ID</th><th>用户</th><th>内容</th><th>时间</th><th>操作</th></tr>";
  els.tableBody.innerHTML = list
    .map(
      (row) => `
        <tr>
          <td>${row.id}</td>
          <td>${row.articleId}</td>
          <td>${escapeHtml(row.username)}</td>
          <td>${escapeHtml(row.content)}</td>
          <td>${new Date(row.createdAt).toLocaleString("zh-CN")}</td>
          <td><button data-delete-id="${row.id}" class="danger">删除</button></td>
        </tr>
      `
    )
    .join("");
}

async function renderCurrentSection() {
  const section = state.currentSection;
  const config = sections[section];
  els.sectionTitle.textContent = config.title;

  let extra = {};
  if (section === "roles") {
    const resources = await api("/api/admin/resources");
    extra.resourceHint = resources.map((v) => `${v.id}:${v.name}`).join(" / ");
  } else if (section === "users") {
    const roles = await api("/api/admin/roles");
    extra.roleHint = roles.map((v) => `${v.id}:${v.name}`).join(" / ");
  }

  if (section === "comments") {
    els.entityForm.classList.add("hidden");
    els.entityForm.innerHTML = "";
  } else {
    els.entityForm.classList.remove("hidden");
    els.entityForm.innerHTML = buildFormHtml(section, extra);
  }

  const list = await api(config.endpoint);
  renderTable(section, list);
}

async function handleCreate(event) {
  event.preventDefault();
  const section = state.currentSection;
  if (section === "comments") return;

  const form = new FormData(els.entityForm);
  let payload = {};
  if (section === "roles") {
    payload = {
      name: form.get("name"),
      description: form.get("description"),
      resourceIds: parseIds(form.get("resourceIds")),
    };
  } else if (section === "users") {
    payload = {
      username: form.get("username"),
      nickname: form.get("nickname"),
      password: form.get("password"),
      roleIds: parseIds(form.get("roleIds")),
    };
  } else if (section === "resources") {
    payload = {
      code: form.get("code"),
      name: form.get("name"),
    };
  } else if (section === "articles") {
    payload = {
      title: form.get("title"),
      summary: form.get("summary"),
      author: form.get("author"),
      content: form.get("content"),
      published: form.get("published") === "on",
    };
  } else if (section === "bannedWords") {
    payload = { word: form.get("word") };
  }

  await api(sections[section].endpoint, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  await renderCurrentSection();
}

async function handleDelete(event) {
  const target = event.target.closest("[data-delete-id]");
  if (!target) return;
  const id = target.dataset.deleteId;
  await api(`${sections[state.currentSection].endpoint}/${id}`, { method: "DELETE" });
  await renderCurrentSection();
}

async function doLogin(event) {
  event.preventDefault();
  const form = new FormData(els.loginForm);
  const data = await api(
    "/api/auth/login",
    {
      method: "POST",
      body: JSON.stringify({
        username: form.get("username"),
        password: form.get("password"),
      }),
    },
    false
  );
  const isAdmin = (data.roles || []).some((role) => role.name === "admin");
  if (!isAdmin) {
    throw new Error("当前账号没有管理员权限");
  }
  state.token = data.token;
  state.user = data.user;
  localStorage.setItem("admin_token", state.token);
  setAuthedUI();
  await renderCurrentSection();
}

function logout() {
  state.token = "";
  state.user = null;
  localStorage.removeItem("admin_token");
  setAuthedUI();
}

function bindEvents() {
  els.loginForm.addEventListener("submit", async (event) => {
    try {
      await doLogin(event);
    } catch (error) {
      alert(error.message);
    }
  });

  els.logoutBtn.addEventListener("click", logout);
  els.refreshBtn.addEventListener("click", async () => {
    try {
      await renderCurrentSection();
    } catch (error) {
      alert(error.message);
    }
  });

  els.sectionButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      setSectionActive(button.dataset.section);
      try {
        await renderCurrentSection();
      } catch (error) {
        alert(error.message);
      }
    });
  });

  els.entityForm.addEventListener("submit", async (event) => {
    try {
      await handleCreate(event);
    } catch (error) {
      alert(error.message);
    }
  });

  els.tableBody.addEventListener("click", async (event) => {
    try {
      await handleDelete(event);
    } catch (error) {
      alert(error.message);
    }
  });
}

async function tryAutoLogin() {
  if (!state.token) return;
  try {
    const me = await api("/api/admin/users");
    if (!Array.isArray(me)) throw new Error("invalid");
    state.user = { username: "admin" };
    setAuthedUI();
    await renderCurrentSection();
  } catch {
    logout();
  }
}

setSectionActive(state.currentSection);
setAuthedUI();
bindEvents();
tryAutoLogin();
