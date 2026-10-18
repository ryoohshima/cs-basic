# CS学習ノート

[学習ノートを開く](https://ryoohshima.github.io/cs-basic/)

CS基礎の講義を、原文の説明・コード・図解・確認問題を保ってまとめた学習ノートです。構造や処理の流れはMermaidで図示し、元のテキストも確認できます。

## 更新

講義データは `lessons.json` で管理します。新しい講義は末尾に追加し、補足は原文と分けて記載します。

配信済みの講義を同期し、GitHub Actionsでページを生成・公開します。

## ローカル確認

Python 3で実行します。生成した `dist/index.html` をブラウザで開いてください。

```sh
python3 -m unittest discover -s tests -v
python3 build.py
```
