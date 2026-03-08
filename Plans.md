# Plans.md

このファイルには、実装タスクを記録します。

---

## 🔴 進行中のタスク

(なし)

---

## 🟡 未着手のタスク

### 優先度1：今すぐ実装（レビュー指摘対応）

- [x] next.config.tsのTypeScriptエラーを修正 `cc:完了` (2026-03-08)
  - `turbopack: false` を削除
  - ファイル: `frontend/next.config.ts`

- [x] エラー発生時のユーザー通知を追加 `cc:完了` (2026-03-08)
  - fetch失敗時にエラーメッセージ表示 + Retryボタン追加
  - ファイル: `frontend/app/game/page.tsx`

- [x] アクセシビリティ属性の追加 `cc:完了` (2026-03-08)
  - ボタンにaria-label追加（7箇所）
  - ファイル: `frontend/app/game/page.tsx`

- [x] 地図への地形表示 `cc:完了` (2026-03-08)
  - グリッドベースの地形データ生成（森林、山岳、市街地、水域）
  - SVGマップに地形レンダリング
  - 地形記号表示: ■(市街地)、▓(森林)、▲(高地)、△(山岳)、≈(水域)、◇(湿地)
  - ファイル: `frontend/app/game/page.tsx` + `backend/app/services/terrain.py`

- [x] 地図への気象情報表示 `cc:完了` (2026-03-08)
  - ヘッダーに日付表示 (1985-11-22)
  - 時間帯アイコン (☀️/🌙)
  - 偵察倍率表示
  - 夜間背景色変化
  - ファイル: `frontend/app/game/page.tsx` + `backend/app/services/weather_effects.py`

### 優先度2：ドキュメント整備

- [x] README.md 更新 `cc:完了` (2026-03-08)
  - プロジェクト概要
  - セットアップ手順
  - 技術スタック
  - ファイル構成

- [x] docs/game-rules.md 作成 `cc:完了` (2026-03-08)
  - ゲームルール詳細
  - ターン進行
  - 判定基準
  - 資源管理

- [x] docs/architecture.md 作成 `cc:完了` (2026-03-08)
  - システムアーキテクチャ
  - コンポーネント構成
  - データフロー

### 優先度3：UI改善

- [x] 日付表示追加 `cc:完了` (2026-03-08)
  - ヘッダーに日付表示（YYYY-MM-DD）
  - ファイル: `frontend/app/game/page.tsx`

- [x] ユニット詳細パネルの充実 `cc:完了` (2026-03-08)
  - 戦力、弾薬・燃料・整備状況の表示
  - 位置座標の表示

---

## 🟢 完了タスク

- [x] 優先度4実装 `cc:完了` (2026-03-08)
  - 命令レベルシステム: OrderLevel enum追加
  - 摩擦イベント: app/services/friction_events.py
  - 偵察・情報精度: app/services/intelligence.py
  - エスカレーション: app/services/escalation.py

- [x] 優先度5実装 `cc:完了` (2026-03-08)
  - 装備データベース: app/data/weapons.py（冷戦期装備）
  - 初期配置: app/services/initial_setup.py
  - 日付・時刻管理: Gameモデル更新

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

- [x] テキストマップ生成 `cc:完了` (2026-03-08)
  - app/services/map_renderer.py 実装完了

- [x] 敵の能動的AI `cc:完了` (2026-03-08)
  - app/services/excon_ai.py 実装完了

- [x] 消耗資源管理 `cc:完了` (2026-03-08)
  - app/services/resource_manager.py 実装完了

- [x] 上官命令システム `cc:完了` (2026-03-08)
  - app/services/commander_order_service.py 実装完了

- [x] 詳細なSITREPフォーマット `cc:完了` (2026-03-08)
  - app/services/sitrep_generator.py 実装完了

- [x] 判定基準の構造化 `cc:完了` (2026-03-08)
  - app/services/adjudication.py 更新完了

- [x] 報告義務システム `cc:完了` (2026-03-08)
  - app/services/reporting.py 実装完了

- [x] 夜間・天候効果 `cc:完了` (2026-03-08)
  - app/services/weather_effects.py 実装完了

- [x] 地形効果 `cc:完了` (2026-03-08)
  - app/services/terrain.py 実装完了

- [x] 膠着状態ルール `cc:完了` (2026-03-08)
  - app/services/stalemate.py 実装完了

---

## 📦 アーカイブ
