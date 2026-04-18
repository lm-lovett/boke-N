const state = {
  token: localStorage.getItem("h5_token") || "",
  user: (() => {
    try {
      return JSON.parse(localStorage.getItem("h5_user") || "null");
    } catch {
      return null;
    }
  })(),
  articles: [],
  currentArticleId: null,
};

const el = {
  username: document.getElementById("h5-username"),
  password: document.getElementById("h5-password"),
  loginBtn: document.getElementById("h5-login"),
  registerBtn: document.getElementById("h5-register"),
  userState: document.getElementById("h5-user-state"),
  articleList: document.getElementById("article-list"),
  detailCard: document.getElementById("article-detail-card"),
  articleTitle: document.getElementById("article-title"),
  articleMeta: document.getElementById("article-meta"),
  articleContent: document.getElementById("article-content"),
  commentContent: document.getElementById("comment-content"),
  submitComment: document.getElementById("submit-comment"),
  commentList: document.getElementById("comment-list"),
  topArticles: document.getElementById("top-articles"),
  weatherCard: document.getElementById("weather-card"),
  weatherContent: document.getElementById("weather-content"),
};

function htmlEscape(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function saveSession() {
  if (state.token) {
    localStorage.setItem("h5_token", state.token);
  } else {
    localStorage.removeItem("h5_token");
  }
  if (state.user) {
    localStorage.setItem("h5_user", JSON.stringify(state.user));
  } else {
    localStorage.removeItem("h5_user");
  }
}

function renderUserState(message = "") {
  if (state.token && state.user) {
    el.userState.textContent = `已登录：${state.user.nickname || state.user.username}。${message}`;
    return;
  }
  el.userState.textContent = message || "当前未登录";
}

async function request(url, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  const res = await fetch(url, { ...options, headers });
  const text = await res.text();
  const data = text ? JSON.parse(text) : {};
  if (!res.ok) {
    throw new Error(data.message || "请求失败");
  }
  return data;
}

function renderComments(comments = []) {
  if (!comments.length) {
    el.commentList.innerHTML = '<p class="muted">暂无评论，快来抢沙发。</p>';
    return;
  }
  el.commentList.innerHTML = comments
    .map(
      (c) => `
      <div class="comment-item">
        <strong>${htmlEscape(c.username || "匿名用户")}</strong>
        <p>${htmlEscape(c.content)}</p>
        <p class="muted">${new Date(c.createdAt).toLocaleString("zh-CN")}</p>
      </div>
    `
    )
    .join("");
}

async function loadArticleDetail(articleId) {
  const numericId = Number(articleId);
  if (!Number.isInteger(numericId) || numericId <= 0) {
    throw new Error("无效的文章ID");
  }
  const data = await request(`/api/articles/${numericId}`);
  state.currentArticleId = numericId;
  el.detailCard.classList.remove("hidden");
  el.articleTitle.textContent = data.article.title;
  el.articleMeta.textContent = `作者：${data.article.author || "未知"} | 浏览量：${data.article.views}`;
  el.articleContent.textContent = data.article.content;
  renderComments(data.comments);
}

function renderArticleList() {
  if (!state.articles.length) {
    el.articleList.innerHTML = '<p class="muted">当前暂无文章，请稍后查看。</p>';
    el.detailCard.classList.add("hidden");
    return;
  }
  el.articleList.innerHTML = state.articles
    .map(
      (article) => `
      <div class="article-item">
        <h3>${htmlEscape(article.title)}</h3>
        <p class="muted">作者：${htmlEscape(article.author || "未知")} | 浏览量：${article.views}</p>
        <p>${htmlEscape(article.summary || "").slice(0, 80)}</p>
        <button data-article-id="${article.id}">查看详情</button>
      </div>
    `
    )
    .join("");

  el.articleList.querySelectorAll("[data-article-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await loadArticleDetail(Number(btn.dataset.articleId));
        await loadTopOrWeather();
      } catch (error) {
        renderUserState(error.message);
      }
    });
  });
}

async function loadTopOrWeather() {
  const top10 = await request("/api/articles/top10");
  if (top10.length > 0) {
    el.weatherCard.classList.add("hidden");
    el.topArticles.innerHTML = top10
      .map(
        (item, index) => `
        <div class="list-row">
          <span>${index + 1}. ${htmlEscape(item.title)}</span>
          <span class="muted">${item.views} 浏览</span>
        </div>
      `
      )
      .join("");
    return;
  }

  const weather = await request("/api/weather?city=上海市");
  el.topArticles.innerHTML = '<p class="muted">暂无文章热榜。</p>';
  el.weatherCard.classList.remove("hidden");
  el.weatherContent.textContent = `${weather.city}：${weather.weather}，${weather.temperature}，湿度 ${weather.humidity}`;
}

async function loadArticles() {
  state.articles = await request("/api/articles");
  renderArticleList();
  if (state.articles.length) {
    await loadArticleDetail(state.articles[0].id);
  }
  await loadTopOrWeather();
}

async function login() {
  const username = el.username.value.trim();
  const password = el.password.value.trim();
  if (!username || !password) {
    renderUserState("请输入用户名和密码");
    return;
  }
  const data = await request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
    headers: { Authorization: "" },
  });
  state.token = data.token;
  state.user = data.user;
  saveSession();
  renderUserState("登录成功，可以评论了。");
}

async function register() {
  const username = el.username.value.trim();
  const password = el.password.value.trim();
  if (!username || !password) {
    renderUserState("注册需要用户名和密码");
    return;
  }
  await request("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password, nickname: username }),
    headers: { Authorization: "" },
  });
  renderUserState("注册成功，请点击登录。");
}

async function submitComment() {
  if (!state.token) {
    renderUserState("请先登录后再评论");
    return;
  }
  if (!state.currentArticleId) {
    renderUserState("请先选择文章");
    return;
  }
  const content = el.commentContent.value.trim();
  if (!content) {
    renderUserState("评论内容不能为空");
    return;
  }
  await request(`/api/articles/${state.currentArticleId}/comments`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
  el.commentContent.value = "";
  renderUserState("评论成功");
  await loadArticleDetail(state.currentArticleId);
}

function bindEvents() {
  el.loginBtn.addEventListener("click", async () => {
    try {
      await login();
    } catch (error) {
      renderUserState(error.message);
    }
  });

  el.registerBtn.addEventListener("click", async () => {
    try {
      await register();
    } catch (error) {
      renderUserState(error.message);
    }
  });

  el.submitComment.addEventListener("click", async () => {
    try {
      await submitComment();
      await loadTopOrWeather();
    } catch (error) {
      renderUserState(error.message);
    }
  });
}

async function bootstrap() {
  renderUserState();
  bindEvents();
  try {
    await loadArticles();
  } catch (error) {
    renderUserState(error.message);
  }
}

bootstrap();
