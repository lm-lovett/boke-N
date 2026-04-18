<script setup>
import { computed, onMounted, reactive } from 'vue';

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8080';
const view = new URLSearchParams(window.location.search).get('view') === 'admin' ? 'admin' : 'h5';

const menus = [
  { key: 'roles', label: '角色管理', endpoint: '/api/admin/roles' },
  { key: 'users', label: '用户管理', endpoint: '/api/admin/users' },
  { key: 'resources', label: '资源管理', endpoint: '/api/admin/resources' },
  { key: 'articles', label: '文章管理', endpoint: '/api/admin/articles' },
  { key: 'bannedWords', label: '违禁词管理', endpoint: '/api/admin/banned-words' },
  { key: 'comments', label: '评论记录管理', endpoint: '/api/admin/comments' }
];

const state = reactive({
  mode: view,
  adminToken: localStorage.getItem('admin_token') || '',
  adminUser: null,
  adminSection: 'roles',
  adminRows: [],
  adminHint: '',
  adminMessage: '',

  h5Token: localStorage.getItem('h5_token') || '',
  h5User: (() => {
    try {
      return JSON.parse(localStorage.getItem('h5_user') || 'null');
    } catch {
      return null;
    }
  })(),
  h5Message: '',
  h5Articles: [],
  h5CurrentDetail: null,
  h5Top10: [],
  weather: null,

  loginForm: { username: '', password: '' },
  registerForm: { username: '', password: '' },
  adminLoginForm: { username: 'admin', password: 'Admin123!' },
  commentText: ''
});

const adminMenuTitle = computed(() => menus.find((m) => m.key === state.adminSection)?.label || '管理');
const isAdminLoggedIn = computed(() => Boolean(state.adminToken));

async function request(path, options = {}, token = '') {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(`${apiBase}${path}`, { ...options, headers });
  const raw = await res.text();
  const payload = raw ? JSON.parse(raw) : null;
  if (!res.ok) {
    throw new Error(payload?.message || '请求失败');
  }
  if (payload && payload.success === false) {
    throw new Error(payload.message || '请求失败');
  }
  return payload?.data;
}

function escapeHtml(text) {
  return String(text ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

function saveH5Session() {
  if (state.h5Token) {
    localStorage.setItem('h5_token', state.h5Token);
  } else {
    localStorage.removeItem('h5_token');
  }
  if (state.h5User) {
    localStorage.setItem('h5_user', JSON.stringify(state.h5User));
  } else {
    localStorage.removeItem('h5_user');
  }
}

function saveAdminSession() {
  if (state.adminToken) {
    localStorage.setItem('admin_token', state.adminToken);
  } else {
    localStorage.removeItem('admin_token');
  }
}

async function adminLogin() {
  const data = await request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(state.adminLoginForm)
  });
  const roles = data.roles || [];
  const isAdmin = roles.some((r) => r.name === 'admin');
  if (!isAdmin) {
    throw new Error('当前账号不是管理员');
  }
  state.adminToken = data.token;
  state.adminUser = data.user;
  saveAdminSession();
  state.adminMessage = '登录成功';
  await loadAdminSection(state.adminSection);
}

function adminLogout() {
  state.adminToken = '';
  state.adminUser = null;
  state.adminRows = [];
  state.adminMessage = '已退出';
  saveAdminSession();
}

async function loadAdminSection(sectionKey) {
  state.adminSection = sectionKey;
  const menu = menus.find((m) => m.key === sectionKey);
  if (!menu) {
    return;
  }
  state.adminRows = await request(menu.endpoint, {}, state.adminToken);
  state.adminHint = '';

  if (sectionKey === 'roles') {
    const resources = await request('/api/admin/resources', {}, state.adminToken);
    state.adminHint = resources.map((r) => `${r.id}:${r.name}`).join(' / ');
  } else if (sectionKey === 'users') {
    const roles = await request('/api/admin/roles', {}, state.adminToken);
    state.adminHint = roles.map((r) => `${r.id}:${r.name}`).join(' / ');
  }
}

