# CS基礎 学習ノート

第1〜15回の解説・フロントエンド実務例・確認問題30問を収録。
スマホ対応の目次、各回の独立ページ、前後ナビゲーション、開閉式の解答を同じ講義データから生成します。

## 教材を読む・更新する

```sh
python3 build.py
```

`dist/index.html` が目次、`dist/lessons/001.html` 以降が講義ページ、`dist/cs-basics.html` がオフライン保存用の全回版です。Python 3.12以上を推奨。追加パッケージは不要です。

教材の正本は `lessons.json`。配列の順序が回番号のため、並び替え・途中挿入はしません。過去回の訂正はPRで行います。第1〜4回は元会話で確認できたテーマをもとに補足した教材であり、原文の完全な復元ではありません。第5〜11回にも総復習からの補足があります。編集方針・確認資料は教材内に明記しています。

## 自動追記

既存の毎朝5時（Asia/Tokyo）の「基本情報 5分学習」は維持します。このリポジトリに講義生成用のcronやAI APIの呼び出しはありません。

同期処理は既存配信チャット `6ac24f47-a554-83ee-a03b-dd8214e63bda` に届いた新しい講義を読み、次のJSON形式で渡します。GitHub Actionsが入力を検証し、`lessons.json` への追記・教材全体の再生成・Pages公開を行います。ChatGPTへのログイン情報やAPIキーをリポジトリへ保存する必要はありません。

```json
{
  "number": 16,
  "lesson": {
    "title": "配信されたテーマ",
    "group": "分野",
    "goal": "この回の学習目標",
    "body": "<p>配信された仕組みの解説</p>",
    "practice": "<p>実務との接続</p>",
    "questions": [["理解確認の質問", "解答と解説"]]
  }
}
```

これは形式の説明であり、第16回の教材ではありません。実際に配信された内容を使います。HTMLの使用可能なタグ・属性は `ingest.py` で制限しています。コード中の `<` は `&lt;` と記述します。

送信方式は以下のどちらかです。

- `POST /repos/ryoohshima/cs-basic/dispatches` に `event_type: cs-lesson`、`client_payload: 上記JSON` を送信。
- Actionsの **Receive lesson and publish → Run workflow** に同じJSONを指定。空欄では既存教材を再公開。

認証済みGitHub CLIが使える同期環境では、講義JSONをファイルへ保存して次のコマンドで送れます（JSONをシェル式に埋め込みません）。

```sh
gh workflow run publish.yml --repo ryoohshima/cs-basic --ref main -F lesson_json=@lesson.json
```

送信後はActionsの成功を確認します。同じ回・同じ内容の再送は変更なし。登録済みの回と異なる内容、欠番、不正なHTML、必須項目の欠落は失敗として停止し、過去の教材を書き換えません。複数回を取り込む場合は1回ずつ実行成功を待ってください。待機キューは最大100件ですが実行開始順は保証されないため、まとめて同時送信せず、失敗・キャンセル時は同じJSONを再送します。

データ保存後に公開だけ失敗した場合も、同じJSONの再送、または入力なしの手動実行で再公開できます。ブランチ保護でbotのmain更新が拒否された場合は、権限を自動で緩和せず、講義データのPRを作成します。そのPRがmainへ反映されると公開が動きます。

## 接続と公開の初期設定

1. 実装PRを確認してmainへ反映する。
2. Settings → Pages → Build and deployment の Source を **GitHub Actions** にする。
3. **Receive lesson and publish** を入力なしで実行し、初回公開の成功を確認する。
4. Codexの同期予約を有効にする。毎朝5時15分（Asia/Tokyo）、元の配信チャットを読む。新規の講義がなければ静かに終了し、本文を確認できなければ推測で教材を作らない。

同期予約は配信処理とは別の追記専用処理です。既存5時配信の時刻・指示・通知設定は変更しません。実装PRが未マージの間は同期によるリポジトリ変更を行いません。予約の実行環境には元チャットの読み取りと、このリポジトリのActions実行（または講義データPR作成）が可能なGitHub接続が必要です。ローカル実行ではアプリや端末の稼働状況による遅延があり得ます。

公開予定URL: https://ryoohshima.github.io/cs-basic/ （初回公開完了後に利用可能）

## 検証

```sh
python3 -m unittest discover -s tests -v
python3 build.py
```

リンクの参照先、各回の前後ナビゲーション、確認問題数、追記・再送・競合・欠番、不正入力を検証します。PRと作業ブランチへのpushでも検証し、生成済み教材をActionsのプレビュー成果物へ保存します。

## 参照

- [GitHub Actionsの外部イベントと手動実行](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [GitHub PagesをActionsで公開](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [ChatGPTの定期実行](https://learn.chatgpt.com/docs/automations)
