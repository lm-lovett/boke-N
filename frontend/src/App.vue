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
import { ApiError, request } from './lib/request.js';
import { createTask } from './composables/useTask.js';
import TopProgress from './components/TopProgress.vue';
import Skeleton from './components/Skeleton.vue';
import LoadingOverlay from './components/LoadingOverlay.vue';
import StateBlock from './components/StateBlock.vue';

const view = new URLSearchParams(window.location.search).get('view') === 'admin' ? 'admin' : 'h5';

const menus = [
  { key: 'roles', label: '角色管理', icon: ShieldCheck, endpoint: '/api/admin/roles' },
  { key: 'users', label: '用户管理', icon: Users, endpoint: '/api/admin/users' },
  { key: 'resources', label: '资源管理', icon: KeyRound, endpoint: '/api/admin/resources' },
  { key: 'articles', label: '文章管理', icon: FileText, endpoint: '/api/admin/articles' },
  { key: 'bannedWords', label: '违禁词管理', icon: Ban, endpoint: '/api/admin/banned-words' },
  { key: 'comments', label: '评论记录管理', icon: MessagesSquare, endpoint: '/api/admin/comments' }
];

// 分区要展示的关联数据：与列表请求并行拉取，避免两轮串行等待
const hintEndpoints = {
  roles: '/api/admin/resources',
  users: '/api/admin/roles'
};

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
  h5ActiveId: null,
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

const authNotice = ref('');
const deletingIds = reactive(new Set());

function openAuth(tab = 'login') {
  authModal.tab = tab;
  authModal.open = true;
}

function closeAuth() {
  authModal.open = false;
  authNotice.value = '';
}

const adminMenuTitle = computed(() => menus.find((m) => m.key === state.adminSection)?.label || '管理');
const adminMenuIcon = computed(() => menus.find((m) => m.key === state.adminSection)?.icon || LayoutGrid);
const isAdminLoggedIn = computed(() => Boolean(state.adminToken));
const isH5Admin = computed(() => (state.h5User?.roles || []).some((r) => r.name === 'admin'));

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

function handleAuthExpired(message = '登录已失效，请重新登录') {
  state.adminToken = '';
  state.adminUser = null;
  state.adminRows = [];
  state.adminHint = '';
  state.adminMessage = message;
  saveAdminSession();
}

/* ---------------- 后台管理 ---------------- */

async function fetchAdminSection(signal, sectionKey) {
  const menu = menus.find((m) => m.key === sectionKey);
  if (!menu) {
    return;
  }
  const depEndpoint = hintEndpoints[sectionKey];
  const [rows, dep] = await Promise.all([
    request(menu.endpoint, {}, state.adminToken, { signal }),
    depEndpoint ? request(depEndpoint, {}, state.adminToken, { signal }) : Promise.resolve(null)
  ]);
  state.adminRows = rows || [];
  state.adminHint = dep ? dep.map((r) => `${r.id}:${r.name}`).join(' / ') : '';
}

async function postAdminSection(signal, { endpoint, body, form }) {
  await request(endpoint, { method: 'POST', body: JSON.stringify(body) }, state.adminToken, { signal });
  form.reset();
  state.adminMessage = '保存成功';
  await fetchAdminSection(signal, state.adminSection);
}

async function loginAdmin(signal) {
  const data = await request(
    '/api/auth/login',
    { method: 'POST', body: JSON.stringify(state.adminLoginForm) },
    '',
    { signal }
  );
  const roles = data.roles || [];
  if (!roles.some((r) => r.name === 'admin')) {
    throw new ApiError('当前账号不是管理员', 'business');
  }
  state.adminToken = data.token;
  state.adminUser = data.user;
  saveAdminSession();
  state.adminMessage = '登录成功';
}

const {
  loading: adminListLoading,
  error: adminListError,
  run: runAdminList
} = createTask(fetchAdminSection, {
  onError: (err) => {
    if (err?.status === 401 || err?.status === 403) {
      handleAuthExpired();
    }
  }
});

