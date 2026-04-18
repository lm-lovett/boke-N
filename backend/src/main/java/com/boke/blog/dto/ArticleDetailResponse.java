package com.boke.blog.dto;

import com.boke.blog.model.Article;
import com.boke.blog.model.Comment;
import java.util.List;

public record ArticleDetailResponse(Article article, List<Comment> comments) {
}
