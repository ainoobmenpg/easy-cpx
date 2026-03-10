# API-1: /api/games/start が /api/games/{game_id} と競合して 405/422 になる

### 症状（再現）
- `POST http://localhost:8000/api/games/start` → 405 Method Not Allowed
- `GET  http://localhost:8000/api/games/start` → 422（`game_id` に `start` が解釈される）
- ルータで `@router.get('/games/{game_id}')` が `@router.post('/games/start')` より優先され、静的パスが動的パスに食われている。

### 影響
- フロントのシナリオ起動（/scenarios → ミッション開始）が失敗し、/game へ遷移しない。
- E2E（Playwright）でも遷移待ちでタイムアウト。

### 対応案
- 静的パスを動的パスより前に宣言する（FastAPIは宣言順で一致評価）。
- あるいはエンドポイント名を `POST /api/start-game` 等に変更。

### 完了条件
- `POST /api/games/start` が200でゲームIDを返し、/game?gameId=… へ遷移可能になる。
- E2Eがパス。
