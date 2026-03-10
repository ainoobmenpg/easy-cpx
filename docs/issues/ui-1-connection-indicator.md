# UI-1: バックエンド接続インジケータ＋APIベースURL診断

### 症状
- 実機で `/game` を開くと `GET /api/games/` が 405 になるケースがあり、UIが静かに失敗（JS実行時に無反応）。
- `NEXT_PUBLIC_API_URL` と実稼働URLの不一致を検出できない。

### 対応
- ヘッダー右側に接続バッジ（healthy/timeout/mismatch）。`/health` 叩いて状態表示。クリックで診断モーダル（現在の `API.baseUrl` と推奨設定、CORS注意）
- 初回ロードで `games` 取得失敗時は `/games` へガイド付き遷移（"新規開始はこちら"）。

### 実装ポイント
- `frontend/app/lib/api.ts` に `pingHealth()` を追加。
- `frontend/app/game/page.tsx` の初期 `useEffect` 成否で案内UIを出す。

### 完了条件
- API不調時もUIが沈黙せず、ユーザが自己解決できる導線が出る。
