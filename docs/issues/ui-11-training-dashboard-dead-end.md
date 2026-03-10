# UI-11: `/training` が Next.js 側の未実装 API に向いていて開始できない

### 症状
- Playwright で `http://localhost:3000/training` を開くと画面自体は表示される。
- ただし「Start Training」を押すと `POST /api/training/initialize` が `http://localhost:3000/api/training/initialize` に送られ、404 になる。
- 画面には `Failed to initialize scoreboard` とだけ表示される。

### 原因
- `frontend/app/training/page.tsx` が `fetch("/api/training/...")` の相対パスを使っており、FastAPI (`localhost:8000/api/...`) ではなく Next.js 側に投げている。
- このリポジトリに `frontend/app/api/training/*` の route handler は存在しない。

### 対応
- `training` 画面も `frontend/app/lib/api.ts` 経由で backend API を参照する。
- 404/500 時は `ErrorDisplay` か toast で原因を明示する。
- 必要なら training API の疎通確認用スモークテストを追加する。

### 完了条件
- `/training` から初期化、更新、集計が backend API へ正しく到達する。
- 初回クリックで 404 にならない。
- 失敗時も「どの API が失敗したか」が UI 上で分かる。
