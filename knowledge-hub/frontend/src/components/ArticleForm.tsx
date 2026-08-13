"use client";

import { useActionState } from "react";
import Link from "next/link";
import type { FormState } from "@/lib/actions";
import type { Article } from "@/lib/types";

type Props = {
  action: (prev: FormState, formData: FormData) => Promise<FormState>;
  article?: Article;
  submitLabel: string;
};

const initialState: FormState = { message: "", errors: [] };

/**
 * 記事の作成・編集フォーム。Server Action + useActionState で
 * ページ遷移なしにバリデーションエラーを表示する。
 */
export function ArticleForm({ action, article, submitLabel }: Props) {
  const [state, formAction, pending] = useActionState(action, initialState);

  return (
    <form action={formAction} className="form-card">
      {state.message && (
        <div className="form-error" role="alert">
          {state.message}
          {state.errors.length > 0 && (
            <ul>
              {state.errors.map((e) => (
                <li key={e}>{e}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="form-field">
        <label className="form-field__label" htmlFor="title">
          タイトル <span className="form-field__required">必須</span>
        </label>
        <input
          id="title"
          name="title"
          type="text"
          className="form-field__input"
          defaultValue={article?.title ?? ""}
          maxLength={200}
          required
        />
      </div>

      <div className="form-field">
        <label className="form-field__label" htmlFor="category">
          カテゴリ <span className="form-field__required">必須</span>
          <span className="form-field__hint">例: IT-FAQ / 総務 / 開発</span>
        </label>
        <input
          id="category"
          name="category"
          type="text"
          className="form-field__input"
          defaultValue={article?.category ?? ""}
          maxLength={50}
          required
        />
      </div>

      <div className="form-field">
        <label className="form-field__label" htmlFor="tags">
          タグ
          <span className="form-field__hint">カンマ区切りで最大10個 (例: VPN, ネットワーク)</span>
        </label>
        <input
          id="tags"
          name="tags"
          type="text"
          className="form-field__input"
          defaultValue={article?.tags.join(", ") ?? ""}
        />
      </div>

      <div className="form-field">
        <label className="form-field__label" htmlFor="body">
          本文 <span className="form-field__required">必須</span>
          <span className="form-field__hint">Markdown が使えます</span>
        </label>
        <textarea
          id="body"
          name="body"
          className="form-field__textarea"
          defaultValue={article?.body ?? ""}
          required
        />
      </div>

      <div className="form-actions">
        <button type="submit" className="btn btn--primary" disabled={pending}>
          {pending ? "保存中…" : submitLabel}
        </button>
        <Link
          href={article ? `/articles/${article.id}` : "/articles"}
          className="btn btn--ghost"
        >
          キャンセル
        </Link>
      </div>
    </form>
  );
}
