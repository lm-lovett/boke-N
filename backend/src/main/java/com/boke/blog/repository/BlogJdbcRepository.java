package com.boke.blog.repository;

import com.boke.blog.model.Article;
import com.boke.blog.model.BannedWord;
import com.boke.blog.model.Comment;
import com.boke.blog.model.Resource;
import com.boke.blog.model.Role;
import com.boke.blog.model.User;
import java.sql.PreparedStatement;
import java.sql.Statement;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
@Transactional
public class BlogJdbcRepository {

  private final JdbcTemplate jdbcTemplate;

  public BlogJdbcRepository(JdbcTemplate jdbcTemplate) {
    this.jdbcTemplate = jdbcTemplate;
  }

  public Optional<User> findUserByUsername(String username) {
    List<User> users = jdbcTemplate.query(
        "SELECT id, username, nickname, password_hash FROM users WHERE username = ?",
        (rs, rowNum) -> {
          User user = new User();
          user.setId(rs.getLong("id"));
          user.setUsername(rs.getString("username"));
          user.setNickname(rs.getString("nickname"));
          user.setPasswordHash(rs.getString("password_hash"));
          return user;
        },
        username
    );
    if (users.isEmpty()) {
      return Optional.empty();
    }
    User user = users.getFirst();
    user.setRoleIds(listRoleIdsByUserId(user.getId()));
    return Optional.of(user);
  }

  public Optional<User> findUserById(Long id) {
    List<User> users = jdbcTemplate.query(
        "SELECT id, username, nickname, password_hash FROM users WHERE id = ?",
        (rs, rowNum) -> {
          User user = new User();
          user.setId(rs.getLong("id"));
          user.setUsername(rs.getString("username"));
          user.setNickname(rs.getString("nickname"));
          user.setPasswordHash(rs.getString("password_hash"));
          return user;
        },
        id
    );
    if (users.isEmpty()) {
      return Optional.empty();
    }
    User user = users.getFirst();
    user.setRoleIds(listRoleIdsByUserId(user.getId()));
    return Optional.of(user);
  }

  public boolean existsUserByUsername(String username) {
    Integer count = jdbcTemplate.queryForObject(
        "SELECT COUNT(1) FROM users WHERE username = ?",
        Integer.class,
        username
    );
    return count != null && count > 0;
  }

  public List<User> listUsers() {
    List<User> users = jdbcTemplate.query(
        "SELECT id, username, nickname, password_hash FROM users ORDER BY id ASC",
        (rs, rowNum) -> {
          User user = new User();
          user.setId(rs.getLong("id"));
          user.setUsername(rs.getString("username"));
          user.setNickname(rs.getString("nickname"));
          user.setPasswordHash(rs.getString("password_hash"));
          return user;
        }
    );
    Map<Long, List<Long>> roleMap = listRoleIdsByUserIds(
        users.stream().map(User::getId).toList()
    );
    users.forEach(user -> user.setRoleIds(roleMap.getOrDefault(user.getId(), new ArrayList<>())));
    return users;
  }

  public Long insertUser(String username, String nickname, String passwordHash, List<Long> roleIds) {
    KeyHolder keyHolder = new GeneratedKeyHolder();
    jdbcTemplate.update(connection -> {
      PreparedStatement ps = connection.prepareStatement(
          "INSERT INTO users (username, nickname, password_hash) VALUES (?, ?, ?)",
          Statement.RETURN_GENERATED_KEYS
      );
      ps.setString(1, username);
      ps.setString(2, nickname);
      ps.setString(3, passwordHash);
      return ps;
    }, keyHolder);
    Long userId = Optional.ofNullable(keyHolder.getKey())
        .map(Number::longValue)
        .orElseThrow(() -> new IllegalStateException("创建用户失败"));
    replaceUserRoles(userId, roleIds == null ? List.of() : roleIds);
    return userId;
  }

  public void updateUser(Long id, String nickname, String passwordHash) {
    jdbcTemplate.update(
        "UPDATE users SET nickname = ?, password_hash = ? WHERE id = ?",
        nickname,
        passwordHash,
        id
    );
  }

  public void updateUserPasswordHash(Long id, String passwordHash) {
    jdbcTemplate.update("UPDATE users SET password_hash = ? WHERE id = ?", passwordHash, id);
  }

