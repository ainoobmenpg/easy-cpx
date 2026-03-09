# Issue #63: AGENTS.md と実装実態の乖離を解消する

- 作成日: 2026-03-09
- ステータス: 未着手
- 優先度: High（ガイド誤記により新規コントリビューターが必ず詰まる）
- オーナー候補: Docs / Contributor Experience

## 背景
2026-03-09 時点の `AGENTS.md`（Repository Guidelines）は、最新の実装や `README.md` と矛盾する記述を含んでいる。結果として、環境構築に失敗したり、存在しないテスト手順を期待させるなど、貢献フローを阻害している。

## 問題点
1. **バックエンド依存のインストール手順が欠落**
   - `README.md` では `pip install fastapi uvicorn sqlalchemy pydantic httpx alembic` を要求しているが、`AGENTS.md` では仮想環境構築のみ記述されており、依存を入れないまま `uvicorn` を実行することになる。
2. **`shared/` の説明が実態と異なる**
   - ドキュメントでは「前後分離を防止」と説明しているが、現状は TypeScript 型定義のみで、`frontend/tsconfig.json` の `@shared/*` 参照経由でフロントエンドから利用している。Python 側には共有コードが存在せず、読者が「バックエンドからも import できる」と誤解する。
3. **フロントエンドテスト手順の記述が空文化**
   - `npm run test` や Vitest/RTL の導入に触れているが、`frontend/package.json` に該当スクリプト・依存は未定義。実行不能な手順を要求している。

## 対応方針
- Backend setup セクションに `pip install -r requirements.txt` or 既存 `pip install fastapi ...` の明示を追記し、実際に必要な依存が揃うことを確認する。
- `shared/` の役割を「TypeScript 型共有（@shared/* エイリアス）」と正確に説明し、Python からの参照は今後の ToDo として切り分ける。
- フロントエンドの自動テストについて、現状 lint + 手動検証であることを明記し、将来的に導入する場合は別 Issue でスコープを定義。あるいは Vitest/RTL を実際に追加して `npm run test` を提供する。

## 完了条件
- `AGENTS.md` が上記 3 点を反映し、手順通りに実行すればエラーなくセットアップできる。
- 更新内容が `README.md`・`frontend/package.json`・`shared/` 構造と整合している。
- 変更後ドキュメントをレビューし、誤情報が取り除かれていることを確認。