const { loading: adminSaveLoading, run: runAdminSave } = createTask(postAdminSection, {
  onError: (err) => {
    if (err?.status === 401 || err?.status === 403) {
      handleAuthExpired();
    } else {
      state.adminMessage = err.message;
    }
  }
});

const { loading: adminLoginLoading, error: adminLoginError, run: runAdminLogin } = createTask(loginAdmin);

function switchAdminSection(key) {
  if (key === state.adminSection && !adminListError.value) {
    refreshAdminSection();
    return;
  }
  state.adminSection = key;
  // 不同分区列结构不同，切换时先清空，避免旧数据残留被误读
  state.adminRows = [];
  state.adminHint = '';
  runAdminList(key);
}

function refreshAdminSection() {
  runAdminList(state.adminSection);
}

function adminLogout() {
  state.adminToken = '';
  state.adminUser = null;
  state.adminRows = [];
  state.adminHint = '';
  state.adminMessage = '已退出';
  saveAdminSession();
}

function buildAdminBody(form) {
  if (state.adminSection === 'roles') {
    return {
      name: form.get('name'),
      description: form.get('description'),
      resourceIds: String(form.get('resourceIds') || '')
        .split(',')
        .map((v) => Number(v.trim()))
        .filter((v) => Number.isInteger(v) && v > 0)
    };
  }
  if (state.adminSection === 'users') {
    return {
      username: form.get('username'),
      nickname: form.get('nickname'),
      password: form.get('password'),
      roleIds: String(form.get('roleIds') || '')
        .split(',')
        .map((v) => Number(v.trim()))
        .filter((v) => Number.isInteger(v) && v > 0)
    };
  }
  if (state.adminSection === 'resources') {
    return { code: form.get('code'), name: form.get('name') };
  }
  if (state.adminSection === 'articles') {
    return {
      title: form.get('title'),
      summary: form.get('summary'),
      content: form.get('content'),
      author: form.get('author'),
      published: form.get('published') === 'on'
    };
  }
  if (state.adminSection === 'bannedWords') {
    return { word: form.get('word') };
  }
  return null;
}

function onAdminSubmit(event) {
  event.preventDefault();
  if (adminSaveLoading.value) {
    return;
  }
  const menu = menus.find((m) => m.key === state.adminSection);
  if (!menu || state.adminSection === 'comments') {
    return;
  }
  const body = buildAdminBody(new FormData(event.target));
  if (!body) {
    return;
  }
  runAdminSave({ endpoint: menu.endpoint, body, form: event.target });
}

async function confirmDelete(row) {
  const menu = menus.find((m) => m.key === state.adminSection);
  if (!menu || deletingIds.has(row.id)) {
    return;
  }
  if (!window.confirm(`确认删除「${row.name || row.title || row.word || row.content || row.id}」？此操作不可撤销。`)) {
    return;
  }
  deletingIds.add(row.id);
  try {
    await request(`${menu.endpoint}/${row.id}`, { method: 'DELETE' }, state.adminToken);
    state.adminMessage = '删除成功';
    await refreshAdminRows();
  } catch (err) {
    state.adminMessage = err?.status === 401 || err?.status === 403 ? '登录已失效，请重新登录' : err.message;
    if (err?.status === 401 || err?.status === 403) {
      handleAuthExpired();
    }
  } finally {
    deletingIds.delete(row.id);
  }
}

async function refreshAdminRows() {
  const menu = menus.find((m) => m.key === state.adminSection);
  if (!menu) {
    return;
  }
  state.adminRows = (await request(menu.endpoint, {}, state.adminToken)) || [];
}

/* ---------------- H5 前台 ---------------- */

async function fetchArticles(signal) {
  const list = (await request('/api/articles', {}, '', { signal })) || [];
  state.h5Articles = list;
  return list;
}

