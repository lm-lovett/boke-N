INSERT OR IGNORE INTO roles (id, name, description) VALUES
  (1, 'admin', '系统管理员'),
  (2, 'reader', '普通用户');

INSERT OR IGNORE INTO resources (id, code, name) VALUES
  (1, 'role:manage', '角色管理'),
  (2, 'user:manage', '用户管理'),
  (3, 'resource:manage', '资源管理'),
  (4, 'article:manage', '文章管理'),
  (5, 'bannedword:manage', '违禁词管理'),
  (6, 'comment:manage', '评论记录管理');

INSERT OR IGNORE INTO role_resources (role_id, resource_id) VALUES
  (1, 1),
  (1, 2),
  (1, 3),
  (1, 4),
  (1, 5),
  (1, 6);

INSERT OR IGNORE INTO users (id, username, nickname, password_hash) VALUES
  (1, 'admin', '管理员', '$2a$10$LsJpYNJ3fEtSkouyp4wDhuwW3atbTJ87CLoFsJ3/7EWiQcclyHnWy'),
  (2, 'demo', '示例用户', '$2a$10$0297XSzEHmr5.L7Mye4EbOnyRZ.HYP2niQ.eKZVgyUSdHPPJj2ZNm');

INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES
  (1, 1),
  (2, 2);

INSERT OR IGNORE INTO banned_words (id, word) VALUES
  (1, '赌博'),
  (2, '诈骗');

INSERT OR IGNORE INTO articles (id, title, summary, content, author, views, published, created_at) VALUES
  (1, '欢迎使用博客系统', '系统初始化文章', '这是一篇初始化文章内容。', 'admin', 12, 1, datetime('now'));

INSERT OR IGNORE INTO comments (id, article_id, user_id, username, content, created_at) VALUES
  (1, 1, 2, 'demo', '这是一条初始化评论。', datetime('now'));
