# Docs-5: デプロイ/セキュリティガイド（ENV/CORS/内部API）

### 背景
本番運用に必要な項目（CORS、内部API無効化、シークレット、レート制限等）のガイドが分散/不足。

### 対応
- `docs/deploy.md` を作成し、`CORS_ORIGINS` `ENABLE_INTERNAL_ENDPOINTS` `JWT_*` `DATABASE_URL` `NEXT_PUBLIC_API_URL` 等を整理。
- レート制限/監査ログの推奨設定とプロキシ例（nginx等）を記載。

### 完了条件
- このドキュメントだけで安全に本番立上げが可能。
