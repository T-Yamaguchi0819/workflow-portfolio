import Link from "next/link";
import { notFound } from "next/navigation";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ApiRequestError, getArticle } from "@/lib/api";
import { deleteArticleAction } from "@/lib/actions";
import { DeleteButton } from "@/components/DeleteButton";

type Params = Promise<{ id: string }>;

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

async function fetchArticleOr404(id: string) {
  try {
    return await getArticle(id);
  } catch (e) {
    if (e instanceof ApiRequestError && e.status === 404) {
      notFound();
    }
    throw e;
  }
}

export async function generateMetadata(props: { params: Params }) {
  const { id } = await props.params;
  const article = await fetchArticleOr404(id);
  return { title: article.title };
}

export default async function ArticleDetailPage(props: { params: Params }) {
  const { id } = await props.params;
  const article = await fetchArticleOr404(id);
  const deleteAction = deleteArticleAction.bind(null, article.id);

  return (
    <>
      <Link href="/articles" className="back-link">
        ← 記事一覧に戻る
      </Link>

      <article className="article-detail fade-in">
        <div className="article-detail__meta">
          <span className="article-card__category">{article.category}</span>
          {article.tags.map((t) => (
            <Link key={t} href={`/articles?tag=${encodeURIComponent(t)}`} className="tag-pill">
              #{t}
            </Link>
          ))}
        </div>

        <h1 className="article-detail__title">{article.title}</h1>

        <div className="prose">
          <Markdown remarkPlugins={[remarkGfm]}>{article.body}</Markdown>
        </div>

        <div className="article-detail__dates">
          <span>作成: {formatDateTime(article.createdAt)}</span>
          <span>最終更新: {formatDateTime(article.updatedAt)}</span>
          <span>ID: {article.id}</span>
        </div>

        <div className="article-detail__actions">
          <Link href={`/articles/${article.id}/edit`} className="btn">
            編集する
          </Link>
          <DeleteButton action={deleteAction} />
        </div>
      </article>
    </>
  );
}
