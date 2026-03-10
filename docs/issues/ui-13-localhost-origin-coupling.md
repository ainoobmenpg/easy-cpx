# UI-13: フロントを `127.0.0.1` で開くと API が `localhost` 固定で CORS 失敗する

### 症状
- Playwright で `http://127.0.0.1:3000` を開くと、`/scenarios` の API 取得が失敗する。
- Console には `Access to fetch at 'http://localhost:8000/api/scenarios' ... blocked by CORS policy` が出る。
- 同じアプリを `http://localhost:3000` で開くと再現しない。

### 原因
- `frontend/.env.local` の `NEXT_PUBLIC_API_URL` が `http://localhost:8000` 固定。
- `backend/main.py` の CORS 既定値も `http://localhost:3000` のみ。
- フロントの閲覧元ホストと API ホストが少しでもズレると、ローカル確認でも即失敗する。

### 対応
- 開発時は `localhost` と `127.0.0.1` の両方を CORS 許可に含める。
- 可能なら frontend は相対 URL または現在ホストから API URL を組み立てる。
- README に「どの origin で起動する前提か」を明記する。

### 完了条件
- `localhost:3000` と `127.0.0.1:3000` の両方から主要 API が成功する。
- `/scenarios` `/games` で CORS エラーが出ない。
