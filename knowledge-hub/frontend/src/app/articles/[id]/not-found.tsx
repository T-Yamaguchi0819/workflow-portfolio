import Link from "next/link";

export default function ArticleNotFound() {
  return (
    <div className="empty-state" style={{ marginTop: "72px" }}>
      <span className="empty-state__mark">迷</span>
      お探しの記事は見つかりませんでした。削除されたか、URL が誤っている可能性があります。
      <p style={{ marginTop: "24px" }}>
        <Link href="/articles" className="btn">
          記事一覧へ戻る
        </Link>
      </p>
    </div>
  );
}
