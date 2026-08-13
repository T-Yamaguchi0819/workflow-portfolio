package com.knowledgehub.api.article;

import com.knowledgehub.api.article.dto.ArticleRequest;
import com.knowledgehub.api.common.NotFoundException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ArticleServiceTest {

    private static final Instant FIXED_NOW = Instant.parse("2026-01-15T09:00:00Z");

    private ArticleService service;

    @BeforeEach
    void setUp() {
        service = new ArticleService(
                new InMemoryArticleRepository(),
                Clock.fixed(FIXED_NOW, ZoneOffset.UTC));
    }

    private Article create(String title, String body, String category, List<String> tags) {
        return service.create(new ArticleRequest(title, body, category, tags));
    }

    @Nested
    class Create {

        @Test
        void ID_と作成更新日時が採番される() {
            Article article = create("タイトル", "本文", "IT-FAQ", List.of("VPN"));

            assertThat(article.getId()).isNotBlank();
            assertThat(article.getCreatedAt()).isEqualTo(FIXED_NOW);
            assertThat(article.getUpdatedAt()).isEqualTo(FIXED_NOW);
        }

        @Test
        void タグは空白除去と重複排除される() {
            Article article = create("t", "b", "c", List.of(" VPN ", "VPN", "", "ネットワーク"));

            assertThat(article.getTags()).containsExactly("VPN", "ネットワーク");
        }

        @Test
        void タグ_null_は空リストになる() {
            Article article = create("t", "b", "c", null);

            assertThat(article.getTags()).isEmpty();
        }
    }

    @Nested
    class Search {

        @BeforeEach
        void seed() {
            create("VPN 接続手順", "VPN の設定方法", "IT-FAQ", List.of("VPN"));
            create("経費精算ルール", "締め日は25日", "総務", List.of("経費"));
            create("プリンタ設定", "ドライバのインストール", "IT-FAQ", List.of("プリンタ"));
        }

        @Test
        void 条件なしは全件返す() {
            assertThat(service.search(null, null, null)).hasSize(3);
        }

        @Test
        void カテゴリで絞り込める() {
            List<Article> result = service.search("IT-FAQ", null, null);

            assertThat(result).hasSize(2)
                    .allMatch(a -> a.getCategory().equals("IT-FAQ"));
        }

        @Test
        void タグで絞り込める() {
            List<Article> result = service.search(null, "経費", null);

            assertThat(result).hasSize(1);
            assertThat(result.get(0).getTitle()).isEqualTo("経費精算ルール");
        }

        @Test
        void キーワードはタイトルと本文の両方に一致する() {
            assertThat(service.search(null, null, "VPN")).hasSize(1);
            assertThat(service.search(null, null, "25日")).hasSize(1);
            assertThat(service.search(null, null, "存在しない語")).isEmpty();
        }

        @Test
        void カテゴリとキーワードの複合条件() {
            List<Article> result = service.search("IT-FAQ", null, "ドライバ");

            assertThat(result).hasSize(1);
            assertThat(result.get(0).getTitle()).isEqualTo("プリンタ設定");
        }
    }

    @Nested
    class UpdateAndDelete {

        @Test
        void 更新でタイトルと更新日時が変わり作成日時は変わらない() {
            Article article = create("旧タイトル", "本文", "IT-FAQ", List.of());

            Article updated = service.update(article.getId(),
                    new ArticleRequest("新タイトル", "新本文", "総務", List.of("tag")));

            assertThat(updated.getTitle()).isEqualTo("新タイトル");
            assertThat(updated.getCategory()).isEqualTo("総務");
            assertThat(updated.getCreatedAt()).isEqualTo(FIXED_NOW);
        }

        @Test
        void 存在しないIDの更新は404() {
            assertThatThrownBy(() -> service.update("missing",
                    new ArticleRequest("t", "b", "c", List.of())))
                    .isInstanceOf(NotFoundException.class);
        }

        @Test
        void 削除すると取得できなくなる() {
            Article article = create("t", "b", "c", List.of());

            service.delete(article.getId());

            assertThatThrownBy(() -> service.getById(article.getId()))
                    .isInstanceOf(NotFoundException.class);
        }

        @Test
        void 存在しないIDの削除は404() {
            assertThatThrownBy(() -> service.delete("missing"))
                    .isInstanceOf(NotFoundException.class);
        }
    }
}
