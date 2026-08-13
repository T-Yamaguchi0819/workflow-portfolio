package com.knowledgehub.api.article;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Repository;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbEnhancedClient;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbTable;
import software.amazon.awssdk.enhanced.dynamodb.Key;
import software.amazon.awssdk.enhanced.dynamodb.TableSchema;
import software.amazon.awssdk.enhanced.dynamodb.model.QueryConditional;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;

/**
 * DynamoDB 実装。一覧は Scan、カテゴリ絞り込みは GSI (category-index) の Query。
 * ポートフォリオ規模 (数百件) を前提とした設計で、大規模化する場合は
 * ページネーション (ExclusiveStartKey) と検索基盤 (OpenSearch 等) の導入が前提になる。
 */
@Repository
@Profile("!local")
public class DynamoDbArticleRepository implements ArticleRepository {

    private final DynamoDbTable<Article> table;

    public DynamoDbArticleRepository(
            DynamoDbEnhancedClient enhancedClient,
            @Value("${app.dynamodb.table-name}") String tableName) {
        this.table = enhancedClient.table(tableName, TableSchema.fromBean(Article.class));
    }

    @Override
    public List<Article> findAll() {
        List<Article> articles = new ArrayList<>();
        table.scan().items().forEach(articles::add);
        articles.sort(Comparator.comparing(Article::getUpdatedAt).reversed());
        return articles;
    }

    @Override
    public List<Article> findByCategory(String category) {
        List<Article> articles = new ArrayList<>();
        table.index("category-index")
                .query(QueryConditional.keyEqualTo(Key.builder().partitionValue(category).build()))
                .forEach(page -> articles.addAll(page.items()));
        articles.sort(Comparator.comparing(Article::getUpdatedAt).reversed());
        return articles;
    }

    @Override
    public Optional<Article> findById(String id) {
        return Optional.ofNullable(table.getItem(Key.builder().partitionValue(id).build()));
    }

    @Override
    public Article save(Article article) {
        table.putItem(article);
        return article;
    }

    @Override
    public void deleteById(String id) {
        table.deleteItem(Key.builder().partitionValue(id).build());
    }
}
