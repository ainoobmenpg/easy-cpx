# UI-10: i18n対象漏れ/固定文面の洗い出し

### 症状
- `frontend/app/game/page.tsx` に固定日本語が多く、i18n未適用。`/scenarios` は一部i18n対応済み。

### 対応
- ゲーム画面の固定文言を `public/locales` に移管、`useI18n()` フックを適用。

### 完了条件
- 主要画面がja/enで切替可能、未翻訳キーなし。
