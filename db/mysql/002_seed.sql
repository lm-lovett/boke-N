USE boke_n;

-- 默认角色
INSERT IGNORE INTO roles (id, name, description) VALUES
  (1, 'admin', '系统管理员'),
  (2, 'reader', '普通用户');

-- RBAC 资源菜单
INSERT IGNORE INTO resources (id, code, name) VALUES
  (1, 'role:manage', '角色管理'),
  (2, 'user:manage', '用户管理'),
  (3, 'resource:manage', '资源管理'),
  (4, 'article:manage', '文章管理'),
  (5, 'bannedword:manage', '违禁词管理'),
  (6, 'comment:manage', '评论记录管理');

-- 角色-资源关系：admin 拥有全部菜单权限
INSERT IGNORE INTO role_resources (role_id, resource_id) VALUES
  (1, 1),
  (1, 2),
  (1, 3),
  (1, 4),
  (1, 5),
  (1, 6);

-- 默认用户（密码 hash 请替换为你系统实际算法产物）
-- 这里使用占位 hash，接入真实登录时建议由服务端创建/迁移时加密
INSERT IGNORE INTO users (id, username, nickname, password_hash) VALUES
  (1, 'admin', '管理员', '$2a$10$LsJpYNJ3fEtSkouyp4wDhuwW3atbTJ87CLoFsJ3/7EWiQcclyHnWy'),
  (2, 'demo', '示例用户', '$2a$10$0297XSzEHmr5.L7Mye4EbOnyRZ.HYP2niQ.eKZVgyUSdHPPJj2ZNm');

-- 用户-角色关系
INSERT IGNORE INTO user_roles (user_id, role_id) VALUES
  (1, 1),
  (2, 2);

-- 默认违禁词
INSERT IGNORE INTO banned_words (id, word) VALUES
  (1, '赌博'),
  (2, '诈骗');

-- 文章与评论演示数据（可选）
INSERT IGNORE INTO articles (id, title, summary, content, author, views, published, created_at) VALUES
  (1, '欢迎使用博客系统', '系统初始化文章', '这是一篇初始化文章内容。', 'admin', 12, 1, CURRENT_TIMESTAMP);

INSERT IGNORE INTO comments (id, article_id, user_id, username, content, created_at) VALUES
  (1, 1, 2, 'demo', '这是一条初始化评论。', CURRENT_TIMESTAMP);

