package com.knowledgehub.api.article;

import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Repository;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

/**
 * local プロファイル用のインメモリ実装。AWS 環境なしでフロントエンド込みの
 * 動作確認ができるようにするためのもの。再起動でデータは消える。
 */
@Repository
@Profile("local")
public class InMemoryArticleRepository implements ArticleRepository {

    private final Map<String, Article> store = new ConcurrentHashMap<>();

    @Override
    public List<Article> findAll() {
        return store.values().stream()
                .sorted(Comparator.comparing(Article::getUpdatedAt).reversed())
                .toList();
    }

    @Override
    public List<Article> findByCategory(String category) {
        return store.values().stream()
                .filter(a -> category.equals(a.getCategory()))
                .sorted(Comparator.comparing(Article::getUpdatedAt).reversed())
                .toList();
    }

    @Override
    public Optional<Article> findById(String id) {
        return Optional.ofNullable(store.get(id));
    }

    @Override
    public Article save(Article article) {
        store.put(article.getId(), article);
        return article;
    }

    @Override
    public void deleteById(String id) {
        store.remove(id);
    }
}
