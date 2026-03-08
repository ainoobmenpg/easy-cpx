# Plans.md

このファイルには、実装タスクを記録します。

---

## 🔴 進行中のタスク

(なし)

---

## 🟡 未着手のタスク

(なし)

---

## 🟢 完了タスク

- [x] テスト実装 `cc:完了` (2026-03-08)
  - Backend: pytest + conftest.py セットアップ
  - ルールエンジン単テスト (test_adjudication.py): 15テスト
  - API エンドポイントテスト (test_api.py): 18テスト
  - データベーステスト (test_database.py): 3テスト
  - カバレッジ結果: **86%** (目標80%達成)
  - 総テスト数: 36件全てパス

- [x] 基盤セットアップ `cc:完了` (2026-03-08)
  - Frontend: Next.js 14 + React + TypeScript プロジェクト作成
  - Backend: Python FastAPI プロジェクト作成
  - ディレクトリ構造設計（frontend/, backend/, shared/）
  - ESLint + TypeScript 設定
  - 各プロジェクトの依存関係セットアップ

- [x] 共有スキーマ定義 `cc:完了` (2026-03-08)
  - shared/schemas/order-parser.schema.json
  - shared/schemas/adjudication-result.schema.json
  - shared/schemas/sitrep.schema.json
  - shared/types/ 型定義

- [x] データベース設計 `cc:完了` (2026-03-08)
  - ER図設計（ユニット、ターン履歴、状態等）
  - PostgreSQL スキーマ作成
  - Alembic マイグレーション設定
  - API エンドポイント作成

- [x] コア機能実装 `cc:完了` (2026-03-08)
  - ルールエンジン基盤 (app/services/adjudication.py)
  - AI統合（MiniMax M2.5）(app/services/ai_client.py)
  - 状態管理設計 (RuleEngine)

- [x] UI実装 `cc:完了` (2026-03-08)
  - 地図表示コンポーネント (SVG マップ)
  - SITREP 表示
  - 命令入力UI

---

## 📦 アーカイブ
