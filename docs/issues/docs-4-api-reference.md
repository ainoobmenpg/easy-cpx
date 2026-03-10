# Docs-4: APIリファレンス新規作成（認証/RBAC含む）

### 背景
エンドポイントが増加（Inject/OPORD/turn/commit等）。統合APIリファレンスがない。

### 対応
- `docs/api.md` を新設し、各エンドポイントのメソッド/パラメータ/例/ロール要件/HTTPコードを記述。
- 内部用APIは明示的に「本番では無効」注釈。ENV `ENABLE_INTERNAL_ENDPOINTS` を記載。

### 完了条件
- 主要APIが網羅され、例がコピペで動く。
