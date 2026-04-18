const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

const app = express();
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || "blog-secret-key";
const DB_PATH = path.join(__dirname, "..", "data", "db.json");
const PUBLIC_DIR = path.join(__dirname, "..", "public");

app.use(cors());
app.use(express.json());
app.use(express.static(PUBLIC_DIR));

function ensureDb() {
  fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });
  if (!fs.existsSync(DB_PATH)) {
    const initial = {
      users: [],
      roles: [],
      resources: [],
      articles: [],
      bannedWords: [],
      comments: [],
      counters: {
        userId: 1,
        roleId: 1,
        resourceId: 1,
        articleId: 1,
        bannedWordId: 1,
        commentId: 1,
      },
    };
    fs.writeFileSync(DB_PATH, JSON.stringify(initial, null, 2), "utf-8");
  }
}

function readDb() {
  ensureDb();
  return JSON.parse(fs.readFileSync(DB_PATH, "utf-8"));
}

function writeDb(db) {
  fs.writeFileSync(DB_PATH, JSON.stringify(db, null, 2), "utf-8");
}

function nextId(db, key) {
  const value = db.counters[key] || 1;
  db.counters[key] = value + 1;
  return value;
}

function initSeed() {
  const db = readDb();
  let changed = false;

  if (db.roles.length === 0) {
    db.roles.push(
      {
        id: nextId(db, "roleId"),
        name: "admin",
        description: "系统管理员",
        resourceIds: [],
      },
      {
        id: nextId(db, "roleId"),
        name: "reader",
        description: "普通用户",
        resourceIds: [],
      }
    );
    changed = true;
  }

  if (db.resources.length === 0) {
    const menus = [
      { code: "role:manage", name: "角色管理" },
      { code: "user:manage", name: "用户管理" },
      { code: "resource:manage", name: "资源管理" },
      { code: "article:manage", name: "文章管理" },
      { code: "bannedword:manage", name: "违禁词管理" },
      { code: "comment:manage", name: "评论记录管理" },
    ];
    menus.forEach((menu) => {
      db.resources.push({
        id: nextId(db, "resourceId"),
        code: menu.code,
        name: menu.name,
      });
    });
    const adminRole = db.roles.find((r) => r.name === "admin");
    if (adminRole) {
      adminRole.resourceIds = db.resources.map((r) => r.id);
    }
    changed = true;
  }

  if (db.users.length === 0) {
    const adminRole = db.roles.find((r) => r.name === "admin");
    const readerRole = db.roles.find((r) => r.name === "reader");
    db.users.push(
      {
        id: nextId(db, "userId"),
        username: "admin",
        nickname: "管理员",
        passwordHash: bcrypt.hashSync("Admin123!", 10),
        roleIds: adminRole ? [adminRole.id] : [],
      },
      {
        id: nextId(db, "userId"),
        username: "demo",
        nickname: "示例用户",
        passwordHash: bcrypt.hashSync("Demo123!", 10),
        roleIds: readerRole ? [readerRole.id] : [],
      }
    );
    changed = true;
  }

  if (db.bannedWords.length === 0) {
    db.bannedWords.push(
      { id: nextId(db, "bannedWordId"), word: "赌博" },
      { id: nextId(db, "bannedWordId"), word: "诈骗" }
    );
    changed = true;
  }

  if (changed) {
    writeDb(db);
  }
}

function sanitizeUser(user) {
  const { passwordHash, ...rest } = user;
  return rest;
}

function getAuth(req) {
  const header = req.headers.authorization || "";
  if (!header.startsWith("Bearer ")) return null;
  const token = header.slice(7);
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch {
    return null;
  }
}

function authRequired(req, res, next) {
  const payload = getAuth(req);
  if (!payload) {
    return res.status(401).json({ message: "未登录或登录已过期" });
  }
  req.user = payload;
  next();
}

