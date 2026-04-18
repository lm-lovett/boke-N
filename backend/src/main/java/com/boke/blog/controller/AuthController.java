package com.boke.blog.controller;

import com.boke.blog.common.ApiResponse;
import com.boke.blog.dto.LoginRequest;
import com.boke.blog.dto.LoginResponse;
import com.boke.blog.dto.RegisterRequest;
import com.boke.blog.service.BlogService;
import java.util.Map;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

  private final BlogService blogService;

  public AuthController(BlogService blogService) {
    this.blogService = blogService;
  }

  @PostMapping("/login")
  public ApiResponse<LoginResponse> login(@RequestBody LoginRequest request) {
    return ApiResponse.ok(blogService.login(request.username(), request.password()));
  }

  @PostMapping("/register")
  public ApiResponse<Map<String, Object>> register(@RequestBody RegisterRequest request) {
    return ApiResponse.ok(blogService.register(request));
  }
}
