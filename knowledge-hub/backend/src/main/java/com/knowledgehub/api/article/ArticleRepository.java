package com.knowledgehub.api.article;

import java.util.List;
import java.util.Optional;

/**
 * 記事の永続化層。実装は 2 つ:
 * - {@link DynamoDbArticleRepository}: 本番 (Lambda + DynamoDB) と DynamoDB Local
 * - {@link InMemoryArticleRepository}: local プロファイルでの起動用 (AWS 不要)
 */
public interface ArticleRepository {

    List<Article> findAll();

    List<Article> findByCategory(String category);

    Optional<Article> findById(String id);

    Article save(Article article);

    void deleteById(String id);
}