async function fetchArticleDetail(signal, id) {
  const detail = await request(`/api/articles/${id}`, {}, '', { signal });
  state.h5CurrentDetail = detail;
}

async function fetchTop10(signal) {
  const top = (await request('/api/articles/top10', {}, '', { signal })) || [];
  state.h5Top10 = top;
  state.weather = top.length === 0 ? await request('/api/weather?city=上海市', {}, '', { signal }) : null;
}

async function postComment(signal) {
  const articleId = state.h5CurrentDetail?.article?.id;
  if (!articleId) {
    throw new ApiError('请先选择文章', 'business');
  }
  await request(
    `/api/articles/${articleId}/comments`,
    { method: 'POST', body: JSON.stringify({ content: state.commentText }) },
    state.h5Token,
    { signal }
  );
  state.commentText = '';
  state.h5Message = '评论成功';
  await fetchArticleDetail(signal, articleId);
  // 浏览量可能变化，静默刷新热榜，失败也不打扰用户
  fetchTop10(signal).catch(() => {});
}

async function loginH5(signal) {
  const data = await request(
    '/api/auth/login',
    { method: 'POST', body: JSON.stringify(state.loginForm) },
    '',
    { signal }
  );
  state.h5Token = data.token;
  state.h5User = { ...(data.user || {}), roles: data.roles || [] };
  saveH5Session();
  authNotice.value = '';
  authModal.open = false;
  state.h5Message = '登录成功，可评论';
}

async function registerH5(signal) {
  await request(
    '/api/auth/register',
    {
      method: 'POST',
      body: JSON.stringify({
        username: state.registerForm.username,
        nickname: state.registerForm.username,
        password: state.registerForm.password
      })
    },
    '',
    { signal }
  );
  authNotice.value = '注册成功，请登录';
  authModal.tab = 'login';
}

const { loading: articlesLoading, run: runArticles } = createTask(fetchArticles);
const { loading: detailLoading, error: detailError, run: runDetail } = createTask(fetchArticleDetail);
const { loading: topLoading, run: runTop10 } = createTask(fetchTop10);
const { loading: commentLoading, run: runComment } = createTask(postComment, {
  onError: (err) => {
    state.h5Message = err.message;
  }
});
const { loading: loginLoading, error: loginError, run: runLogin } = createTask(loginH5);
const { loading: registerLoading, error: registerError, run: runRegister } = createTask(registerH5);

// 首次加载用骨架屏，已有数据时的刷新用半透明遮罩保留旧内容，避免布局跳动
const adminTableSkeleton = computed(() => adminListLoading.value && state.adminRows.length === 0);
const articlesSkeleton = computed(() => articlesLoading.value && state.h5Articles.length === 0);
const topSkeleton = computed(() => topLoading.value && state.h5Top10.length === 0);
const detailSkeleton = computed(() => detailLoading.value && !state.h5CurrentDetail);

function openArticle(id) {
  if (id === state.h5ActiveId) {
    return;
  }
  state.h5ActiveId = id;
  runDetail(id);
}

function retryDetail() {
  if (state.h5ActiveId) {
    runDetail(state.h5ActiveId);
  }
}

function submitComment() {
  if (commentLoading.value) {
    return;
  }
  if (!state.h5Token) {
    authModal.tab = 'login';
    authModal.open = true;
    return;
  }
  if (!state.commentText.trim()) {
    state.h5Message = '评论内容不能为空';
    return;
  }
  runComment();
}

function h5Logout() {
  state.h5Token = '';
  state.h5User = null;
  saveH5Session();
  state.h5Message = '已退出登录';
}

onMounted(() => {
  if (state.mode === 'admin') {
    if (!state.adminToken) {
      return;
    }
    runAdminList(state.adminSection);
    return;
  }
  // 列表与热榜并行拉取，首屏不用等瀑布式串行
  runArticles().then((list) => {
    if (Array.isArray(list) && list.length > 0) {
      openArticle(list[0].id);
    } else {
      state.h5CurrentDetail = null;
    }
  });
  runTop10();
});
</script>

