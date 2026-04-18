package com.boke.blog.dto;

public record ArticleRequest(String title, String summary, String content, String author, Boolean published) {
}
