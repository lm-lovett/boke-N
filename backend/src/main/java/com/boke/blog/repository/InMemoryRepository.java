package com.boke.blog.repository;

import com.boke.blog.model.Article;
import com.boke.blog.model.BannedWord;
import com.boke.blog.model.Comment;
import com.boke.blog.model.Resource;
import com.boke.blog.model.Role;
import com.boke.blog.model.User;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Component;

@Component
public class InMemoryRepository {

  private final AtomicLong userId = new AtomicLong(1);
  private final AtomicLong roleId = new AtomicLong(1);
  private final AtomicLong resourceId = new AtomicLong(1);
  private final AtomicLong articleId = new AtomicLong(1);
  private final AtomicLong bannedWordId = new AtomicLong(1);
  private final AtomicLong commentId = new AtomicLong(1);

  private final List<User> users = new ArrayList<>();
  private final List<Role> roles = new ArrayList<>();
  private final List<Resource> resources = new ArrayList<>();
  private final List<Article> articles = new ArrayList<>();
  private final List<BannedWord> bannedWords = new ArrayList<>();
  private final List<Comment> comments = new ArrayList<>();

  public InMemoryRepository() {
    seed();
  }

  private void seed() {
    Role adminRole = new Role();
    adminRole.setId(nextRoleId());
    adminRole.setName("admin");
    adminRole.setDescription("系统管理员");

    Role readerRole = new Role();
    readerRole.setId(nextRoleId());
    readerRole.setName("reader");
    readerRole.setDescription("普通用户");

    roles.add(adminRole);
    roles.add(readerRole);

    String[][] menuDefs = {
        {"role:manage", "角色管理"},
        {"user:manage", "用户管理"},
        {"resource:manage", "资源管理"},
        {"article:manage", "文章管理"},
        {"bannedword:manage", "违禁词管理"},
        {"comment:manage", "评论记录管理"}
    };
    for (String[] def : menuDefs) {
      Resource resource = new Resource();
      resource.setId(nextResourceId());
      resource.setCode(def[0]);
      resource.setName(def[1]);
      resources.add(resource);
      adminRole.getResourceIds().add(resource.getId());
    }

    BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    User admin = new User();
    admin.setId(nextUserId());
    admin.setUsername("admin");
    admin.setNickname("管理员");
    admin.setPasswordHash(encoder.encode("Admin123!"));
    admin.setRoleIds(new ArrayList<>(List.of(adminRole.getId())));

    User demo = new User();
    demo.setId(nextUserId());
    demo.setUsername("demo");
    demo.setNickname("示例用户");
    demo.setPasswordHash(encoder.encode("Demo123!"));
    demo.setRoleIds(new ArrayList<>(List.of(readerRole.getId())));

    users.add(admin);
    users.add(demo);

    BannedWord bw1 = new BannedWord();
    bw1.setId(nextBannedWordId());
    bw1.setWord("赌博");

    BannedWord bw2 = new BannedWord();
    bw2.setId(nextBannedWordId());
    bw2.setWord("诈骗");

    bannedWords.add(bw1);
    bannedWords.add(bw2);
  }

  public synchronized Long nextUserId() {
    return userId.getAndIncrement();
  }

  public synchronized Long nextRoleId() {
    return roleId.getAndIncrement();
  }

  public synchronized Long nextResourceId() {
    return resourceId.getAndIncrement();
  }

  public synchronized Long nextArticleId() {
    return articleId.getAndIncrement();
  }

  public synchronized Long nextBannedWordId() {
    return bannedWordId.getAndIncrement();
  }

  public synchronized Long nextCommentId() {
    return commentId.getAndIncrement();
  }

  public List<User> users() {
    return users;
  }

  public List<Role> roles() {
    return roles;
  }

  public List<Resource> resources() {
    return resources;
  }

  public List<Article> articles() {
    return articles;
  }

  public List<BannedWord> bannedWords() {
    return bannedWords;
  }

  public List<Comment> comments() {
    return comments;
  }
}