function adminFormSubmit(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  let body = {};

  if (state.adminSection === 'roles') {
    body = {
      name: form.get('name'),
      description: form.get('description'),
      resourceIds: String(form.get('resourceIds') || '')
        .split(',')
        .map((v) => Number(v.trim()))
        .filter((v) => Number.isInteger(v) && v > 0)
    };
  } else if (state.adminSection === 'users') {
    body = {
      username: form.get('username'),
      nickname: form.get('nickname'),
      password: form.get('password'),
      roleIds: String(form.get('roleIds') || '')
        .split(',')
        .map((v) => Number(v.trim()))
        .filter((v) => Number.isInteger(v) && v > 0)
    };
  } else if (state.adminSection === 'resources') {
    body = {
      code: form.get('code'),
      name: form.get('name')
    };
  } else if (state.adminSection === 'articles') {
    body = {
      title: form.get('title'),
      summary: form.get('summary'),
      content: form.get('content'),
      author: form.get('author'),
      published: form.get('published') === 'on'
    };
  } else if (state.adminSection === 'bannedWords') {
    body = { word: form.get('word') };
  }

  const menu = menus.find((m) => m.key === state.adminSection);
  if (!menu || state.adminSection === 'comments') {
    return;
  }

  request(menu.endpoint, { method: 'POST', body: JSON.stringify(body) }, state.adminToken)
    .then(async () => {
      state.adminMessage = '保存成功';
      await loadAdminSection(state.adminSection);
      event.target.reset();
    })
    .catch((err) => {
      state.adminMessage = err.message;
    });
}

function adminDelete(id) {
  const menu = menus.find((m) => m.key === state.adminSection);
  if (!menu) {
    return;
  }
  request(`${menu.endpoint}/${id}`, { method: 'DELETE' }, state.adminToken)
    .then(async () => {
      state.adminMessage = '删除成功';
      await loadAdminSection(state.adminSection);
    })
    .catch((err) => {
      state.adminMessage = err.message;
    });
}

async function h5Login() {
  const data = await request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(state.loginForm)
  });
  state.h5Token = data.token;
  state.h5User = data.user;
  state.h5Message = '登录成功，可评论';
  saveH5Session();
}

async function h5Register() {
  await request('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      username: state.registerForm.username,
      nickname: state.registerForm.username,
      password: state.registerForm.password
    })
  });
  state.h5Message = '注册成功，请登录';
}

function h5Logout() {
  state.h5Token = '';
  state.h5User = null;
  saveH5Session();
  state.h5Message = '已退出登录';
}

async function loadArticles() {
  state.h5Articles = await request('/api/articles');
  if (state.h5Articles.length > 0) {
    await loadArticleDetail(state.h5Articles[0].id);
  } else {
    state.h5CurrentDetail = null;
  }
  await loadTop10OrWeather();
}

async function loadArticleDetail(id) {
  state.h5CurrentDetail = await request(`/api/articles/${id}`);
  await loadTop10OrWeather();
}

async function loadTop10OrWeather() {
  state.h5Top10 = await request('/api/articles/top10');
  if (state.h5Top10.length === 0) {
    state.weather = await request('/api/weather?city=上海市');
  } else {
    state.weather = null;
  }
}

async function submitComment() {
  if (!state.h5Token) {
    state.h5Message = '请先登录';
    return;
  }
  if (!state.h5CurrentDetail?.article?.id) {
    state.h5Message = '请先选择文章';
    return;
  }
  await request(
    `/api/articles/${state.h5CurrentDetail.article.id}/comments`,
    {
      method: 'POST',
      body: JSON.stringify({ content: state.commentText })
    },
    state.h5Token
  );
  state.commentText = '';
  state.h5Message = '评论成功';
  await loadArticleDetail(state.h5CurrentDetail.article.id);
}

onMounted(async () => {
  if (state.mode === 'admin') {
    if (!state.adminToken) {
      return;
    }
    try {
      await loadAdminSection(state.adminSection);
    } catch {
      adminLogout();
    }
    return;
  }

  try {
    await loadArticles();
  } catch (err) {
    state.h5Message = err.message;
  }
});
</script>

