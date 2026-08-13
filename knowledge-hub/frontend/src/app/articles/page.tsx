import Link from "next/link";
import type { Metadata } from "next";
import { getArticles } from "@/lib/api";
import type { Article } from "@/lib/types";

export const metadata: Metadata = {
  title: "記事一覧",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

/** Markdown 記法をおおまかに落として一覧用の抜粋を作る */
function excerpt(body: string): string {
  return body
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/[*_`>#-]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 120);
}

type SearchParams = Promise<{
  q?: string;
  category?: string;
  tag?: string;
}>;

export default async function ArticlesPage(props: { searchParams: SearchParams }) {
  const { q, category, tag } = await props.searchParams;
  const articles = await getArticles({ q, category, tag });

  // フィルタ用の候補は現在の絞り込みを外した全件から作る
  const all = q || category || tag ? await getArticles() : articles;
  const categories = [...new Set(all.map((a) => a.category))].sort();
  const tags = [...new Set(all.flatMap((a) => a.tags))].sort();

  const buildQuery = (patch: Record<string, string | undefined>) => {
    const params = new URLSearchParams();
    const merged = { q, category, tag, ...patch };
    for (const [key, value] of Object.entries(merged)) {
      if (value) params.set(key, value);
    }
    const s = params.toString();
    return s ? `/articles?${s}` : "/articles";
  };

  return (
    <>
      <div className="page-head">
        <div>
          <p className="page-head__eyebrow">ARTICLES ／ 記事一覧</p>
          <h1 className="page-head__title">ナレッジを探す</h1>
        </div>
        <p className="page-head__count">
          <strong>{articles.length}</strong>件
        </p>
      </div>

      <section className="search-panel" aria-label="検索とフィルタ">
        <form action="/articles" method="get" className="search-panel__row">
          <input
            type="search"
            name="q"
            defaultValue={q ?? ""}
            placeholder="キーワードで検索 (タイトル・本文)"
            className="search-panel__input"
            aria-label="キーワード検索"
          />
          {category && <input type="hidden" name="category" value={category} />}
          {tag && <input type="hidden" name="tag" value={tag} />}
          <button type="submit" className="btn">
            検索
          </button>
        </form>

        {categories.length > 0 && (
          <div className="filter-chips">
            <span className="filter-chips__label">CATEGORY</span>
            <Link
              href={buildQuery({ category: undefined })}
              className={`chip ${!category ? "chip--active" : ""}`}
            >
              すべて
            </Link>
            {categories.map((c) => (
              <Link
                key={c}
                href={buildQuery({ category: c === category ? undefined : c })}
                className={`chip ${c === category ? "chip--active" : ""}`}
              >
                {c}
              </Link>
            ))}
          </div>
        )}

        {tags.length > 0 && (
          <div className="filter-chips">
            <span className="filter-chips__label">TAG</span>
            {tags.map((t) => (
              <Link
                key={t}
                href={buildQuery({ tag: t === tag ? undefined : t })}
                className={`chip chip--tag ${t === tag ? "chip--active" : ""}`}
              >
                #{t}
              </Link>
            ))}
          </div>
        )}
      </section>

      {articles.length === 0 ? (
        <div className="empty-state">
          <span className="empty-state__mark">無</span>
          条件に一致する記事がありません。
          <br />
          検索条件を変えるか、新しい記事を作成してください。
        </div>
      ) : (
        <ul className="article-list">
          {articles.map((article: Article) => (
            <li key={article.id} className="fade-in">
              <Link href={`/articles/${article.id}`} className="article-card">
                <div className="article-card__meta">
                  <span className="article-card__category">{article.category}</span>
                  <span className="article-card__date">
                    更新 {formatDate(article.updatedAt)}
                  </span>
                </div>
                <h2 className="article-card__title">{article.title}</h2>
                <p className="article-card__excerpt">{excerpt(article.body)}</p>
                {article.tags.length > 0 && (
                  <div className="article-card__tags">
                    {article.tags.map((t) => (
                      <span key={t} className="tag-pill">
                        #{t}
                      </span>
                    ))}
                  </div>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
