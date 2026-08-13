import Link from "next/link";
import type { Metadata } from "next";
import { createArticleAction } from "@/lib/actions";
import { ArticleForm } from "@/components/ArticleForm";

export const metadata: Metadata = {
  title: "新規作成",
};

export default function NewArticlePage() {
  return (
    <>
      <Link href="/articles" className="back-link">
        ← 記事一覧に戻る
      </Link>
      <div className="page-head">
        <div>
          <p className="page-head__eyebrow">NEW ／ 新規作成</p>
          <h1 className="page-head__title">記事を書く</h1>
        </div>
      </div>
      <ArticleForm action={createArticleAction} submitLabel="作成する" />
    </>
  );
}
