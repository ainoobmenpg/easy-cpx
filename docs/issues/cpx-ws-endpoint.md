# CPX-WS: WebSocketエンドポイント実装と通知配信

### 背景
通知サービスはあるが、FastAPIの`@app.websocket`による実エンドポイントが未実装。ターン確定/SITREP/Inject更新をリアルタイム配信したい。

### 提案
- `/ws/games/{game_id}` を追加し、接続時にRBAC確認
- `notify_turn_advance`, `notify_sitrep_available` 連動
- フロント: `game`ページで接続し、UIイベント反映

### 受け入れ基準
- 複数クライアント接続で同報可
- ターン確定後に全接続へ通知が届く（統合テスト）
