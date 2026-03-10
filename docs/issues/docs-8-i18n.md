# Docs-8: 文言/言語統一（UI/i18n方針）

### 問題
UI/Docsで英日が混在。Quick-Ref表の英見出し等。ユーザ層に応じて統一かi18n対応が必要。

### 対応
- UIを日本語に統一 or Next.js i18nを導入し `ja/en` を切替。
- 文言資産を `frontend/public/locales/*` に集約。

### 完了条件
- 主要画面の文言が方針に沿って統一 or 言語切替可能。
