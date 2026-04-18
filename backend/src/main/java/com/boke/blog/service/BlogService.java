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
import com.boke.blog.repository.InMemoryRepository;
import com.boke.blog.security.AuthPrincipal;
import com.boke.blog.security.JwtService;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class BlogService {

  private final InMemoryRepository repo;
  private final JwtService jwtService;
  private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

  public BlogService(InMemoryRepository repo, JwtService jwtService) {
    this.repo = repo;
    this.jwtService = jwtService;
  }

  public LoginResponse login(String username, String password) {
    if (blank(username) || blank(password)) {
      throw new IllegalArgumentException("用户名和密码不能为空");
    }
    User user = repo.users().stream().filter(u -> u.getUsername().equals(username)).findFirst()
        .orElseThrow(() -> new IllegalArgumentException("用户名或密码错误"));
    if (!passwordEncoder.matches(password, user.getPasswordHash())) {
      throw new IllegalArgumentException("用户名或密码错误");
    }

    List<Role> roles = repo.roles().stream().filter(r -> user.getRoleIds().contains(r.getId())).toList();
    List<Long> resourceIds = roles.stream().flatMap(r -> r.getResourceIds().stream()).distinct().toList();
    List<Resource> resources = repo.resources().stream().filter(r -> resourceIds.contains(r.getId())).toList();
    boolean isAdmin = roles.stream().anyMatch(r -> "admin".equals(r.getName()));

    String token = jwtService.issueToken(user.getId(), user.getUsername(), user.getRoleIds(), isAdmin);
    return new LoginResponse(token, sanitizeUser(user), roles, resources);
  }

  public Map<String, Object> register(RegisterRequest request) {
    if (request == null || blank(request.username()) || blank(request.password())) {
      throw new IllegalArgumentException("用户名和密码不能为空");
    }
    boolean exists = repo.users().stream().anyMatch(u -> u.getUsername().equals(request.username()));
    if (exists) {
      throw new IllegalArgumentException("用户名已存在");
    }

    Role reader = repo.roles().stream().filter(r -> "reader".equals(r.getName())).findFirst()
        .orElseThrow(() -> new IllegalArgumentException("reader 角色不存在"));

    User user = new User();
    user.setId(repo.nextUserId());
    user.setUsername(request.username());
    user.setNickname(blank(request.nickname()) ? request.username() : request.nickname());
    user.setPasswordHash(passwordEncoder.encode(request.password()));
    user.setRoleIds(new ArrayList<>(List.of(reader.getId())));

    repo.users().add(user);
    return sanitizeUser(user);
  }

  public List<Role> listRoles() {
    return repo.roles();
  }

  public Role createRole(RoleRequest request) {
    requireAdminFields(request != null && !blank(request.name()), "角色名不能为空");
    boolean exists = repo.roles().stream().anyMatch(r -> r.getName().equals(request.name()));
    if (exists) {
      throw new IllegalArgumentException("角色名已存在");
    }
    Role role = new Role();
    role.setId(repo.nextRoleId());
    role.setName(request.name());
    role.setDescription(Objects.requireNonNullElse(request.description(), ""));
    role.setResourceIds(new ArrayList<>(Objects.requireNonNullElse(request.resourceIds(), List.of())));
    repo.roles().add(role);
    return role;
  }

  public Role updateRole(Long id, RoleRequest request) {
    Role role = findById(repo.roles(), id).orElseThrow(() -> new IllegalArgumentException("角色不存在"));
    if (request == null) {
      return role;
    }
    if (!blank(request.name())) {
      role.setName(request.name());
    }
    if (request.description() != null) {
      role.setDescription(request.description());
    }
    if (request.resourceIds() != null) {
      role.setResourceIds(new ArrayList<>(request.resourceIds()));
    }
    return role;
  }

  public void deleteRole(Long id) {
    repo.roles().removeIf(r -> r.getId().equals(id));
    for (User user : repo.users()) {
      user.getRoleIds().removeIf(roleId -> roleId.equals(id));
    }
  }

  public List<Map<String, Object>> listUsers() {
    return repo.users().stream().map(this::sanitizeUser).toList();
  }

  public Map<String, Object> createUser(UserRequest request) {
    if (request == null || blank(request.username()) || blank(request.password())) {
      throw new IllegalArgumentException("用户名和密码不能为空");
    }
    boolean exists = repo.users().stream().anyMatch(u -> u.getUsername().equals(request.username()));
    if (exists) {
      throw new IllegalArgumentException("用户名已存在");
    }
    User user = new User();
    user.setId(repo.nextUserId());
    user.setUsername(request.username());
    user.setNickname(blank(request.nickname()) ? request.username() : request.nickname());
    user.setPasswordHash(passwordEncoder.encode(request.password()));
    user.setRoleIds(new ArrayList<>(Objects.requireNonNullElse(request.roleIds(), List.of())));
    repo.users().add(user);
    return sanitizeUser(user);
  }

  public Map<String, Object> updateUser(Long id, UserRequest request) {
    User user = findById(repo.users(), id).orElseThrow(() -> new IllegalArgumentException("用户不存在"));
    if (request == null) {
      return sanitizeUser(user);
    }
    if (request.nickname() != null) {
      user.setNickname(request.nickname());
    }
    if (request.roleIds() != null) {
      user.setRoleIds(new ArrayList<>(request.roleIds()));
    }
    if (!blank(request.password())) {
      user.setPasswordHash(passwordEncoder.encode(request.password()));
    }
    return sanitizeUser(user);
  }

  public void deleteUser(Long id) {
    repo.users().removeIf(u -> u.getId().equals(id));
  }

  public List<Resource> listResources() {
    return repo.resources();
  }

  public Resource createResource(ResourceRequest request) {
    if (request == null || blank(request.code()) || blank(request.name())) {
      throw new IllegalArgumentException("资源编码和名称不能为空");
    }
    Resource resource = new Resource();
    resource.setId(repo.nextResourceId());
    resource.setCode(request.code());
    resource.setName(request.name());
    repo.resources().add(resource);
    return resource;
  }

  public Resource updateResource(Long id, ResourceRequest request) {
    Resource resource = findById(repo.resources(), id)
        .orElseThrow(() -> new IllegalArgumentException("资源不存在"));
    if (request == null) {
      return resource;
    }
    if (!blank(request.code())) {
      resource.setCode(request.code());
    }
    if (!blank(request.name())) {
      resource.setName(request.name());
    }
    return resource;
  }

  public void deleteResource(Long id) {
    repo.resources().removeIf(r -> r.getId().equals(id));
    for (Role role : repo.roles()) {
      role.getResourceIds().removeIf(resourceId -> resourceId.equals(id));
    }
  }

  public List<Article> listAdminArticles() {
    return repo.articles().stream().sorted(Comparator.comparing(Article::getCreatedAt).reversed()).toList();
  }

  public Article createArticle(ArticleRequest request, AuthPrincipal principal) {
    if (request == null || blank(request.title()) || blank(request.content())) {
      throw new IllegalArgumentException("文章标题和内容不能为空");
    }
    Article article = new Article();
    article.setId(repo.nextArticleId());
    article.setTitle(request.title());
    article.setSummary(Objects.requireNonNullElse(request.summary(), ""));
    article.setContent(request.content());
    article.setAuthor(blank(request.author()) ? principal.username() : request.author());
    article.setViews(0L);
    article.setPublished(request.published() == null || request.published());
    article.setCreatedAt(Instant.now());
    repo.articles().add(article);
    return article;
  }

  public Article updateArticle(Long id, ArticleRequest request) {
    Article article = findById(repo.articles(), id)
        .orElseThrow(() -> new IllegalArgumentException("文章不存在"));
    if (request == null) {
      return article;
    }
    if (request.title() != null) {
      article.setTitle(request.title());
    }
    if (request.summary() != null) {
      article.setSummary(request.summary());
    }
    if (request.content() != null) {
      article.setContent(request.content());
    }
    if (request.author() != null) {
      article.setAuthor(request.author());
    }
    if (request.published() != null) {
      article.setPublished(request.published());
    }
    return article;
  }

  public void deleteArticle(Long id) {
    repo.articles().removeIf(a -> a.getId().equals(id));
    repo.comments().removeIf(c -> c.getArticleId().equals(id));
  }

  public List<BannedWord> listBannedWords() {
    return repo.bannedWords();
  }

  public BannedWord createBannedWord(BannedWordRequest request) {
    if (request == null || blank(request.word())) {
      throw new IllegalArgumentException("违禁词不能为空");
    }
    BannedWord bannedWord = new BannedWord();
    bannedWord.setId(repo.nextBannedWordId());
    bannedWord.setWord(request.word());
    repo.bannedWords().add(bannedWord);
    return bannedWord;
  }

  public void deleteBannedWord(Long id) {
    repo.bannedWords().removeIf(word -> word.getId().equals(id));
  }

  public List<Comment> listAdminComments() {
    return repo.comments().stream().sorted(Comparator.comparing(Comment::getCreatedAt).reversed()).toList();
  }

  public void deleteComment(Long id) {
    repo.comments().removeIf(c -> c.getId().equals(id));
  }

  public List<Article> listPublicArticles() {
    return repo.articles().stream()
        .filter(article -> Boolean.TRUE.equals(article.getPublished()))
        .sorted(Comparator.comparing(Article::getCreatedAt).reversed())
        .toList();
  }

  public List<Article> top10Articles() {
    return repo.articles().stream()
        .filter(article -> Boolean.TRUE.equals(article.getPublished()))
        .sorted(Comparator.comparing(Article::getViews).reversed())
        .limit(10)
        .toList();
  }

  public ArticleDetailResponse articleDetail(Long id) {
    Article article = repo.articles().stream()
        .filter(a -> a.getId().equals(id) && Boolean.TRUE.equals(a.getPublished()))
        .findFirst()
        .orElseThrow(() -> new IllegalArgumentException("文章不存在"));
    article.setViews(article.getViews() + 1);
    List<Comment> comments = repo.comments().stream()
        .filter(c -> c.getArticleId().equals(id))
        .sorted(Comparator.comparing(Comment::getCreatedAt).reversed())
        .toList();
    return new ArticleDetailResponse(article, comments);
  }

  public Comment createComment(Long articleId, CommentRequest request, AuthPrincipal principal) {
    if (request == null || blank(request.content())) {
      throw new IllegalArgumentException("评论内容不能为空");
    }
    Article article = repo.articles().stream()
        .filter(a -> a.getId().equals(articleId) && Boolean.TRUE.equals(a.getPublished()))
        .findFirst()
        .orElseThrow(() -> new IllegalArgumentException("文章不存在"));
    for (BannedWord word : repo.bannedWords()) {
      if (request.content().contains(word.getWord())) {
        throw new IllegalArgumentException("评论包含违禁词: " + word.getWord());
      }
    }
    User user = repo.users().stream().filter(u -> u.getId().equals(principal.userId())).findFirst()
        .orElseThrow(() -> new IllegalArgumentException("用户不存在"));

    Comment comment = new Comment();
    comment.setId(repo.nextCommentId());
    comment.setArticleId(article.getId());
    comment.setUserId(user.getId());
    comment.setUsername(user.getUsername());
    comment.setContent(request.content());
    comment.setCreatedAt(Instant.now());

    repo.comments().add(comment);
    return comment;
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

  private void requireAdminFields(boolean condition, String message) {
    if (!condition) {
      throw new IllegalArgumentException(message);
    }
  }

  private boolean blank(String value) {
    return value == null || value.isBlank();
  }

  private Map<String, Object> sanitizeUser(User user) {
    Map<String, Object> map = new HashMap<>();
    map.put("id", user.getId());
    map.put("username", user.getUsername());
    map.put("nickname", user.getNickname());
    map.put("roleIds", user.getRoleIds());
    return map;
  }

  private <T> Optional<T> findById(List<T> list, Long id) {
    for (T item : list) {
      if (item instanceof Role role && role.getId().equals(id)) {
        return Optional.of(item);
      }
      if (item instanceof User user && user.getId().equals(id)) {
        return Optional.of(item);
      }
      if (item instanceof Resource resource && resource.getId().equals(id)) {
        return Optional.of(item);
      }
      if (item instanceof Article article && article.getId().equals(id)) {
        return Optional.of(item);
      }
      if (item instanceof BannedWord bannedWord && bannedWord.getId().equals(id)) {
        return Optional.of(item);
      }
      if (item instanceof Comment comment && comment.getId().equals(id)) {
        return Optional.of(item);
      }
    }
    return Optional.empty();
  }
}
