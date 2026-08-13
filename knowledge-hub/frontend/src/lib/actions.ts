"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { ApiRequestError, createArticle, deleteArticle, updateArticle } from "./api";
import type { ArticleInput } from "./types";

export type FormState = {
  message: string;
  errors: string[];
};

function toInput(formData: FormData): ArticleInput {
  const tags = String(formData.get("tags") ?? "")
    .split(/[,、]/)
    .map((t) => t.trim())
    .filter((t) => t.length > 0);

  return {
    title: String(formData.get("title") ?? ""),
    body: String(formData.get("body") ?? ""),
    category: String(formData.get("category") ?? ""),
    tags,
  };
}

function toFormState(e: unknown): FormState {
  if (e instanceof ApiRequestError) {
    return { message: e.message, errors: e.errors };
  }
  return {
    message: "APIに接続できませんでした。バックエンドの起動状態を確認してください。",
    errors: [],
  };
}

export async function createArticleAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  let id: string;
  try {
    const article = await createArticle(toInput(formData));
    id = article.id;
  } catch (e) {
    return toFormState(e);
  }
  revalidatePath("/articles");
  redirect(`/articles/${id}`);
}

export async function updateArticleAction(
  id: string,
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  try {
    await updateArticle(id, toInput(formData));
  } catch (e) {
    return toFormState(e);
  }
  revalidatePath("/articles");
  revalidatePath(`/articles/${id}`);
  redirect(`/articles/${id}`);
}

export async function deleteArticleAction(id: string): Promise<void> {
  await deleteArticle(id);
  revalidatePath("/articles");
  redirect("/articles");
}