function adminRequired(req, res, next) {
  const payload = getAuth(req);
  if (!payload) {
    return res.status(401).json({ message: "未登录或登录已过期" });
  }
  if (!payload.isAdmin) {
    return res.status(403).json({ message: "需要管理员权限" });
  }
  req.user = payload;
  next();
}

function containsBannedWord(text, bannedWords) {
  return bannedWords.find((item) => text.includes(item.word));
}

app.get("/api/health", (_req, res) => {
  res.json({ ok: true });
});

app.post("/api/auth/login", (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ message: "用户名和密码不能为空" });
  }
  const db = readDb();
  const user = db.users.find((u) => u.username === username);
  if (!user || !bcrypt.compareSync(password, user.passwordHash)) {
    return res.status(401).json({ message: "用户名或密码错误" });
  }
  const roles = db.roles.filter((r) => user.roleIds.includes(r.id));
  const resources = db.resources.filter((resource) =>
    roles.some((role) => role.resourceIds.includes(resource.id))
  );
  const token = jwt.sign(
    {
      userId: user.id,
      username: user.username,
      isAdmin: roles.some((r) => r.name === "admin"),
      roleIds: user.roleIds,
    },
    JWT_SECRET,
    { expiresIn: "7d" }
  );
  return res.json({
    token,
    user: sanitizeUser(user),
    roles,
    resources,
  });
});

app.post("/api/auth/register", (req, res) => {
  const { username, nickname, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ message: "用户名和密码不能为空" });
  }
  const db = readDb();
  if (db.users.some((u) => u.username === username)) {
    return res.status(409).json({ message: "用户名已存在" });
  }
  const readerRole = db.roles.find((r) => r.name === "reader");
  const user = {
    id: nextId(db, "userId"),
    username,
    nickname: nickname || username,
    passwordHash: bcrypt.hashSync(password, 10),
    roleIds: readerRole ? [readerRole.id] : [],
  };
  db.users.push(user);
  writeDb(db);
  return res.status(201).json({ user: sanitizeUser(user) });
});

app.get("/api/admin/roles", adminRequired, (_req, res) => {
  const db = readDb();
  res.json(db.roles);
});

app.post("/api/admin/roles", adminRequired, (req, res) => {
  const { name, description, resourceIds } = req.body || {};
  if (!name) {
    return res.status(400).json({ message: "角色名不能为空" });
  }
  const db = readDb();
  if (db.roles.some((r) => r.name === name)) {
    return res.status(409).json({ message: "角色名已存在" });
  }
  const role = {
    id: nextId(db, "roleId"),
    name,
    description: description || "",
    resourceIds: Array.isArray(resourceIds) ? resourceIds : [],
  };
  db.roles.push(role);
  writeDb(db);
  res.status(201).json(role);
});

app.put("/api/admin/roles/:id", adminRequired, (req, res) => {
  const id = Number(req.params.id);
  const { name, description, resourceIds } = req.body || {};
  const db = readDb();
  const role = db.roles.find((r) => r.id === id);
  if (!role) {
    return res.status(404).json({ message: "角色不存在" });
  }
  if (name) role.name = name;
  if (description !== undefined) role.description = description;
  if (Array.isArray(resourceIds)) role.resourceIds = resourceIds;
  writeDb(db);
  res.json(role);
});

app.delete("/api/admin/roles/:id", adminRequired, (req, res) => {
  const id = Number(req.params.id);
  const db = readDb();
  db.roles = db.roles.filter((r) => r.id !== id);
  db.users = db.users.map((u) => ({
    ...u,
    roleIds: u.roleIds.filter((roleId) => roleId !== id),
  }));
  writeDb(db);
  res.json({ message: "删除成功" });
});

app.get("/api/admin/users", adminRequired, (_req, res) => {
  const db = readDb();
  res.json(db.users.map(sanitizeUser));
});

