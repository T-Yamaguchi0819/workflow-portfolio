package com.knowledgehub.api.config;

import com.knowledgehub.api.article.ArticleService;
import com.knowledgehub.api.article.dto.ArticleRequest;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;

import java.util.List;

/**
 * local プロファイル起動時にデモ用の記事を投入する。
 */
@Configuration
@Profile("local")
public class LocalSeedData {

    @Bean
    public CommandLineRunner seedArticles(ArticleService service) {
        return args -> {
            service.create(new ArticleRequest(
                    "VPN に接続できないときの確認手順",
                    """
                    社内 VPN に接続できない場合、以下を順に確認してください。

                    ## 1. クライアントの状態確認
                    - タスクトレイの VPN クライアントが起動しているか
                    - プロファイルが `corp-tokyo` になっているか

                    ## 2. 認証エラーの場合
                    - パスワード有効期限切れの可能性があります。社内ポータルからリセットしてください
                    - ワンタイムコードの時刻ずれ: スマートフォンの時刻を自動設定にする

                    ## 3. それでも解決しない場合
                    情報システム部のヘルプデスク (内線 2100) へ連絡してください。
                    """,
                    "IT-FAQ",
                    List.of("VPN", "ネットワーク", "トラブルシューティング")));

            service.create(new ArticleRequest(
                    "経費精算の締め日と申請ルール",
                    """
                    ## 締め日
                    毎月 **25 日 18:00** までに申請されたものが当月精算の対象です。

                    ## 申請時の注意
                    - 領収書は PDF またはスマートフォン撮影画像を添付
                    - 交際費は事前申請番号を備考欄に記載
                    - 交通費は IC カード履歴の CSV を添付すると承認が早くなります
                    """,
                    "総務",
                    List.of("経費", "申請")));

            service.create(new ArticleRequest(
                    "新入社員向け: 開発環境セットアップガイド",
                    """
                    開発チームに配属されたら、まず以下をセットアップしてください。

                    1. **Git** — 社内 GitLab のアカウント発行を依頼
                    2. **JDK 21** — SDKMAN または公式インストーラで導入
                    3. **Docker Desktop** — ライセンス申請が必要 (上長承認)
                    4. **IDE** — IntelliJ IDEA Community または VS Code

                    セットアップ完了後、`sandbox` リポジトリの README に従って
                    サンプルアプリのビルドが通ることを確認してください。
                    """,
                    "開発",
                    List.of("オンボーディング", "環境構築")));

            service.create(new ArticleRequest(
                    "会議室予約システムの使い方",
                    """
                    ## 予約方法
                    社内ポータル → 「会議室予約」から空き状況を確認して予約します。

                    ## ルール
                    - 予約は 2 週間先まで
                    - 30 分単位。無断キャンセルが月 3 回を超えると翌月の予約が制限されます
                    - 大会議室 (A/B) はプロジェクター利用の有無を選択してください
                    """,
                    "総務",
                    List.of("会議室", "社内システム")));
        };
    }
}
