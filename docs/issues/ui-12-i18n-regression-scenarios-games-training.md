# UI-12: `/scenarios` `/games` `/training` に未翻訳キーと固定文言が残っている

### 症状
- Playwright で locale を `EN` に切り替えると、英語 UI の中に日本語と raw key が混在する。
- `http://localhost:3000/games` ではエラーカードのタイトルが `games.errorTitle` のまま出る。
- `http://localhost:3000/games` は `新規ゲーム`, `ゲームがありません`, `新しいゲームを開始` が英語化されない。
- `http://localhost:3000/scenarios` はモーダル内の `マップ情報`, `サイズ:`, `開始中...`, `ミッション開始`, `キャンセル` が固定日本語。
- `http://localhost:3000/training` は locale が日本語でも見出しや説明の大半が英語のまま。

### 原因
- `frontend/public/locales/*/translation.json` に `games.errorTitle` など必要キーがない。
- 各ページに `t()` を通していない固定文言が残っている。

### 対応
- `games`, `scenarios`, `training` の固定文言を locale ファイルへ移す。
- raw key 表示を防ぐため、主要画面で未翻訳キー検知を入れる。
- 既存の `UI-10` を拡張するか、本件をその具体タスクとして扱う。

### 完了条件
- ja/en 切替時に raw key が表示されない。
- `/scenarios` `/games` `/training` の主要ラベルが locale に追従する。
- Playwright の smoke で言語混在が再発しない。
