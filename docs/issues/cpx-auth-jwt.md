# CPX-AUTH: 認証基盤（ログイン/JWT）＋パスワードハッシュ導入

### 背景
RBACモデル/サービスは存在するが、実APIにユーザ認証が未適用。`users`/`game_players`はあるが、ログイン/トークン発行/認可ミドルウェアがないため、実運用や多役割CPXに不可欠な前提が欠落。

### 目的
- ログイン（ユーザ名/パスワード）→ JWT発行（短命Access/長命Refresh）
- パスワードはPBKDF2/Argon2等でハッシュ化
- FastAPI依存関数 `get_current_user()` を実装し、APIガードに利用

### 提案
- `/auth/login` `/auth/refresh` `/auth/logout` `/auth/me` 追加
- 設定: `JWT_SECRET`, `JWT_EXP_MIN`, `JWT_REFRESH_EXP_MIN`
- 失敗時は 401/403 と監査ログ出力（structured_logging）

### 受け入れ基準
- 正しいクレデンシャルでトークン取得→保護APIにアクセス可能
- 誤ったトークン/期限切れは 401
- ユニットテスト（成功/失敗/期限切れ/ロール別）を追加