  public void replaceUserRoles(Long userId, List<Long> roleIds) {
    jdbcTemplate.update("DELETE FROM user_roles WHERE user_id = ?", userId);
    if (roleIds == null || roleIds.isEmpty()) {
      return;
    }
    for (Long roleId : roleIds) {
      jdbcTemplate.update(
          "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
          userId,
          roleId
      );
    }
  }

  public void deleteUser(Long id) {
    jdbcTemplate.update("DELETE FROM users WHERE id = ?", id);
  }

  public List<Role> listRoles() {
    List<Role> roles = jdbcTemplate.query(
        "SELECT id, name, description FROM roles ORDER BY id ASC",
        (rs, rowNum) -> {
          Role role = new Role();
          role.setId(rs.getLong("id"));
          role.setName(rs.getString("name"));
          role.setDescription(rs.getString("description"));
          return role;
        }
    );
    Map<Long, List<Long>> resourceMap = listResourceIdsByRoleIds(roles.stream().map(Role::getId).toList());
    roles.forEach(role -> role.setResourceIds(resourceMap.getOrDefault(role.getId(), new ArrayList<>())));
    return roles;
  }

  public List<Role> listRolesByIds(List<Long> ids) {
    if (ids == null || ids.isEmpty()) {
      return List.of();
    }
    String inClause = placeholders(ids);
    List<Role> roles = jdbcTemplate.query(
        "SELECT id, name, description FROM roles WHERE id IN (" + inClause + ")",
        (rs, rowNum) -> {
          Role role = new Role();
          role.setId(rs.getLong("id"));
          role.setName(rs.getString("name"));
          role.setDescription(rs.getString("description"));
          return role;
        },
        ids.toArray()
    );
    Map<Long, List<Long>> resourceMap = listResourceIdsByRoleIds(roles.stream().map(Role::getId).toList());
    roles.forEach(role -> role.setResourceIds(resourceMap.getOrDefault(role.getId(), new ArrayList<>())));
    roles.sort(Comparator.comparing(Role::getId));
    return roles;
  }

  public Optional<Role> findRoleByName(String name) {
    List<Role> roles = jdbcTemplate.query(
        "SELECT id, name, description FROM roles WHERE name = ?",
        (rs, rowNum) -> {
          Role role = new Role();
          role.setId(rs.getLong("id"));
          role.setName(rs.getString("name"));
          role.setDescription(rs.getString("description"));
          return role;
        },
        name
    );
    if (roles.isEmpty()) {
      return Optional.empty();
    }
    Role role = roles.getFirst();
    role.setResourceIds(listResourceIdsByRoleId(role.getId()));
    return Optional.of(role);
  }

  public Optional<Role> findRoleById(Long id) {
    List<Role> roles = jdbcTemplate.query(
        "SELECT id, name, description FROM roles WHERE id = ?",
        (rs, rowNum) -> {
          Role role = new Role();
          role.setId(rs.getLong("id"));
          role.setName(rs.getString("name"));
          role.setDescription(rs.getString("description"));
          return role;
        },
        id
    );
    if (roles.isEmpty()) {
      return Optional.empty();
    }
    Role role = roles.getFirst();
    role.setResourceIds(listResourceIdsByRoleId(role.getId()));
    return Optional.of(role);
  }

  public boolean existsRoleName(String name) {
    Integer count = jdbcTemplate.queryForObject(
        "SELECT COUNT(1) FROM roles WHERE name = ?",
        Integer.class,
        name
    );
    return count != null && count > 0;
  }

  public Long insertRole(String name, String description, List<Long> resourceIds) {
    KeyHolder keyHolder = new GeneratedKeyHolder();
    jdbcTemplate.update(connection -> {
      PreparedStatement ps = connection.prepareStatement(
          "INSERT INTO roles (name, description) VALUES (?, ?)",
          Statement.RETURN_GENERATED_KEYS
      );
      ps.setString(1, name);
      ps.setString(2, description);
      return ps;
    }, keyHolder);
    Long roleId = Optional.ofNullable(keyHolder.getKey())
        .map(Number::longValue)
        .orElseThrow(() -> new IllegalStateException("创建角色失败"));
    replaceRoleResources(roleId, resourceIds == null ? List.of() : resourceIds);
    return roleId;
  }

