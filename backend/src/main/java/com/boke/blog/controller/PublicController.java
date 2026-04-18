package com.boke.blog.controller;

import com.boke.blog.common.ApiResponse;
import com.boke.blog.dto.CommentRequest;
import com.boke.blog.service.BlogService;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class PublicController {

  private final BlogService blogService;

  public PublicController(BlogService blogService) {
    this.blogService = blogService;
  }

  @GetMapping("/health")
  public ApiResponse<?> health() {
    return ApiResponse.ok(Map.of("ok", true));
  }

  @GetMapping("/articles")
  public ApiResponse<?> articles() {
    return ApiResponse.ok(blogService.listPublicArticles());
  }

  @GetMapping("/articles/top10")
  public ApiResponse<?> top10() {
    return ApiResponse.ok(blogService.top10Articles());
  }

  @GetMapping("/articles/{id}")
  public ApiResponse<?> articleDetail(@PathVariable Long id) {
    return ApiResponse.ok(blogService.articleDetail(id));
  }

  @PostMapping("/articles/{id}/comments")
  public ApiResponse<?> createComment(@PathVariable Long id,
      @RequestBody CommentRequest request,
      @RequestHeader("Authorization") String authHeader) {
    return ApiResponse.ok(blogService.createComment(id, request, blogService.parseToken(authHeader)));
  }

  @GetMapping("/weather")
  public ApiResponse<?> weather(@RequestParam(value = "city", required = false) String city) {
    return ApiResponse.ok(blogService.weather(city));
  }
}
