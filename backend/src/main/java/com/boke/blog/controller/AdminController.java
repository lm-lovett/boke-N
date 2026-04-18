package com.boke.blog.controller;

import com.boke.blog.common.ApiResponse;
import com.boke.blog.dto.ArticleRequest;
import com.boke.blog.dto.BannedWordRequest;
import com.boke.blog.dto.ResourceRequest;
import com.boke.blog.dto.RoleRequest;
import com.boke.blog.dto.UserRequest;
import com.boke.blog.security.AuthPrincipal;
import com.boke.blog.service.BlogService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/admin")
public class AdminController {

  private final BlogService blogService;

  public AdminController(BlogService blogService) {
    this.blogService = blogService;
  }

  private AuthPrincipal requireAdmin(String authHeader) {
    return blogService.requireAdmin(authHeader);
  }

  @GetMapping("/roles")
  public ApiResponse<?> roles(@RequestHeader("Authorization") String authHeader) {
    requireAdmin(authHeader);
    return ApiResponse.ok(blogService.listRoles());
  }

  @PostMapping("/roles")
  public ApiResponse<?> createRole(@RequestHeader("Authorization") String authHeader,
      @RequestBody RoleRequest request) {
    requireAdmin(authHeader);
    return ApiResponse.ok(blogService.createRole(request));
  }

  @PutMapping("/roles/{id}")
  public ApiResponse<?> updateRole(@RequestHeader("Authorization") String authHeader,
      @PathVariable Long id, @RequestBody RoleRequest request) {
    requireAdmin(authHeader);
    return ApiResponse.ok(blogService.updateRole(id, request));
  }

  @DeleteMapping("/roles/{id}")
  public ApiResponse<?> deleteRole(@RequestHeader("Authorization") String authHeader,
      @PathVariable Long id) {
    requireAdmin(authHeader);
    blogService.deleteRole(id);
    return ApiResponse.ok("删除成功", null);
  }

  @GetMapping("/users")
  public ApiResponse<List<Map<String, Object>>> users(@RequestHeader("Authorization") String authHeader) {
    requireAdmin(authHeader);
    return ApiResponse.ok(blogService.listUsers());
  }

  @PostMapping("/users")
  public ApiResponse<Map<String, Object>> createUser(@RequestHeader("Authorization") String authHeader,
      @RequestBody UserRequest request) {
    requireAdmin(authHeader);
    return ApiResponse.ok(blogService.createUser(request));
  }

  @PutMapping("/users/{id}")
  public ApiResponse<Map<String, Object>> updateUser(@RequestHeader("Authorization") String authHeader,
      @PathVariable Long id, @RequestBody UserRequest request) {
    requireAdmin(authHeader);
    return ApiResponse.ok(blogService.updateUser(id, request));
  }

  @DeleteMapping("/users/{id}")
  public ApiResponse<?> deleteUser(@RequestHeader("Authorization") String authHeader,
      @PathVariable Long id) {
    requireAdmin(authHeader);
    blogService.deleteUser(id);
    return ApiResponse.ok("删除成功", null);
  }

  @GetMapping("/resources")
  public ApiResponse<?> resources(@RequestHeader("Authorization") String authHeader) {
    requireAdmin(authHeader);
    return ApiResponse.ok(blogService.listResources());
  }

  @PostMapping("/resources")
  public ApiResponse<?> createResource(@RequestHeader("Authorization") String authHeader,
      @RequestBody ResourceRequest request) {
    requireAdmin(authHeader);
    return ApiResponse.ok(blogService.createResource(request));
  }

  @PutMapping("/resources/{id}")
  public ApiResponse<?> updateResource(@RequestHeader("Authorization") String authHeader,
      @PathVariable Long id, @RequestBody ResourceRequest request) {
    requireAdmin(authHeader);
    return ApiResponse.ok(blogService.updateResource(id, request));
  }

  @DeleteMapping("/resources/{id}")
  public ApiResponse<?> deleteResource(@RequestHeader("Authorization") String authHeader,
      @PathVariable Long id) {
    requireAdmin(authHeader);
    blogService.deleteResource(id);
    return ApiResponse.ok("删除成功", null);
  }

  @GetMapping("/articles")
  public ApiResponse<?> articles(@RequestHeader("Authorization") String authHeader) {
    requireAdmin(authHeader);
    return ApiResponse.ok(blogService.listAdminArticles());
  }

  @PostMapping("/articles")
  public ApiResponse<?> createArticle(@RequestHeader("Authorization") String authHeader,
      @RequestBody ArticleRequest request) {
    AuthPrincipal principal = requireAdmin(authHeader);
    return ApiResponse.ok(blogService.createArticle(request, principal));
  }

  @PutMapping("/articles/{id}")
  public ApiResponse<?> updateArticle(@RequestHeader("Authorization") String authHeader,
      @PathVariable Long id, @RequestBody ArticleRequest request) {
    requireAdmin(authHeader);
    return ApiResponse.ok(blogService.updateArticle(id, request));
  }

  @DeleteMapping("/articles/{id}")
  public ApiResponse<?> deleteArticle(@RequestHeader("Authorization") String authHeader,
      @PathVariable Long id) {
    requireAdmin(authHeader);
    blogService.deleteArticle(id);
    return ApiResponse.ok("删除成功", null);
  }

  @GetMapping("/banned-words")
  public ApiResponse<?> bannedWords(@RequestHeader("Authorization") String authHeader) {
    requireAdmin(authHeader);
    return ApiResponse.ok(blogService.listBannedWords());
  }

  @PostMapping("/banned-words")
  public ApiResponse<?> createBannedWord(@RequestHeader("Authorization") String authHeader,
      @RequestBody BannedWordRequest request) {
    requireAdmin(authHeader);
    return ApiResponse.ok(blogService.createBannedWord(request));
  }

  @DeleteMapping("/banned-words/{id}")
  public ApiResponse<?> deleteBannedWord(@RequestHeader("Authorization") String authHeader,
      @PathVariable Long id) {
    requireAdmin(authHeader);
    blogService.deleteBannedWord(id);
    return ApiResponse.ok("删除成功", null);
  }

  @GetMapping("/comments")
  public ApiResponse<?> comments(@RequestHeader("Authorization") String authHeader) {
    requireAdmin(authHeader);
    return ApiResponse.ok(blogService.listAdminComments());
  }

  @DeleteMapping("/comments/{id}")
  public ApiResponse<?> deleteComment(@RequestHeader("Authorization") String authHeader,
      @PathVariable Long id) {
    requireAdmin(authHeader);
    blogService.deleteComment(id);
    return ApiResponse.ok("删除成功", null);
  }
}
