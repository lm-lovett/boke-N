<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import {
  BookOpen,
  User,
  LogIn,
  LogOut,
  UserPlus,
  Eye,
  MessageSquare,
  Flame,
  CloudSun,
  ShieldCheck,
  Users,
  KeyRound,
  FileText,
  Ban,
  MessagesSquare,
  RefreshCw,
  X,
  Send,
  LayoutGrid
} from 'lucide-vue-next';

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8080';
const view = new URLSearchParams(window.location.search).get('view') === 'admin' ? 'admin' : 'h5';

const menus = [
  { key: 'roles', label: '角色管理', icon: ShieldCheck, endpoint: '/api/admin/roles' },
  { key: 'users', label: '用户管理', icon: Users, endpoint: '/api/admin/users' },
  { key: 'resources', label: '资源管理', icon: KeyRound, endpoint: '/api/admin/resources' },
  { key: 'articles', label: '文章管理', icon: FileText, endpoint: '/api/admin/articles' },
  { key: 'bannedWords', label: '违禁词管理', icon: Ban, endpoint: '/api/admin/banned-words' },
  { key: 'comments', label: '评论记录管理', icon: MessagesSquare, endpoint: '/api/admin/comments' }
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
  adminLoginForm: { username: '', password: '' },
  commentText: ''
});

const authModal = reactive({
  open: false,
  tab: 'login' // 'login' | 'register'
});

const submitting = ref(false);

function openAuth(tab = 'login') {
  authModal.tab = tab;
  authModal.open = true;
}

function closeAuth() {
  authModal.open = false;
}

const adminMenuTitle = computed(() => menus.find((m) => m.key === state.adminSection)?.label || '管理');
const adminMenuIcon = computed(() => menus.find((m) => m.key === state.adminSection)?.icon || LayoutGrid);
const isAdminLoggedIn = computed(() => Boolean(state.adminToken));
const isH5Admin = computed(() => (state.h5User?.roles || []).some((r) => r.name === 'admin'));

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
  try {
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
  } catch (err) {
    state.adminMessage = err.message;
  }
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
  try {
    const data = await request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(state.loginForm)
    });
    state.h5Token = data.token;
    state.h5User = { ...(data.user || {}), roles: data.roles || [] };
    state.h5Message = '登录成功，可评论';
    saveH5Session();
    authModal.open = false;
  } catch (err) {
    state.h5Message = err.message;
  }
}

