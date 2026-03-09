# CPX-6: 多役割RBAC（BLUE/RED/WHITE/Observer）＋リアルタイム通知

### 背景
無認証APIが是正されても、CPXでは役割ごとに可視情報・操作権限が異なる。現状は単一視点。

### 提案
- 認証/RBAC: `User`/`Session`/`Role` モデル（BLUE/RED/WHITE/Observer）。ゲーム参加と権限でAPIレスポンスをフィルタ。
- 通信: WebSocket/SSEでSITREP/Inject/スコア更新をプッシュ。役割別チャンネルを用意。

### 受け入れ基準
- ロールに応じて敵情報/内部状態の露出が制御される。
- ターン確定/Inject等がリアルタイムでクライアントに配信される。
