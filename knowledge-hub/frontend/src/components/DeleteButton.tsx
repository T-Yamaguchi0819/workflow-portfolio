"use client";

/**
 * 削除の確認ダイアログ付き送信ボタン。
 * confirm を挟むためだけの小さなクライアントコンポーネント。
 */
export function DeleteButton({ action }: { action: () => Promise<void> }) {
  return (
    <form
      action={action}
      onSubmit={(e) => {
        if (!window.confirm("この記事を削除します。よろしいですか?")) {
          e.preventDefault();
        }
      }}
    >
      <button type="submit" className="btn btn--danger">
        削除する
      </button>
    </form>
  );
}