<template>
  <div class="app-wrap">
    <TopProgress />

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
              @click="switchAdminSection(m.key)"
              :disabled="!isAdminLoggedIn"
            >
              <component :is="m.icon" :size="16" />
              <span class="nav-label">{{ m.label }}</span>
              <span v-if="adminListLoading && state.adminSection === m.key" class="spinner spinner-sm nav-spinner" aria-hidden="true"></span>
            </button>
          </nav>
        </aside>

        <section class="content">
          <!-- 管理员登录 -->
          <div class="card" v-if="!isAdminLoggedIn">
            <h3 class="card-title"><LogIn :size="18" /> 管理员登录</h3>
            <p class="msg" v-if="state.adminMessage">{{ state.adminMessage }}</p>
            <form class="form-grid" @submit.prevent="runAdminLogin">
              <label>用户名 <input v-model="state.adminLoginForm.username" required :disabled="adminLoginLoading" /></label>
              <label>密码 <input v-model="state.adminLoginForm.password" type="password" required :disabled="adminLoginLoading" /></label>
              <StateBlock
                v-if="adminLoginError"
                tone="error"
                title="登录失败"
                :desc="adminLoginError"
              />
              <div class="form-footer">
                <button type="submit" :disabled="adminLoginLoading">
                  <span class="btn-loading">
                    <span v-if="adminLoginLoading" class="spinner spinner-sm" aria-hidden="true"></span>
                    <LogIn v-else :size="14" />
                    {{ adminLoginLoading ? '登录中…' : '登录' }}
                  </span>
                </button>
              </div>
            </form>
          </div>

          <!-- 已登录：当前分区 -->
          <template v-else>
            <div class="page-head">
              <h3 class="card-title" style="margin:0">
                <component :is="adminMenuIcon" :size="18" /> {{ adminMenuTitle }}
              </h3>
              <button class="secondary sm" @click="refreshAdminSection" :disabled="adminListLoading">
                <span class="btn-loading">
                  <span v-if="adminListLoading" class="spinner spinner-sm" aria-hidden="true"></span>
                  <RefreshCw v-else :size="14" />
                  {{ adminListLoading ? '刷新中…' : '刷新' }}
                </span>
              </button>
            </div>

            <p class="msg" v-if="state.adminMessage">{{ state.adminMessage }}</p>

            <!-- 新增表单 -->
            <div class="card" v-if="state.adminSection !== 'comments'">
              <h3 class="card-title"><UserPlus :size="18" /> 新增{{ adminMenuTitle }}</h3>
              <form class="form-grid" @submit="onAdminSubmit">
                <div class="grid two" v-if="state.adminSection === 'roles'">
                  <label>角色名 <input name="name" required :disabled="adminSaveLoading" /></label>
                  <label>描述 <input name="description" :disabled="adminSaveLoading" /></label>
                  <label>资源ID <input name="resourceIds" placeholder="1,2,3" :disabled="adminSaveLoading" /></label>
                </div>

                <div class="grid two" v-else-if="state.adminSection === 'users'">
                  <label>用户名 <input name="username" required :disabled="adminSaveLoading" /></label>
                  <label>昵称 <input name="nickname" :disabled="adminSaveLoading" /></label>
                  <label>密码 <input name="password" type="password" required :disabled="adminSaveLoading" /></label>
                  <label>角色ID <input name="roleIds" placeholder="1,2" :disabled="adminSaveLoading" /></label>
                </div>

                <div class="grid two" v-else-if="state.adminSection === 'resources'">
                  <label>编码 <input name="code" required :disabled="adminSaveLoading" /></label>
                  <label>名称 <input name="name" required :disabled="adminSaveLoading" /></label>
                </div>

                <template v-else-if="state.adminSection === 'articles'">
                  <div class="grid two">
                    <label>标题 <input name="title" required :disabled="adminSaveLoading" /></label>
                    <label>作者 <input name="author" :disabled="adminSaveLoading" /></label>
                    <label>摘要 <input name="summary" :disabled="adminSaveLoading" /></label>
                  </div>
                  <label>内容 <textarea name="content" rows="5" required :disabled="adminSaveLoading"></textarea></label>
                  <div class="form-footer">
                    <label class="row" style="gap:6px; font-weight:400">
                      <input name="published" type="checkbox" checked style="width:auto" :disabled="adminSaveLoading" /> 立即发布
                    </label>
                  </div>
                </template>

                <label v-else-if="state.adminSection === 'bannedWords'">
                  违禁词 <input name="word" required :disabled="adminSaveLoading" />
                </label>

                <div class="form-footer">
                  <button type="submit" :disabled="adminSaveLoading">
                    <span class="btn-loading">
                      <span v-if="adminSaveLoading" class="spinner spinner-sm" aria-hidden="true"></span>
                      <UserPlus v-else :size="14" />
                      {{ adminSaveLoading ? '提交中…' : '新增' }}
                    </span>
                  </button>
                </div>
              </form>
              <p class="hint" v-if="state.adminHint && !adminListLoading">参考：{{ state.adminHint }}</p>
            </div>

            <!-- 数据表格 -->
            <div class="card">
              <h3 class="card-title"><FileText :size="18" /> {{ adminMenuTitle }}列表</h3>

              <StateBlock
                v-if="adminListError"
                tone="error"
                title="列表加载失败"
                :desc="adminListError"
                :retryable="true"
                :retrying="adminListLoading"
                @retry="refreshAdminSection"
              />

              <template v-else-if="adminTableSkeleton">
                <Skeleton variant="table" :rows="5" />
              </template>

              <template v-else>
                <div class="overlay-host">
                  <LoadingOverlay :show="adminListLoading" :text="`${adminMenuTitle}加载中…`" />
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
                        <tr v-for="row in state.adminRows" :key="row.id" :class="{ 'is-busy': deletingIds.has(row.id) }">
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
                          <td>
                            <button class="danger" :disabled="deletingIds.has(row.id)" @click="confirmDelete(row)">
                              <span class="btn-loading">
                                <span v-if="deletingIds.has(row.id)" class="spinner spinner-sm" aria-hidden="true"></span>
                                {{ deletingIds.has(row.id) ? '删除中…' : '删除' }}
                              </span>
                            </button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </template>
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
          <div class="card" v-if="detailSkeleton">
            <Skeleton variant="card" />
          </div>

          <StateBlock
            v-else-if="detailError"
            tone="error"
            title="文章加载失败"
            :desc="detailError"
            :retryable="true"
            :retrying="detailLoading"
            @retry="retryDetail"
          />

          <StateBlock
            v-else-if="!state.h5CurrentDetail && !detailLoading"
            tone="empty"
            title="还没有文章"
            desc="发布第一篇文章后，这里会显示正文。"
          />

          <div class="card overlay-host" v-else-if="state.h5CurrentDetail">
            <LoadingOverlay :show="detailLoading" text="文章加载中…" />
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
              <textarea
                v-model="state.commentText"
                rows="3"
                :placeholder="state.h5Token ? '说点什么…' : '登录后可评论'"
                :disabled="commentLoading"
              ></textarea>
              <div class="form-footer" style="margin-top:10px">
                <button class="sm" @click="submitComment" :disabled="commentLoading">
                  <span class="btn-loading">
                    <span v-if="commentLoading" class="spinner spinner-sm" aria-hidden="true"></span>
                    <Send v-else :size="14" />
                    {{ commentLoading ? '提交中…' : '提交评论' }}
                  </span>
                </button>
              </div>
            </div>

            <div class="comment-list">
              <template v-if="(state.h5CurrentDetail.comments || []).length > 0">
                <div class="comment-item" v-for="c in state.h5CurrentDetail.comments" :key="c.id">
                  <strong>{{ c.username }}</strong>
                  <p>{{ c.content }}</p>
                  <p class="muted" style="font-size:12px; margin:0">{{ new Date(c.createdAt).toLocaleString('zh-CN') }}</p>
                </div>
              </template>
              <StateBlock v-else tone="empty" title="还没有评论" desc="来写下第一条评论吧。" />
            </div>
          </div>
        </div>

        <aside class="sidebar">
          <!-- 浏览量置顶 -->
          <div class="card">
            <h3 class="card-title"><Flame :size="18" /> 浏览量 Top 10</h3>
            <div class="overlay-host">
              <Skeleton v-if="topSkeleton" variant="row" :rows="6" />
              <template v-else>
                <LoadingOverlay :show="topLoading" text="刷新榜单…" />
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
              </template>
            </div>
          </div>

          <!-- 文章列表 -->
          <div class="card">
            <h3 class="card-title"><FileText :size="18" /> 文章列表</h3>
            <div class="overlay-host">
              <template v-if="articlesSkeleton">
                <div class="stack">
                  <Skeleton v-for="i in 3" :key="i" variant="card" />
                </div>
              </template>
              <template v-else>
                <LoadingOverlay :show="articlesLoading" text="更新列表…" />
                <div v-if="state.h5Articles.length === 0" class="muted">暂无文章</div>
                <div
                  v-for="article in state.h5Articles"
                  :key="article.id"
                  class="article-item"
                  :class="{ 'is-active': state.h5ActiveId === article.id }"
                >
                  <h4>{{ article.title }}</h4>
                  <div class="article-meta">
                    <span><User :size="12" /> {{ article.author }}</span>
                    <span><Eye :size="12" /> {{ article.views }}</span>
                    <span v-if="detailLoading && state.h5ActiveId === article.id" class="spinner spinner-sm article-spinner" aria-hidden="true"></span>
                  </div>
                  <p style="margin:0 0 10px; color: var(--ink-2)">{{ article.summary }}</p>
                  <button class="sm" @click="openArticle(article.id)" :disabled="detailLoading && state.h5ActiveId === article.id">
                    {{ detailLoading && state.h5ActiveId === article.id ? '加载中…' : '查看详情' }}
                  </button>
                </div>
              </template>
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

          <p class="msg" style="margin-bottom:12px" v-if="authNotice">{{ authNotice }}</p>

          <form v-if="authModal.tab === 'login'" class="form-grid" @submit.prevent="runLogin">
            <label>用户名 <input v-model="state.loginForm.username" required :disabled="loginLoading" /></label>
            <label>密码 <input v-model="state.loginForm.password" type="password" required :disabled="loginLoading" /></label>
            <StateBlock v-if="loginError" tone="error" title="登录失败" :desc="loginError" />
            <button type="submit" :disabled="loginLoading">
              <span class="btn-loading" style="justify-content:center">
                <span v-if="loginLoading" class="spinner spinner-sm" aria-hidden="true"></span>
                {{ loginLoading ? '登录中…' : '登录' }}
              </span>
            </button>
          </form>

          <form v-else class="form-grid" @submit.prevent="runRegister">
            <label>用户名 <input v-model="state.registerForm.username" required :disabled="registerLoading" /></label>
            <label>密码 <input v-model="state.registerForm.password" type="password" required :disabled="registerLoading" /></label>
            <StateBlock v-if="registerError" tone="error" title="注册失败" :desc="registerError" />
            <button type="submit" :disabled="registerLoading">
              <span class="btn-loading" style="justify-content:center">
                <span v-if="registerLoading" class="spinner spinner-sm" aria-hidden="true"></span>
                {{ registerLoading ? '提交中…' : '注册' }}
              </span>
            </button>
          </form>
        </div>
      </div>
    </template>
  </div>
</template>