<template>
  <div class="app-wrap">
    <template v-if="state.mode === 'admin'">
      <header class="app-header">
        <h1>博客后台管理（Vue）</h1>
        <div class="row" style="align-items: center">
          <span class="muted">{{ state.adminUser ? `当前用户：${state.adminUser.username}` : '' }}</span>
          <button class="secondary" @click="adminLogout" v-if="isAdminLoggedIn">退出</button>
        </div>
      </header>

      <main class="layout">
        <aside class="sidebar menu">
          <h2>菜单</h2>
          <button
            v-for="m in menus"
            :key="m.key"
            :class="{ active: state.adminSection === m.key }"
            @click="loadAdminSection(m.key)"
            :disabled="!isAdminLoggedIn"
          >
            {{ m.label }}
          </button>
        </aside>

        <section class="content">
          <div class="card" v-if="!isAdminLoggedIn">
            <h3>管理员登录</h3>
            <form class="form-grid" @submit.prevent="adminLogin">
              <label>用户名 <input v-model="state.adminLoginForm.username" required /></label>
              <label>密码 <input v-model="state.adminLoginForm.password" type="password" required /></label>
              <button type="submit">登录</button>
            </form>
            <p class="muted">默认：admin / Admin123!</p>
          </div>

          <div class="card" v-else>
            <div class="row" style="justify-content: space-between; align-items: center">
              <h3>{{ adminMenuTitle }}</h3>
              <button class="secondary" @click="loadAdminSection(state.adminSection)">刷新</button>
            </div>

            <form class="form-grid" v-if="state.adminSection !== 'comments'" @submit="adminFormSubmit">
              <template v-if="state.adminSection === 'roles'">
                <label>角色名 <input name="name" required /></label>
                <label>描述 <input name="description" /></label>
                <label>资源ID <input name="resourceIds" placeholder="1,2,3" /></label>
              </template>

              <template v-else-if="state.adminSection === 'users'">
                <label>用户名 <input name="username" required /></label>
                <label>昵称 <input name="nickname" /></label>
                <label>密码 <input name="password" type="password" required /></label>
                <label>角色ID <input name="roleIds" placeholder="1,2" /></label>
              </template>

              <template v-else-if="state.adminSection === 'resources'">
                <label>编码 <input name="code" required /></label>
                <label>名称 <input name="name" required /></label>
              </template>

              <template v-else-if="state.adminSection === 'articles'">
                <label>标题 <input name="title" required /></label>
                <label>摘要 <input name="summary" /></label>
                <label>作者 <input name="author" /></label>
                <label>内容 <textarea name="content" rows="5" required></textarea></label>
                <label><input name="published" type="checkbox" checked /> 立即发布</label>
              </template>

              <template v-else-if="state.adminSection === 'bannedWords'">
                <label>违禁词 <input name="word" required /></label>
              </template>

              <button type="submit">新增</button>
              <p class="muted" v-if="state.adminHint">参考：{{ state.adminHint }}</p>
            </form>

            <p class="muted" v-if="state.adminMessage">{{ state.adminMessage }}</p>

            <div class="table-wrap">
              <table>
                <thead>
                  <tr v-if="state.adminSection === 'roles'">
                    <th>ID</th><th>名称</th><th>描述</th><th>资源IDs</th><th>操作</th>
                  </tr>
                  <tr v-else-if="state.adminSection === 'users'">
                    <th>ID</th><th>用户名</th><th>昵称</th><th>角色IDs</th><th>操作</th>
                  </tr>
                  <tr v-else-if="state.adminSection === 'resources'">
                    <th>ID</th><th>编码</th><th>名称</th><th>操作</th>
                  </tr>
                  <tr v-else-if="state.adminSection === 'articles'">
                    <th>ID</th><th>标题</th><th>作者</th><th>浏览</th><th>状态</th><th>操作</th>
                  </tr>
                  <tr v-else-if="state.adminSection === 'bannedWords'">
                    <th>ID</th><th>违禁词</th><th>操作</th>
                  </tr>
                  <tr v-else>
                    <th>ID</th><th>文章ID</th><th>用户</th><th>内容</th><th>时间</th><th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in state.adminRows" :key="row.id">
                    <template v-if="state.adminSection === 'roles'">
                      <td>{{ row.id }}</td><td>{{ row.name }}</td><td>{{ row.description }}</td><td>{{ (row.resourceIds || []).join(',') }}</td>
                    </template>
                    <template v-else-if="state.adminSection === 'users'">
                      <td>{{ row.id }}</td><td>{{ row.username }}</td><td>{{ row.nickname }}</td><td>{{ (row.roleIds || []).join(',') }}</td>
                    </template>
                    <template v-else-if="state.adminSection === 'resources'">
                      <td>{{ row.id }}</td><td>{{ row.code }}</td><td>{{ row.name }}</td>
                    </template>
                    <template v-else-if="state.adminSection === 'articles'">
                      <td>{{ row.id }}</td><td>{{ row.title }}</td><td>{{ row.author }}</td><td>{{ row.views }}</td><td>{{ row.published ? '已发布' : '草稿' }}</td>
                    </template>
                    <template v-else-if="state.adminSection === 'bannedWords'">
                      <td>{{ row.id }}</td><td>{{ row.word }}</td>
                    </template>
                    <template v-else>
                      <td>{{ row.id }}</td><td>{{ row.articleId }}</td><td>{{ row.username }}</td><td>{{ row.content }}</td><td>{{ new Date(row.createdAt).toLocaleString('zh-CN') }}</td>
                    </template>
                    <td><button class="danger" @click="adminDelete(row.id)">删除</button></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </main>
    </template>

    <template v-else>
      <header class="app-header">
        <h1>博客前端 H5（Vue）</h1>
      </header>

      <main class="layout h5-layout">
        <section class="content">
          <div class="card">
            <h3>登录 / 注册（评论需登录）</h3>
            <div class="grid two">
              <label>登录用户名 <input v-model="state.loginForm.username" /></label>
              <label>登录密码 <input v-model="state.loginForm.password" type="password" /></label>
            </div>
            <div class="row">
              <button @click="h5Login">登录</button>
              <button class="secondary" @click="h5Logout">退出</button>
            </div>
            <div class="grid two" style="margin-top: 10px">
              <label>注册用户名 <input v-model="state.registerForm.username" /></label>
              <label>注册密码 <input v-model="state.registerForm.password" type="password" /></label>
            </div>
            <button style="margin-top: 8px" @click="h5Register">注册</button>
            <p class="muted">{{ state.h5User ? `已登录：${state.h5User.username}` : '当前未登录' }}</p>
            <p class="muted" v-if="state.h5Message">{{ state.h5Message }}</p>
            <p class="muted">演示账号：demo / Demo123!</p>
          </div>

          <div class="card">
            <h3>文章列表</h3>
            <div v-if="state.h5Articles.length === 0" class="muted">暂无文章</div>
            <div v-for="article in state.h5Articles" :key="article.id" class="article-item">
              <h4>{{ article.title }}</h4>
              <p class="muted">作者：{{ article.author }} | 浏览：{{ article.views }}</p>
              <p>{{ article.summary }}</p>
              <button @click="loadArticleDetail(article.id)">查看详情</button>
            </div>
          </div>

          <div class="card" v-if="state.h5CurrentDetail">
            <h3>{{ state.h5CurrentDetail.article.title }}</h3>
            <p class="muted">
              作者：{{ state.h5CurrentDetail.article.author }} |
              浏览：{{ state.h5CurrentDetail.article.views }}
            </p>
            <pre class="pre-content">{{ state.h5CurrentDetail.article.content }}</pre>

            <h4>评论</h4>
            <textarea v-model="state.commentText" rows="3" placeholder="登录后可评论"></textarea>
            <button style="margin-top: 8px" @click="submitComment">提交评论</button>
            <div class="comment-list">
              <div class="comment-item" v-for="c in state.h5CurrentDetail.comments" :key="c.id">
                <strong>{{ c.username }}</strong>
                <p>{{ c.content }}</p>
                <p class="muted">{{ new Date(c.createdAt).toLocaleString('zh-CN') }}</p>
              </div>
            </div>
          </div>
        </section>

        <aside class="sidebar">
          <div class="card">
            <h3>浏览量 Top 10</h3>
            <template v-if="state.h5Top10.length > 0">
              <div class="list-row" v-for="(item, idx) in state.h5Top10" :key="item.id">
                <span>{{ idx + 1 }}. {{ item.title }}</span>
                <span class="muted">{{ item.views }}</span>
              </div>
            </template>
            <template v-else>
              <p class="muted">暂无文章热榜</p>
              <div v-if="state.weather">
                <p>{{ state.weather.city }}：{{ state.weather.weather }}</p>
                <p>{{ state.weather.temperature }}，湿度 {{ state.weather.humidity }}</p>
              </div>
            </template>
          </div>
        </aside>
      </main>
    </template>
  </div>
</template>
