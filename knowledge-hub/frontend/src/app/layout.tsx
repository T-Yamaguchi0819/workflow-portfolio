import type { Metadata } from "next";
import { IBM_Plex_Mono, Shippori_Mincho, Zen_Kaku_Gothic_New } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const shippori = Shippori_Mincho({
  weight: ["500", "700"],
  subsets: ["latin"],
  variable: "--font-shippori",
});

const zenKaku = Zen_Kaku_Gothic_New({
  weight: ["400", "500", "700"],
  subsets: ["latin"],
  variable: "--font-zen",
});

const plexMono = IBM_Plex_Mono({
  weight: ["400", "500"],
  subsets: ["latin"],
  variable: "--font-plex-mono",
});

export const metadata: Metadata = {
  title: {
    default: "Knowledge Hub — 社内ナレッジベース",
    template: "%s | Knowledge Hub",
  },
  description:
    "社内のナレッジ・FAQ を蓄積、検索、共有するためのナレッジベース (ポートフォリオ作品)",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ja">
      <body className={`${shippori.variable} ${zenKaku.variable} ${plexMono.variable}`}>
        <header className="site-header">
          <div className="site-header__inner">
            <Link href="/articles" aria-label="Knowledge Hub トップへ">
              <span className="site-header__seal">知</span>
            </Link>
            <div className="site-header__titles">
              <Link href="/articles" className="site-header__name">
                Knowledge Hub
              </Link>
              <span className="site-header__sub">Internal Knowledge Base</span>
            </div>
            <nav className="site-header__nav">
              <Link href="/articles" className="site-header__link">
                記事一覧
              </Link>
              <Link href="/articles/new" className="btn btn--primary">
                ＋ 記事を書く
              </Link>
            </nav>
          </div>
        </header>
        <main className="shell">{children}</main>
        <footer className="site-footer">
          KNOWLEDGE HUB — PORTFOLIO PROJECT / NEXT.JS × SPRING BOOT × DYNAMODB
        </footer>
      </body>
    </html>
  );
}
