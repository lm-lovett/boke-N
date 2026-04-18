package com.boke.blog.service;

import com.boke.blog.dto.ArticleDetailResponse;
import com.boke.blog.dto.ArticleRequest;
import com.boke.blog.dto.BannedWordRequest;
import com.boke.blog.dto.CommentRequest;
import com.boke.blog.dto.LoginResponse;
import com.boke.blog.dto.RegisterRequest;
import com.boke.blog.dto.ResourceRequest;
import com.boke.blog.dto.RoleRequest;
import com.boke.blog.dto.UserRequest;
import com.boke.blog.model.Article;
import com.boke.blog.model.BannedWord;
import com.boke.blog.model.Comment;
import com.boke.blog.model.Resource;
import com.boke.blog.model.Role;
import com.boke.blog.model.User;
import com.boke.blog.repository.BlogJdbcRepository;
import com.boke.blog.security.AuthPrincipal;
import com.boke.blog.security.JwtService;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class BlogService {

  private final BlogJdbcRepository repo;
  private final JwtService jwtService;
  private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

  public BlogService(BlogJdbcRepository repo, JwtService jwtService) {
    this.repo = repo;
    this.jwtService = jwtService;
  }

  public LoginResponse login(String username, String password) {
    if (blank(username) || blank(password)) {
      throw new IllegalArgumentException("用户名和密码不能为空");
    }
    User user = repo.findUserByUsername(username)
        .orElseThrow(() -> new IllegalArgumentException("用户名或密码错误"));
    if (!passwordEncoder.matches(password, user.getPasswordHash())) {
      throw new IllegalArgumentException("用户名或密码错误");
    }

    List<Role> roles = repo.listRolesByIds(user.getRoleIds());
    List<Long> resourceIds = roles.stream().flatMap(r -> r.getResourceIds().stream()).distinct().toList();
    List<Resource> resources = repo.listResourcesByIds(resourceIds);
    boolean isAdmin = roles.stream().anyMatch(r -> "admin".equals(r.getName()));

    String token = jwtService.issueToken(user.getId(), user.getUsername(), user.getRoleIds(), isAdmin);
    return new LoginResponse(token, sanitizeUser(user), roles, resources);
  }

  public Map<String, Object> register(RegisterRequest request) {
    if (request == null || blank(request.username()) || blank(request.password())) {
      throw new IllegalArgumentException("用户名和密码不能为空");
    }
    if (repo.existsUserByUsername(request.username())) {
      throw new IllegalArgumentException("用户名已存在");
    }

    Role reader = repo.findRoleByName("reader")
        .orElseThrow(() -> new IllegalArgumentException("reader 角色不存在"));

    Long userId = repo.insertUser(
        request.username(),
        blank(request.nickname()) ? request.username() : request.nickname(),
        passwordEncoder.encode(request.password()),
        List.of(reader.getId())
    );
    User saved = repo.findUserById(userId).orElseThrow(() -> new IllegalStateException("用户创建失败"));
    return sanitizeUser(saved);
  }

  public List<Role> listRoles() {
    return repo.listRoles();
  }

  public Role createRole(RoleRequest request) {
    if (request == null || blank(request.name())) {
      throw new IllegalArgumentException("角色名不能为空");
    }
    if (repo.existsRoleName(request.name())) {
      throw new IllegalArgumentException("角色名已存在");
    }
    Long roleId = repo.insertRole(
        request.name(),
        Objects.requireNonNullElse(request.description(), ""),
        sanitizeLongList(request.resourceIds())
    );
    return repo.findRoleById(roleId).orElseThrow(() -> new IllegalStateException("角色创建失败"));
  }

  public Role updateRole(Long id, RoleRequest request) {
    Role role = repo.findRoleById(id).orElseThrow(() -> new IllegalArgumentException("角色不存在"));
    if (request == null) {
      return role;
    }
    String nextName = blank(request.name()) ? role.getName() : request.name();
    String nextDesc = request.description() == null ? role.getDescription() : request.description();
    repo.updateRole(id, nextName, nextDesc);
    if (request.resourceIds() != null) {
      repo.replaceRoleResources(id, sanitizeLongList(request.resourceIds()));
    }
    return repo.findRoleById(id).orElseThrow(() -> new IllegalStateException("角色更新失败"));
  }

  public void deleteRole(Long id) {
    if (repo.findRoleById(id).isEmpty()) {
      throw new IllegalArgumentException("角色不存在");
    }
    repo.deleteRole(id);
  }

  public List<Map<String, Object>> listUsers() {
    return repo.listUsers().stream().map(this::sanitizeUser).toList();
  }

  public Map<String, Object> createUser(UserRequest request) {
    if (request == null || blank(request.username()) || blank(request.password())) {
      throw new IllegalArgumentException("用户名和密码不能为空");
    }
    if (repo.existsUserByUsername(request.username())) {
      throw new IllegalArgumentException("用户名已存在");
    }
    Long userId = repo.insertUser(
        request.username(),
        blank(request.nickname()) ? request.username() : request.nickname(),
        passwordEncoder.encode(request.password()),
        sanitizeLongList(request.roleIds())
    );
    User saved = repo.findUserById(userId).orElseThrow(() -> new IllegalStateException("用户创建失败"));
    return sanitizeUser(saved);
  }

  public Map<String, Object> updateUser(Long id, UserRequest request) {
    User existing = repo.findUserById(id).orElseThrow(() -> new IllegalArgumentException("用户不存在"));
    if (request == null) {
      return sanitizeUser(existing);
    }
    String nickname = request.nickname() == null ? existing.getNickname() : request.nickname();
    String passwordHash = existing.getPasswordHash();
    if (!blank(request.password())) {
      passwordHash = passwordEncoder.encode(request.password());
    }
    repo.updateUser(id, nickname, passwordHash);
    if (request.roleIds() != null) {
      repo.replaceUserRoles(id, sanitizeLongList(request.roleIds()));
    }
    User updated = repo.findUserById(id).orElseThrow(() -> new IllegalStateException("用户更新失败"));
    return sanitizeUser(updated);
  }

  public void deleteUser(Long id) {
    if (repo.findUserById(id).isEmpty()) {
      throw new IllegalArgumentException("用户不存在");
    }
    repo.deleteUser(id);
  }

  public List<Resource> listResources() {
    return repo.listResources();
  }

  public Resource createResource(ResourceRequest request) {
    if (request == null || blank(request.code()) || blank(request.name())) {
      throw new IllegalArgumentException("资源编码和名称不能为空");
    }
    Long id = repo.insertResource(request.code(), request.name());
    return repo.findResourceById(id).orElseThrow(() -> new IllegalStateException("资源创建失败"));
  }

  public Resource updateResource(Long id, ResourceRequest request) {
    Resource existing = repo.findResourceById(id).orElseThrow(() -> new IllegalArgumentException("资源不存在"));
    if (request == null) {
      return existing;
    }
    String nextCode = blank(request.code()) ? existing.getCode() : request.code();
    String nextName = blank(request.name()) ? existing.getName() : request.name();
    repo.updateResource(id, nextCode, nextName);
    return repo.findResourceById(id).orElseThrow(() -> new IllegalStateException("资源更新失败"));
  }

  public void deleteResource(Long id) {
    if (repo.findResourceById(id).isEmpty()) {
      throw new IllegalArgumentException("资源不存在");
    }
    repo.deleteResource(id);
  }

  public List<Article> listAdminArticles() {
    return repo.listAdminArticles();
  }

  public Article createArticle(ArticleRequest request, AuthPrincipal principal) {
    if (request == null || blank(request.title()) || blank(request.content())) {
      throw new IllegalArgumentException("文章标题和内容不能为空");
    }
    Long articleId = repo.insertArticle(
        request.title(),
        Objects.requireNonNullElse(request.summary(), ""),
        request.content(),
        blank(request.author()) ? principal.username() : request.author(),
        request.published() == null || request.published(),
        Instant.now()
    );
    return repo.findArticleById(articleId).orElseThrow(() -> new IllegalStateException("文章创建失败"));
  }

  public Article updateArticle(Long id, ArticleRequest request) {
    Article existing = repo.findArticleById(id).orElseThrow(() -> new IllegalArgumentException("文章不存在"));
    if (request == null) {
      return existing;
    }
    repo.updateArticle(
        id,
        request.title() == null ? existing.getTitle() : request.title(),
        request.summary() == null ? existing.getSummary() : request.summary(),
        request.content() == null ? existing.getContent() : request.content(),
        request.author() == null ? existing.getAuthor() : request.author(),
        request.published() == null ? Boolean.TRUE.equals(existing.getPublished()) : request.published()
    );
    return repo.findArticleById(id).orElseThrow(() -> new IllegalStateException("文章更新失败"));
  }

  public void deleteArticle(Long id) {
    if (repo.findArticleById(id).isEmpty()) {
      throw new IllegalArgumentException("文章不存在");
    }
    repo.deleteArticle(id);
  }

  public List<BannedWord> listBannedWords() {
    return repo.listBannedWords();
  }

  public BannedWord createBannedWord(BannedWordRequest request) {
    if (request == null || blank(request.word())) {
      throw new IllegalArgumentException("违禁词不能为空");
    }
    Long id = repo.insertBannedWord(request.word());
    return repo.listBannedWords().stream()
        .filter(item -> item.getId().equals(id))
        .findFirst()
        .orElseThrow(() -> new IllegalStateException("违禁词创建失败"));
  }

  public void deleteBannedWord(Long id) {
    boolean exists = repo.listBannedWords().stream().anyMatch(item -> item.getId().equals(id));
    if (!exists) {
      throw new IllegalArgumentException("违禁词不存在");
    }
    repo.deleteBannedWord(id);
  }

  public List<Comment> listAdminComments() {
    return repo.listAdminComments();
  }

  public void deleteComment(Long id) {
    if (repo.findCommentById(id).isEmpty()) {
      throw new IllegalArgumentException("评论不存在");
    }
    repo.deleteComment(id);
  }

  public List<Article> listPublicArticles() {
    return repo.listPublicArticles();
  }

  public List<Article> top10Articles() {
    return repo.top10Articles();
  }

  public ArticleDetailResponse articleDetail(Long id) {
    Article article = repo.findPublishedArticleById(id)
        .orElseThrow(() -> new IllegalArgumentException("文章不存在"));
    repo.incrementArticleViews(id);
    Article refreshed = repo.findPublishedArticleById(id)
        .orElseThrow(() -> new IllegalArgumentException("文章不存在"));
    List<Comment> comments = repo.listCommentsByArticleId(id);
    return new ArticleDetailResponse(refreshed, comments);
  }

  public Comment createComment(Long articleId, CommentRequest request, AuthPrincipal principal) {
    if (request == null || blank(request.content())) {
      throw new IllegalArgumentException("评论内容不能为空");
    }
    Article article = repo.findPublishedArticleById(articleId)
        .orElseThrow(() -> new IllegalArgumentException("文章不存在"));

    for (BannedWord word : repo.listBannedWords()) {
      if (request.content().contains(word.getWord())) {
        throw new IllegalArgumentException("评论包含违禁词: " + word.getWord());
      }
    }

    User user = repo.findUserById(principal.userId())
        .orElseThrow(() -> new IllegalArgumentException("用户不存在"));

    Long commentId = repo.insertComment(article.getId(), user.getId(), user.getUsername(), request.content(),
        Instant.now());
    return repo.findCommentById(commentId).orElseThrow(() -> new IllegalStateException("评论创建失败"));
  }

  public Map<String, Object> weather(String city) {
    String finalCity = blank(city) ? "上海市" : city;
    Map<String, Object> map = new HashMap<>();
    map.put("city", finalCity);
    map.put("weather", "多云");
    map.put("temperature", "18~24°C");
    map.put("humidity", "62%");
    map.put("tip", "当前为演示天气数据，可后续接入真实天气 API。");
    map.put("updatedAt", Instant.now());
    return map;
  }

  public AuthPrincipal parseToken(String authorizationHeader) {
    if (blank(authorizationHeader) || !authorizationHeader.startsWith("Bearer ")) {
      throw new SecurityException("未登录或登录已过期");
    }
    String token = authorizationHeader.substring("Bearer ".length());
    try {
      return jwtService.parseToken(token);
    } catch (Exception e) {
      throw new SecurityException("未登录或登录已过期");
    }
  }

  public AuthPrincipal requireAdmin(String authorizationHeader) {
    AuthPrincipal principal = parseToken(authorizationHeader);
    if (!principal.admin()) {
      throw new SecurityException("需要管理员权限");
    }
    return principal;
  }

  private boolean blank(String value) {
    return value == null || value.isBlank();
  }

  private List<Long> sanitizeLongList(List<Long> values) {
    if (values == null) {
      return List.of();
    }
    Set<Long> distinct = values.stream().filter(Objects::nonNull).filter(v -> v > 0)
        .collect(Collectors.toCollection(java.util.LinkedHashSet::new));
    return List.copyOf(distinct);
  }

  private Map<String, Object> sanitizeUser(User user) {
    Map<String, Object> map = new HashMap<>();
    map.put("id", user.getId());
    map.put("username", user.getUsername());
    map.put("nickname", user.getNickname());
    map.put("roleIds", user.getRoleIds());
    return map;
  }
}