async function h5Register() {
  try {
    await request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        username: state.registerForm.username,
        nickname: state.registerForm.username,
        password: state.registerForm.password
      })
    });
    state.h5Message = '注册成功，请登录';
    authModal.tab = 'login';
  } catch (err) {
    state.h5Message = err.message;
  }
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
    authModal.tab = 'login';
    authModal.open = true;
    return;
  }
  if (!state.h5CurrentDetail?.article?.id) {
    state.h5Message = '请先选择文章';
    return;
  }
  try {
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
  } catch (err) {
    state.h5Message = err.message;
  }
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
    <!-- ==================== 后台管理 ==================== -->
    <template v-if="state.mode === 'admin'">
      <header class="app-header">
        <div class="brand">
          <span class="brand-badge"><LayoutGrid :size="16" /></span>
          博客后台管理
        </div>
        <div class="header-actions">
          <a href="/" class="admin-entry">
            <BookOpen :size="14" /> 回到前台
          </a>
          <span class="header-user" v-if="state.adminUser">
            <User :size="14" />
            {{ state.adminUser.username }}
          </span>
          <button class="ghost-dark sm" @click="adminLogout" v-if="isAdminLoggedIn">
            <span class="row" style="gap:6px"><LogOut :size="14" /> 退出</span>
          </button>
        </div>
      </header>

      <main class="layout">
        <aside class="sidebar">
          <nav class="side-nav">
            <h2>管理菜单</h2>
            <button
              v-for="m in menus"
              :key="m.key"
              class="nav-item"
              :class="{ active: state.adminSection === m.key }"
              @click="loadAdminSection(m.key)"
              :disabled="!isAdminLoggedIn"
            >
              <component :is="m.icon" :size="16" />
              {{ m.label }}
            </button>
          </nav>
        </aside>

        <section class="content">
          <!-- 管理员登录 -->
          <div class="card" v-if="!isAdminLoggedIn">
            <h3 class="card-title"><LogIn :size="18" /> 管理员登录</h3>
            <form class="form-grid" @submit.prevent="adminLogin">
              <label>用户名 <input v-model="state.adminLoginForm.username" required /></label>
              <label>密码 <input v-model="state.adminLoginForm.password" type="password" required /></label>
              <div class="form-footer">
                <button type="submit">登录</button>
              </div>
            </form>
          </div>

          <!-- 已登录：当前分区 -->
          <template v-else>
            <div class="page-head">
              <h3 class="card-title" style="margin:0">
                <component :is="adminMenuIcon" :size="18" /> {{ adminMenuTitle }}
              </h3>
              <button class="secondary sm" @click="loadAdminSection(state.adminSection)">
                <span class="row" style="gap:6px"><RefreshCw :size="14" /> 刷新</span>
              </button>
            </div>

            <p class="msg" v-if="state.adminMessage">{{ state.adminMessage }}</p>

            <!-- 新增表单 -->
            <div class="card" v-if="state.adminSection !== 'comments'">
              <h3 class="card-title"><UserPlus :size="18" /> 新增{{ adminMenuTitle }}</h3>
              <form class="form-grid" @submit="adminFormSubmit">
                <div class="grid two" v-if="state.adminSection === 'roles'">
                  <label>角色名 <input name="name" required /></label>
                  <label>描述 <input name="description" /></label>
                  <label>资源ID <input name="resourceIds" placeholder="1,2,3" /></label>
                </div>

                <div class="grid two" v-else-if="state.adminSection === 'users'">
                  <label>用户名 <input name="username" required /></label>
                  <label>昵称 <input name="nickname" /></label>
                  <label>密码 <input name="password" type="password" required /></label>
                  <label>角色ID <input name="roleIds" placeholder="1,2" /></label>
                </div>

                <div class="grid two" v-else-if="state.adminSection === 'resources'">
                  <label>编码 <input name="code" required /></label>
                  <label>名称 <input name="name" required /></label>
                </div>

                <template v-else-if="state.adminSection === 'articles'">
                  <div class="grid two">
                    <label>标题 <input name="title" required /></label>
                    <label>作者 <input name="author" /></label>
                    <label>摘要 <input name="summary" /></label>
                  </div>
                  <label>内容 <textarea name="content" rows="5" required></textarea></label>
                  <div class="form-footer">
                    <label class="row" style="gap:6px; font-weight:400">
                      <input name="published" type="checkbox" checked style="width:auto" /> 立即发布
                    </label>
                  </div>
                </template>

                <label v-else-if="state.adminSection === 'bannedWords'">违禁词 <input name="word" required /></label>

                <div class="form-footer">
                  <button type="submit">新增</button>
                </div>
              </form>
              <p class="hint" v-if="state.adminHint">参考：{{ state.adminHint }}</p>
            </div>

            <!-- 数据表格 -->
            <div class="card">
              <h3 class="card-title"><FileText :size="18" /> {{ adminMenuTitle }}列表</h3>
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
                    <tr v-if="state.adminRows.length === 0">
                      <td class="empty-row" :colspan="6">暂无数据</td>
                    </tr>
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
          </template>
        </section>
      </main>
    </template>

    <!-- ==================== H5 前台 ==================== -->
    <template v-else>
      <header class="app-header">
        <div class="brand">
          <span class="brand-badge"><BookOpen :size="16" /></span>
          博客
        </div>
        <div class="header-actions">
          <template v-if="state.h5User">
            <a v-if="isH5Admin" href="/?view=admin" class="admin-entry">
              <LayoutGrid :size="14" /> 后台管理
            </a>
            <span class="header-user"><User :size="14" /> {{ state.h5User.username }}</span>
            <button class="ghost-dark sm" @click="h5Logout">
              <span class="row" style="gap:6px"><LogOut :size="14" /> 退出</span>
            </button>
          </template>
          <button v-else @click="openAuth('login')">
            <span class="row" style="gap:6px"><LogIn :size="14" /> 登录 / 注册</span>
          </button>
        </div>
      </header>

      <main class="layout h5-layout">
        <div class="h5-main">
          <p class="msg" v-if="state.h5Message">{{ state.h5Message }}</p>

          <!-- 文章详情 -->
          <div class="card" v-if="state.h5CurrentDetail">
            <h3 class="card-title">{{ state.h5CurrentDetail.article.title }}</h3>
            <div class="article-meta">
              <span><User :size="12" /> {{ state.h5CurrentDetail.article.author }}</span>
              <span><Eye :size="12" /> {{ state.h5CurrentDetail.article.views }}</span>
            </div>
            <pre class="pre-content">{{ state.h5CurrentDetail.article.content }}</pre>

            <div class="comment-editor">
              <h4 style="margin:0 0 10px; display:flex; align-items:center; gap:6px">
                <MessageSquare :size="16" style="color: var(--primary)" /> 评论
              </h4>
              <textarea v-model="state.commentText" rows="3" placeholder="登录后可评论"></textarea>
              <div class="form-footer" style="margin-top:10px">
                <button class="sm" @click="submitComment">
                  <span class="row" style="gap:6px"><Send :size="14" /> 提交评论</span>
                </button>
              </div>
            </div>

            <div class="comment-list">
              <div class="comment-item" v-for="c in state.h5CurrentDetail.comments" :key="c.id">
                <strong>{{ c.username }}</strong>
                <p>{{ c.content }}</p>
                <p class="muted" style="font-size:12px; margin:0">{{ new Date(c.createdAt).toLocaleString('zh-CN') }}</p>
              </div>
            </div>
          </div>
        </div>

        <aside class="sidebar">
          <!-- 浏览量置顶 -->
          <div class="card">
            <h3 class="card-title"><Flame :size="18" /> 浏览量 Top 10</h3>
            <template v-if="state.h5Top10.length > 0">
              <div class="list-row" v-for="(item, idx) in state.h5Top10" :key="item.id">
                <span><span class="rank">{{ idx + 1 }}</span>{{ item.title }}</span>
                <span class="views">{{ item.views }}</span>
              </div>
            </template>
            <template v-else>
              <p class="muted">暂无文章热榜</p>
              <div class="weather-box" v-if="state.weather">
                <p style="display:flex; align-items:center; gap:6px; font-weight:600">
                  <CloudSun :size="16" /> {{ state.weather.city }}：{{ state.weather.weather }}
                </p>
                <p>{{ state.weather.temperature }}，湿度 {{ state.weather.humidity }}</p>
              </div>
            </template>
          </div>

          <!-- 文章列表 -->
          <div class="card">
            <h3 class="card-title"><FileText :size="18" /> 文章列表</h3>
            <div v-if="state.h5Articles.length === 0" class="muted">暂无文章</div>
            <div v-for="article in state.h5Articles" :key="article.id" class="article-item">
              <h4>{{ article.title }}</h4>
              <div class="article-meta">
                <span><User :size="12" /> {{ article.author }}</span>
                <span><Eye :size="12" /> {{ article.views }}</span>
              </div>
              <p style="margin:0 0 10px; color: var(--ink-2)">{{ article.summary }}</p>
              <button class="sm" @click="loadArticleDetail(article.id)">查看详情</button>
            </div>
          </div>
        </aside>
      </main>

      <!-- 登录 / 注册模态框 -->
      <div class="modal-mask" v-if="authModal.open" @click.self="closeAuth">
        <div class="modal">
          <div class="modal-head">
            <h3>{{ authModal.tab === 'login' ? '登录' : '注册' }}</h3>
            <button class="modal-close" @click="closeAuth"><X :size="18" /></button>
          </div>

          <div class="tabs">
            <button :class="{ on: authModal.tab === 'login' }" @click="authModal.tab = 'login'">登录</button>
            <button :class="{ on: authModal.tab === 'register' }" @click="authModal.tab = 'register'">注册</button>
          </div>

          <p class="msg" style="margin-bottom:12px" v-if="state.h5Message">{{ state.h5Message }}</p>

          <form v-if="authModal.tab === 'login'" class="form-grid" @submit.prevent="h5Login">
            <label>用户名 <input v-model="state.loginForm.username" required /></label>
            <label>密码 <input v-model="state.loginForm.password" type="password" required /></label>
            <button type="submit" :disabled="submitting">登录</button>
          </form>

          <form v-else class="form-grid" @submit.prevent="h5Register">
            <label>用户名 <input v-model="state.registerForm.username" required /></label>
            <label>密码 <input v-model="state.registerForm.password" type="password" required /></label>
            <button type="submit" :disabled="submitting">注册</button>
          </form>
        </div>
      </div>
    </template>
  </div>
</template>
