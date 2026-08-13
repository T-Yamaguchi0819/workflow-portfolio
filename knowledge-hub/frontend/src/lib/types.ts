export type Article = {
  id: string;
  title: string;
  body: string;
  category: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
};

export type ArticleInput = {
  title: string;
  body: string;
  category: string;
  tags: string[];
};

/** バックエンドの統一エラーレスポンス */
export type ApiError = {
  message: string;
  errors: string[];
};
