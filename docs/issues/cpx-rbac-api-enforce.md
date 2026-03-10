# CPX-RBAC: APIへのロール適用（BLUE/RED/WHITE/Observer）

### 背景
RBACサービスはあるが、実際のエンドポイントでの権限制御が限定的。WHITE以外へ内部情報露出禁止、BLUE/REDは自軍操作のみを保証する必要がある。

### 対象API（例）
- `/api/orders/`, `/api/turn/commit`: BLUE/REDのみ・自軍ユニット限定
- `/api/games/{id}/state`: BLUE/REDはFoW適用、WHITE/ADMINはフル
- `/api/internal/*`: WHITE/ADMINのみ（ENVフラグに加えロールチェック）

### 受け入れ基準
- ロールに応じてレスポンス差が発生（テストで検証）
- 自軍外ユニットへの命令は 403
- 監査ログにユーザID/ゲームID/許可or拒否が残る