  public void updateRole(Long id, String name, String description) {
    jdbcTemplate.update(
        "UPDATE roles SET name = ?, description = ? WHERE id = ?",
        name,
        description,
        id
    );
  }

  public void replaceRoleResources(Long roleId, List<Long> resourceIds) {
    jdbcTemplate.update("DELETE FROM role_resources WHERE role_id = ?", roleId);
    if (resourceIds == null || resourceIds.isEmpty()) {
      return;
    }
    for (Long resourceId : resourceIds) {
      jdbcTemplate.update(
          "INSERT INTO role_resources (role_id, resource_id) VALUES (?, ?)",
          roleId,
          resourceId
      );
    }
  }

  public void deleteRole(Long id) {
    jdbcTemplate.update("DELETE FROM roles WHERE id = ?", id);
  }

  public List<Resource> listResources() {
    return jdbcTemplate.query(
        "SELECT id, code, name FROM resources ORDER BY id ASC",
        (rs, rowNum) -> {
          Resource resource = new Resource();
          resource.setId(rs.getLong("id"));
          resource.setCode(rs.getString("code"));
          resource.setName(rs.getString("name"));
          return resource;
        }
    );
  }

  public List<Resource> listResourcesByIds(List<Long> ids) {
    if (ids == null || ids.isEmpty()) {
      return List.of();
    }
    String inClause = placeholders(ids);
    return jdbcTemplate.query(
        "SELECT id, code, name FROM resources WHERE id IN (" + inClause + ")",
        (rs, rowNum) -> {
          Resource resource = new Resource();
          resource.setId(rs.getLong("id"));
          resource.setCode(rs.getString("code"));
          resource.setName(rs.getString("name"));
          return resource;
        },
        ids.toArray()
    );
  }

  public Optional<Resource> findResourceById(Long id) {
    List<Resource> resources = jdbcTemplate.query(
        "SELECT id, code, name FROM resources WHERE id = ?",
        (rs, rowNum) -> {
          Resource resource = new Resource();
          resource.setId(rs.getLong("id"));
          resource.setCode(rs.getString("code"));
          resource.setName(rs.getString("name"));
          return resource;
        },
        id
    );
    return resources.stream().findFirst();
  }

  public Long insertResource(String code, String name) {
    KeyHolder keyHolder = new GeneratedKeyHolder();
    jdbcTemplate.update(connection -> {
      PreparedStatement ps = connection.prepareStatement(
          "INSERT INTO resources (code, name) VALUES (?, ?)",
          Statement.RETURN_GENERATED_KEYS
      );
      ps.setString(1, code);
      ps.setString(2, name);
      return ps;
    }, keyHolder);
    return Optional.ofNullable(keyHolder.getKey())
        .map(Number::longValue)
        .orElseThrow(() -> new IllegalStateException("创建资源失败"));
  }

  public void updateResource(Long id, String code, String name) {
    jdbcTemplate.update(
        "UPDATE resources SET code = ?, name = ? WHERE id = ?",
        code,
        name,
        id
    );
  }

  public void deleteResource(Long id) {
    jdbcTemplate.update("DELETE FROM resources WHERE id = ?", id);
  }

  public List<Article> listAdminArticles() {
    return jdbcTemplate.query(
        "SELECT id, title, summary, content, author, views, published, created_at FROM articles ORDER BY created_at DESC",
        (rs, rowNum) -> mapArticle(rs)
    );
  }

  public Optional<Article> findArticleById(Long id) {
    List<Article> articles = jdbcTemplate.query(
        "SELECT id, title, summary, content, author, views, published, created_at FROM articles WHERE id = ?",
        (rs, rowNum) -> mapArticle(rs),
        id
    );
    return articles.stream().findFirst();
  }

  public Optional<Article> findPublishedArticleById(Long id) {
    List<Article> articles = jdbcTemplate.query(
        "SELECT id, title, summary, content, author, views, published, created_at FROM articles WHERE id = ? AND published = 1",
        (rs, rowNum) -> mapArticle(rs),
        id
    );
    return articles.stream().findFirst();
  }

