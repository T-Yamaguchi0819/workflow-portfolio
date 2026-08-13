package com.knowledgehub.api.article;

import com.knowledgehub.api.article.dto.ArticleRequest;
import com.knowledgehub.api.common.NotFoundException;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

@Service
public class ArticleService {

    private final ArticleRepository repository;
    private final Clock clock;

    public ArticleService(ArticleRepository repository, Clock clock) {
        this.repository = repository;
        this.clock = clock;
    }

    /**
     * 一覧取得。category はリポジトリ (DynamoDB では GSI) で、
     * tag / キーワード q はアプリケーション側で絞り込む。
     */
    public List<Article> search(String category, String tag, String q) {
        List<Article> articles = (category == null || category.isBlank())
                ? repository.findAll()
                : repository.findByCategory(category);

        return articles.stream()
                .filter(a -> tag == null || tag.isBlank() || a.getTags().contains(tag))
                .filter(a -> matchesKeyword(a, q))
                .toList();
    }

    public Article getById(String id) {
        return repository.findById(id)
                .orElseThrow(() -> new NotFoundException("記事が見つかりません: " + id));
    }

    public Article create(ArticleRequest request) {
        Instant now = clock.instant();
        Article article = new Article();
        article.setId(UUID.randomUUID().toString());
        article.setCreatedAt(now);
        applyRequest(article, request, now);
        return repository.save(article);
    }

    public Article update(String id, ArticleRequest request) {
        Article article = getById(id);
        applyRequest(article, request, clock.instant());
        return repository.save(article);
    }

    public void delete(String id) {
        getById(id); // 存在しない ID の削除は 404 にする
        repository.deleteById(id);
    }

    private void applyRequest(Article article, ArticleRequest request, Instant now) {
        article.setTitle(request.title().trim());
        article.setBody(request.body());
        article.setCategory(request.category().trim());
        article.setTags(request.tags() == null
                ? List.of()
                : request.tags().stream().map(String::trim).filter(t -> !t.isEmpty()).distinct().toList());
        article.setUpdatedAt(now);
    }

    private boolean matchesKeyword(Article article, String q) {
        if (q == null || q.isBlank()) {
            return true;
        }
        String keyword = q.toLowerCase(Locale.ROOT);
        return article.getTitle().toLowerCase(Locale.ROOT).contains(keyword)
                || article.getBody().toLowerCase(Locale.ROOT).contains(keyword);
    }
}
