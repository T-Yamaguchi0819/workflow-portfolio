package com.knowledgehub.api.article.dto;

import com.knowledgehub.api.article.Article;

import java.time.Instant;
import java.util.List;

public record ArticleResponse(
        String id,
        String title,
        String body,
        String category,
        List<String> tags,
        Instant createdAt,
        Instant updatedAt
) {
    public static ArticleResponse from(Article article) {
        return new ArticleResponse(
                article.getId(),
                article.getTitle(),
                article.getBody(),
                article.getCategory(),
                article.getTags(),
                article.getCreatedAt(),
                article.getUpdatedAt()
        );
    }
}
