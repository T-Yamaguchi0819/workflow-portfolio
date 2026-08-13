import type { Article, ArticleInput } from "./types";

const BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8080";

/** API のバリデーションエラー等を UI に伝えるための例外 */
export class ApiRequestError extends Error {
  readonly errors: string[];
  readonly status: number;

  constructor(message: string, status: number, errors: string[] = []) {
    super(message);
    this.status = status;
    this.errors = errors;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    // ナレッジは更新頻度が高いので SSR ごとに最新を取得する
    cache: "no-store",
  });

  if (!res.ok) {
    let message = `APIエラー (${res.status})`;
    let errors: string[] = [];
    try {
      const body = await res.json();
      message = body.message ?? message;
      errors = body.errors ?? [];
    } catch {
      // JSON でないエラーレスポンスはステータスのみ伝える
    }
    throw new ApiRequestError(message, res.status, errors);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export type ArticleQuery = {
  category?: string;
  tag?: string;
  q?: string;
};

export function getArticles(query: ArticleQuery = {}): Promise<Article[]> {
  const params = new URLSearchParams();
  if (query.category) params.set("category", query.category);
  if (query.tag) params.set("tag", query.tag);
  if (query.q) params.set("q", query.q);
  const qs = params.toString();
  return request<Article[]>(`/api/articles${qs ? `?${qs}` : ""}`);
}

export function getArticle(id: string): Promise<Article> {
  return request<Article>(`/api/articles/${encodeURIComponent(id)}`);
}

export function createArticle(input: ArticleInput): Promise<Article> {
  return request<Article>("/api/articles", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateArticle(id: string, input: ArticleInput): Promise<Article> {
  return request<Article>(`/api/articles/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export function deleteArticle(id: string): Promise<void> {
  return request<void>(`/api/articles/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}
