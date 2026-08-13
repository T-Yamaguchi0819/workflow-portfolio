import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { ApiRequestError, getArticle } from "@/lib/api";
import { updateArticleAction } from "@/lib/actions";
import { ArticleForm } from "@/components/ArticleForm";

export const metadata: Metadata = {
  title: "記事の編集",
};

type Params = Promise<{ id: string }>;

export default async function EditArticlePage(props: { params: Params }) {
  const { id } = await props.params;

  let article;
  try {
    article = await getArticle(id);
  } catch (e) {
    if (e instanceof ApiRequestError && e.status === 404) {
      notFound();
    }
    throw e;
  }

  const action = updateArticleAction.bind(null, article.id);

  return (
    <>
      <Link href={`/articles/${article.id}`} className="back-link">
        ← 記事に戻る
      </Link>
      <div className="page-head">
        <div>
          <p className="page-head__eyebrow">EDIT ／ 編集</p>
          <h1 className="page-head__title">記事を編集する</h1>
        </div>
      </div>
      <ArticleForm action={action} article={article} submitLabel="更新する" />
    </>
  );
}