  public Long insertArticle(String title, String summary, String content, String author, boolean published,
      Instant createdAt) {
    KeyHolder keyHolder = new GeneratedKeyHolder();
    jdbcTemplate.update(connection -> {
      PreparedStatement ps = connection.prepareStatement(
          "INSERT INTO articles (title, summary, content, author, views, published, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
          Statement.RETURN_GENERATED_KEYS
      );
      ps.setString(1, title);
      ps.setString(2, summary);
      ps.setString(3, content);
      ps.setString(4, author);
      ps.setLong(5, 0L);
      ps.setBoolean(6, published);
      ps.setTimestamp(7, Timestamp.from(createdAt));
      return ps;
    }, keyHolder);
    return Optional.ofNullable(keyHolder.getKey())
        .map(Number::longValue)
        .orElseThrow(() -> new IllegalStateException("创建文章失败"));
  }

  public void updateArticle(Long id, String title, String summary, String content, String author,
      boolean published) {
    jdbcTemplate.update(
        "UPDATE articles SET title = ?, summary = ?, content = ?, author = ?, published = ? WHERE id = ?",
        title,
        summary,
        content,
        author,
        published,
        id
    );
  }

  public void incrementArticleViews(Long id) {
    jdbcTemplate.update("UPDATE articles SET views = views + 1 WHERE id = ?", id);
  }

  public void deleteArticle(Long id) {
    jdbcTemplate.update("DELETE FROM articles WHERE id = ?", id);
  }

  public List<Article> listPublicArticles() {
    return jdbcTemplate.query(
        "SELECT id, title, summary, content, author, views, published, created_at FROM articles WHERE published = 1 ORDER BY created_at DESC",
        (rs, rowNum) -> mapArticle(rs)
    );
  }

  public List<Article> top10Articles() {
    return jdbcTemplate.query(
        "SELECT id, title, summary, content, author, views, published, created_at FROM articles WHERE published = 1 ORDER BY views DESC LIMIT 10",
        (rs, rowNum) -> mapArticle(rs)
    );
  }

  public List<BannedWord> listBannedWords() {
    return jdbcTemplate.query(
        "SELECT id, word FROM banned_words ORDER BY id ASC",
        (rs, rowNum) -> {
          BannedWord bannedWord = new BannedWord();
          bannedWord.setId(rs.getLong("id"));
          bannedWord.setWord(rs.getString("word"));
          return bannedWord;
        }
    );
  }

  public Long insertBannedWord(String word) {
    KeyHolder keyHolder = new GeneratedKeyHolder();
    jdbcTemplate.update(connection -> {
      PreparedStatement ps = connection.prepareStatement(
          "INSERT INTO banned_words (word) VALUES (?)",
          Statement.RETURN_GENERATED_KEYS
      );
      ps.setString(1, word);
      return ps;
    }, keyHolder);
    return Optional.ofNullable(keyHolder.getKey())
        .map(Number::longValue)
        .orElseThrow(() -> new IllegalStateException("创建违禁词失败"));
  }

  public void deleteBannedWord(Long id) {
    jdbcTemplate.update("DELETE FROM banned_words WHERE id = ?", id);
  }

  public List<Comment> listAdminComments() {
    return jdbcTemplate.query(
        "SELECT id, article_id, user_id, username, content, created_at FROM comments ORDER BY created_at DESC",
        (rs, rowNum) -> mapComment(rs)
    );
  }

  public List<Comment> listCommentsByArticleId(Long articleId) {
    return jdbcTemplate.query(
        "SELECT id, article_id, user_id, username, content, created_at FROM comments WHERE article_id = ? ORDER BY created_at DESC",
        (rs, rowNum) -> mapComment(rs),
        articleId
    );
  }

  public Optional<Comment> findCommentById(Long id) {
    List<Comment> comments = jdbcTemplate.query(
        "SELECT id, article_id, user_id, username, content, created_at FROM comments WHERE id = ?",
        (rs, rowNum) -> mapComment(rs),
        id
    );
    return comments.stream().findFirst();
  }

