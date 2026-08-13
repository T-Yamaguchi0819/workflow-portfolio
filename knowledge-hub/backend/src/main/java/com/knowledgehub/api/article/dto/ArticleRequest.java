package com.knowledgehub.api.article.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.util.List;

/**
 * 記事の作成・更新リクエスト。
 */
public record ArticleRequest(
        @NotBlank(message = "タイトルは必須です")
        @Size(max = 200, message = "タイトルは200文字以内で入力してください")
        String title,

        @NotBlank(message = "本文は必須です")
        @Size(max = 50_000, message = "本文は50,000文字以内で入力してください")
        String body,

        @NotBlank(message = "カテゴリは必須です")
        @Size(max = 50, message = "カテゴリは50文字以内で入力してください")
        String category,

        @Size(max = 10, message = "タグは10個までです")
        List<@Size(max = 30, message = "タグは30文字以内で入力してください") String> tags
) {
}
