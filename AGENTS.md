# Repository Guidelines

## プロジェクト構成とモジュール整理
- `frontend/` – Next.js 16 + React 19 UI。`app/game` に戦術ビュー、`app/lib` に API ラッパー、`public/` に HUD アセットを配置。
- `backend/` – FastAPI。`app/api` でエンドポイント、`app/models` が SQLAlchemy モデル、`app/services` が adjudication・terrain・weather・MiniMax 連携、マイグレーションは `alembic/`。
- `shared/` – TypeScript 契約 (`types/index.ts`) を `@shared/*` エイリアスで輸出し、前後分離を防止。
- `docs/` と `Plans.md` はシナリオ設計とスプリント前提を示すので、仕様変更前に必読。

## ビルド・テスト・開発コマンド
- `cd frontend && npm install && npm run dev` でローカルサーバー起動、`npm run build && npm run start` で本番バンドルを検証。
- `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn main:app --reload` で API (http://localhost:8000) をホットリロード。
- `cd backend && pytest tests -v` が標準テスト。CI 互換ログには `--maxfail=1 --disable-warnings` を追加。
- スキーマ更新は `cd backend && alembic revision --autogenerate -m "short msg" && alembic upgrade head` をワンセットで実行。

## コーディングスタイルと命名
- TypeScript は strict モード + 2 スペース。コンポーネントは PascalCase、hooks/util は camelCase、Tailwind クラスは機能順。`npm run lint` (ESLint + eslint-config-next) をコミット前に必須化。
- Python は PEP 8、4 スペース、型ヒント付き関数、snake_case モジュール (`app/services/adjudication.py`, `terrain.py`) を維持。`logging.getLogger("cpx")` 経由でロガー統一。
- API 契約変更時は `shared/types`、Pydantic schema、React コンポーネントを同一 PR で同期。

## テストガイドライン
- バックエンドテストは `backend/tests` で `test_*.py` パターン。触れたモジュールは 80% 以上のカバー率を確保し、必要なら `pytest --cov=app --cov-report=html` で `htmlcov/` を更新。
- フロントエンドは `npm run lint` + 手動シナリオが現状。ロジック追加時は Vitest/React Testing Library を `frontend/__tests__/` に配置し、将来の `npm run test` スクリプトに組み込み。

## コミットと Pull Request 方針
- コミットは `<type>: <summary>` 形式 (例: `feat: Complete Arcade CPX mode`, `fix: Address ChatGPT review`) を踏襲し、命令形で統一。
- `Plans.md` のマイルストン番号や Issue ID を本文に記載し、マイグレーションやスキーマ変更の影響を明示。
- PR では挙動差分、実行した `npm run lint` / `pytest` / `alembic` などのログ、必要な環境変数、UI 変更のスクリーンショット (`game-*.png`) を添付。

## セキュリティと設定 Tips
- MiniMax トークンや DATABASE_URL は未追跡 `.env` に保存し、`operational_cpx.db` 以外の SQLite をコミットしない。
- 共有環境では Alembic 実行前に `export DATABASE_URL=...` を設定し、`alembic downgrade -1` で巻き戻し確認を行う。
