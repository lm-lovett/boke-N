package com.boke.blog.common;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

  @ExceptionHandler(IllegalArgumentException.class)
  @ResponseStatus(HttpStatus.BAD_REQUEST)
  public ApiResponse<Void> handleIllegalArgument(IllegalArgumentException ex) {
    return ApiResponse.fail(ex.getMessage());
  }

  @ExceptionHandler(SecurityException.class)
  @ResponseStatus(HttpStatus.FORBIDDEN)
  public ApiResponse<Void> handleSecurity(SecurityException ex) {
    return ApiResponse.fail(ex.getMessage());
  }

  @ExceptionHandler(Exception.class)
  @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
  public ApiResponse<Void> handleException(Exception ex) {
    return ApiResponse.fail("服务器异常: " + ex.getMessage());
  }
}
