package com.knowledgehub.api.article;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.greaterThan;
import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * local プロファイル (インメモリ + シードデータ) で API を通しで検証する。
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("local")
class ArticleControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void 一覧が取得できる() throws Exception {
        mockMvc.perform(get("/api/articles"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThan(0))));
    }

    @Test
    void 作成_取得_削除が一連で成功する() throws Exception {
        String body = """
                {
                  "title": "テスト記事",
                  "body": "本文です",
                  "category": "テスト",
                  "tags": ["e2e"]
                }
                """;

        String location = mockMvc.perform(post("/api/articles")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.title").value("テスト記事"))
                .andReturn().getResponse().getContentAsString();

        String id = com.jayway.jsonpath.JsonPath.read(location, "$.id");

        mockMvc.perform(get("/api/articles/" + id))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.category").value("テスト"));

        mockMvc.perform(delete("/api/articles/" + id))
                .andExpect(status().isNoContent());

        mockMvc.perform(get("/api/articles/" + id))
                .andExpect(status().isNotFound());
    }

    @Test
    void バリデーションエラーは400とエラー詳細を返す() throws Exception {
        mockMvc.perform(post("/api/articles")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"title\":\"\",\"body\":\"\",\"category\":\"\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.errors", hasSize(greaterThan(0))));
    }

    @Test
    void 存在しないIDは404を返す() throws Exception {
        mockMvc.perform(get("/api/articles/no-such-id"))
                .andExpect(status().isNotFound());
    }
}