app.post("/api/admin/users", adminRequired, (req, res) => {
  const { username, nickname, password, roleIds } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ message: "用户名和密码不能为空" });
  }
  const db = readDb();
  if (db.users.some((u) => u.username === username)) {
    return res.status(409).json({ message: "用户名已存在" });
  }
  const user = {
    id: nextId(db, "userId"),
    username,
    nickname: nickname || username,
    passwordHash: bcrypt.hashSync(password, 10),
    roleIds: Array.isArray(roleIds) ? roleIds : [],
  };
  db.users.push(user);
  writeDb(db);
  res.status(201).json(sanitizeUser(user));
});

app.put("/api/admin/users/:id", adminRequired, (req, res) => {
  const id = Number(req.params.id);
  const { nickname, roleIds, password } = req.body || {};
  const db = readDb();
  const user = db.users.find((u) => u.id === id);
  if (!user) {
    return res.status(404).json({ message: "用户不存在" });
  }
  if (nickname !== undefined) user.nickname = nickname;
  if (Array.isArray(roleIds)) user.roleIds = roleIds;
  if (password) user.passwordHash = bcrypt.hashSync(password, 10);
  writeDb(db);
  res.json(sanitizeUser(user));
});

app.delete("/api/admin/users/:id", adminRequired, (req, res) => {
  const id = Number(req.params.id);
  const db = readDb();
  db.users = db.users.filter((u) => u.id !== id);
  writeDb(db);
  res.json({ message: "删除成功" });
});

app.get("/api/admin/resources", adminRequired, (_req, res) => {
  const db = readDb();
  res.json(db.resources);
});

app.post("/api/admin/resources", adminRequired, (req, res) => {
  const { code, name } = req.body || {};
  if (!code || !name) {
    return res.status(400).json({ message: "资源编码和名称不能为空" });
  }
  const db = readDb();
  const resource = {
    id: nextId(db, "resourceId"),
    code,
    name,
  };
  db.resources.push(resource);
  writeDb(db);
  res.status(201).json(resource);
});

app.put("/api/admin/resources/:id", adminRequired, (req, res) => {
  const id = Number(req.params.id);
  const { code, name } = req.body || {};
  const db = readDb();
  const resource = db.resources.find((r) => r.id === id);
  if (!resource) {
    return res.status(404).json({ message: "资源不存在" });
  }
  if (code) resource.code = code;
  if (name) resource.name = name;
  writeDb(db);
  res.json(resource);
});

app.delete("/api/admin/resources/:id", adminRequired, (req, res) => {
  const id = Number(req.params.id);
  const db = readDb();
  db.resources = db.resources.filter((r) => r.id !== id);
  db.roles = db.roles.map((role) => ({
    ...role,
    resourceIds: role.resourceIds.filter((resourceId) => resourceId !== id),
  }));
  writeDb(db);
  res.json({ message: "删除成功" });
});

app.get("/api/admin/articles", adminRequired, (_req, res) => {
  const db = readDb();
  res.json(db.articles);
});

app.post("/api/admin/articles", adminRequired, (req, res) => {
  const { title, summary, content, author, published } = req.body || {};
  if (!title || !content) {
    return res.status(400).json({ message: "文章标题和内容不能为空" });
  }
  const db = readDb();
  const article = {
    id: nextId(db, "articleId"),
    title,
    summary: summary || "",
    content,
    author: author || req.user.username,
    views: 0,
    published: published !== false,
    createdAt: new Date().toISOString(),
  };
  db.articles.push(article);
  writeDb(db);
  res.status(201).json(article);
});

app.put("/api/admin/articles/:id", adminRequired, (req, res) => {
  const id = Number(req.params.id);
  const { title, summary, content, author, published } = req.body || {};
  const db = readDb();
  const article = db.articles.find((a) => a.id === id);
  if (!article) {
    return res.status(404).json({ message: "文章不存在" });
  }
  if (title !== undefined) article.title = title;
  if (summary !== undefined) article.summary = summary;
  if (content !== undefined) article.content = content;
  if (author !== undefined) article.author = author;
  if (published !== undefined) article.published = Boolean(published);
  writeDb(db);
  res.json(article);
});

