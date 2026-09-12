INSERT INTO users (username, nickname, password_hash)
SELECT 'liumeng', 'liumeng', '$2b$12$5Vk.enJRsJ4FtCSlAfb1pObSVQfsSL0icQ.kQmUXhJE86vi0OMgfe'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'liumeng');

UPDATE users
SET nickname = 'liumeng',
    password_hash = '$2b$12$5Vk.enJRsJ4FtCSlAfb1pObSVQfsSL0icQ.kQmUXhJE86vi0OMgfe'
WHERE username = 'liumeng';

INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT id, 1 FROM users WHERE username = 'liumeng';