  public Long insertComment(Long articleId, Long userId, String username, String content, Instant createdAt) {
    KeyHolder keyHolder = new GeneratedKeyHolder();
    jdbcTemplate.update(connection -> {
      PreparedStatement ps = connection.prepareStatement(
          "INSERT INTO comments (article_id, user_id, username, content, created_at) VALUES (?, ?, ?, ?, ?)",
          Statement.RETURN_GENERATED_KEYS
      );
      ps.setLong(1, articleId);
      ps.setLong(2, userId);
      ps.setString(3, username);
      ps.setString(4, content);
      ps.setTimestamp(5, Timestamp.from(createdAt));
      return ps;
    }, keyHolder);
    return Optional.ofNullable(keyHolder.getKey())
        .map(Number::longValue)
        .orElseThrow(() -> new IllegalStateException("创建评论失败"));
  }

  public void deleteComment(Long id) {
    jdbcTemplate.update("DELETE FROM comments WHERE id = ?", id);
  }

  private List<Long> listRoleIdsByUserId(Long userId) {
    return jdbcTemplate.query(
        "SELECT role_id FROM user_roles WHERE user_id = ? ORDER BY role_id ASC",
        (rs, rowNum) -> rs.getLong("role_id"),
        userId
    );
  }

  private Map<Long, List<Long>> listRoleIdsByUserIds(List<Long> userIds) {
    if (userIds == null || userIds.isEmpty()) {
      return Map.of();
    }
    String inClause = placeholders(userIds);
    List<Map<String, Object>> rows = jdbcTemplate.queryForList(
        "SELECT user_id, role_id FROM user_roles WHERE user_id IN (" + inClause + ")",
        userIds.toArray()
    );
    Map<Long, List<Long>> roleMap = new HashMap<>();
    for (Map<String, Object> row : rows) {
      Long userId = ((Number) row.get("user_id")).longValue();
      Long roleId = ((Number) row.get("role_id")).longValue();
      roleMap.computeIfAbsent(userId, key -> new ArrayList<>()).add(roleId);
    }
    roleMap.values().forEach(list -> list.sort(Long::compareTo));
    return roleMap;
  }

  private List<Long> listResourceIdsByRoleId(Long roleId) {
    return jdbcTemplate.query(
        "SELECT resource_id FROM role_resources WHERE role_id = ? ORDER BY resource_id ASC",
        (rs, rowNum) -> rs.getLong("resource_id"),
        roleId
    );
  }

  private Map<Long, List<Long>> listResourceIdsByRoleIds(List<Long> roleIds) {
    if (roleIds == null || roleIds.isEmpty()) {
      return Map.of();
    }
    String inClause = placeholders(roleIds);
    List<Map<String, Object>> rows = jdbcTemplate.queryForList(
        "SELECT role_id, resource_id FROM role_resources WHERE role_id IN (" + inClause + ")",
        roleIds.toArray()
    );
    Map<Long, List<Long>> resourceMap = new HashMap<>();
    for (Map<String, Object> row : rows) {
      Long roleId = ((Number) row.get("role_id")).longValue();
      Long resourceId = ((Number) row.get("resource_id")).longValue();
      resourceMap.computeIfAbsent(roleId, key -> new ArrayList<>()).add(resourceId);
    }
    resourceMap.values().forEach(list -> list.sort(Long::compareTo));
    return resourceMap;
  }

  private String placeholders(Collection<Long> ids) {
    return ids.stream().map(id -> "?").collect(Collectors.joining(","));
  }

  private Article mapArticle(java.sql.ResultSet rs) throws java.sql.SQLException {
    Article article = new Article();
    article.setId(rs.getLong("id"));
    article.setTitle(rs.getString("title"));
    article.setSummary(rs.getString("summary"));
    article.setContent(rs.getString("content"));
    article.setAuthor(rs.getString("author"));
    article.setViews(rs.getLong("views"));
    article.setPublished(rs.getBoolean("published"));
    Timestamp createdAt = rs.getTimestamp("created_at");
    article.setCreatedAt(createdAt == null ? null : createdAt.toInstant());
    return article;
  }

  private Comment mapComment(java.sql.ResultSet rs) throws java.sql.SQLException {
    Comment comment = new Comment();
    comment.setId(rs.getLong("id"));
    comment.setArticleId(rs.getLong("article_id"));
    comment.setUserId(rs.getLong("user_id"));
    comment.setUsername(rs.getString("username"));
    comment.setContent(rs.getString("content"));
    Timestamp createdAt = rs.getTimestamp("created_at");
    comment.setCreatedAt(createdAt == null ? null : createdAt.toInstant());
    return comment;
  }
}