app.delete("/api/admin/articles/:id", adminRequired, (req, res) => {
  const id = Number(req.params.id);
  const db = readDb();
  db.articles = db.articles.filter((a) => a.id !== id);
  db.comments = db.comments.filter((c) => c.articleId !== id);
  writeDb(db);
  res.json({ message: "删除成功" });
});

app.get("/api/admin/banned-words", adminRequired, (_req, res) => {
  const db = readDb();
  res.json(db.bannedWords);
});

app.post("/api/admin/banned-words", adminRequired, (req, res) => {
  const { word } = req.body || {};
  if (!word) {
    return res.status(400).json({ message: "违禁词不能为空" });
  }
  const db = readDb();
  const item = {
    id: nextId(db, "bannedWordId"),
    word,
  };
  db.bannedWords.push(item);
  writeDb(db);
  res.status(201).json(item);
});

app.delete("/api/admin/banned-words/:id", adminRequired, (req, res) => {
  const id = Number(req.params.id);
  const db = readDb();
  db.bannedWords = db.bannedWords.filter((item) => item.id !== id);
  writeDb(db);
  res.json({ message: "删除成功" });
});

app.get("/api/admin/comments", adminRequired, (_req, res) => {
  const db = readDb();
  res.json(db.comments);
});

app.delete("/api/admin/comments/:id", adminRequired, (req, res) => {
  const id = Number(req.params.id);
  const db = readDb();
  db.comments = db.comments.filter((item) => item.id !== id);
  writeDb(db);
  res.json({ message: "删除成功" });
});

app.get("/api/articles", (_req, res) => {
  const db = readDb();
  const list = db.articles
    .filter((a) => a.published)
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  res.json(list);
});

app.get("/api/articles/top10", (_req, res) => {
  const db = readDb();
  const top10 = db.articles
    .filter((a) => a.published)
    .sort((a, b) => b.views - a.views)
    .slice(0, 10);
  res.json(top10);
});

app.get("/api/articles/:id", (req, res) => {
  const id = Number(req.params.id);
  const db = readDb();
  const article = db.articles.find((a) => a.id === id && a.published);
  if (!article) {
    return res.status(404).json({ message: "文章不存在" });
  }
  article.views += 1;
  writeDb(db);
  const comments = db.comments
    .filter((c) => c.articleId === id)
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  return res.json({ article, comments });
});

app.post("/api/articles/:id/comments", authRequired, (req, res) => {
  const articleId = Number(req.params.id);
  const { content } = req.body || {};
  if (!content) {
    return res.status(400).json({ message: "评论内容不能为空" });
  }
  const db = readDb();
  const article = db.articles.find((a) => a.id === articleId && a.published);
  if (!article) {
    return res.status(404).json({ message: "文章不存在" });
  }
  const hit = containsBannedWord(content, db.bannedWords);
  if (hit) {
    return res.status(400).json({ message: `评论包含违禁词: ${hit.word}` });
  }
  const user = db.users.find((u) => u.id === req.user.userId);
  const comment = {
    id: nextId(db, "commentId"),
    articleId,
    userId: req.user.userId,
    username: user ? user.username : req.user.username,
    content,
    createdAt: new Date().toISOString(),
  };
  db.comments.push(comment);
  writeDb(db);
  res.status(201).json(comment);
});

app.get("/api/weather", (req, res) => {
  const city = req.query.city || "上海市";
  res.json({
    city,
    weather: "多云",
    temperature: "18~24°C",
    humidity: "62%",
    tip: "当前为演示天气数据，可后续接入真实天气 API。",
    updatedAt: new Date().toISOString(),
  });
});

app.get("/admin", (_req, res) => {
  res.sendFile(path.join(PUBLIC_DIR, "admin.html"));
});

app.get("/", (_req, res) => {
  res.sendFile(path.join(PUBLIC_DIR, "index.html"));
});

initSeed();

app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Blog app listening on http://localhost:${PORT}`);
});
