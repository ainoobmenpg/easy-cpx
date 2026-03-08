# Plans.md

このファイルには、実装タスクを記録します。

---

## 🔴 進行中のタスク

(なし)

---

## 🟡 未着手のタスク

### 優先度1：今すぐ実装

- [ ] テキストマップ生成システム `cc:TODO`
  - グリッドベースのテキストマップ生成（記号: █▲▓≈-[F][?][E]★）
  - 地形、市街地、高地、森林、水域の表示
  - 友軍・敵軍・未確認の記号表示
  - ファイル: `app/services/map_renderer.py`

- [ ] 敵の能動的AI (ExCon) `cc:TODO`
  - 敵独自の作戦意図生成
  - 逆襲、側面浸透、偵察強化、欺瞞、火力集中、後退、予備投入、陽動の実装
  - ファイル: `app/services/excon_ai.py`

- [ ] 消耗資源管理 `cc:TODO`
  - 弾薬、燃料、整備余力、迎撃弾、精密誘導兵器の別管理
  - 3段階: 充足 / 低下 / 枯渇
  - ファイル: `app/models/game_state.py` + `app/services/adjudication.py`

### 優先度2：次に実装

- [ ] 上官命令システム `cc:TODO`
  - Intent, Mission, Constraints, ROE, Priorities, Time limit, Available forces, Reporting requirement
  - ファイル: `app/models/command.py`

- [ ] 詳細なSITREPフォーマット `cc:TODO`
  - 【日時】【テキストマップ】【状況】【味方戦力】【敵情報】【重要イベント】【上官命令】
  - 確認済み/推定/不明の区別
  - ファイル: `app/services/sitrep_generator.py`

- [ ] 判定基準の構造化 `cc:TODO`
  - 7つの主要条件での判定ロジック
  - 成功/部分成功/失敗の条件分析
  - ファイル: `app/services/adjudication.py` 更新

- [ ] 報告義務システム `cc:TODO`
  - Reporting requirement に基づく報告追跡
  - 報告がない場合の問い詰めイベント
  - ファイル: `app/services/reporting.py`

### 優先度3：余裕があれば実装

- [ ] 夜間・天候効果 `cc:TODO`
  - 夜間: NOD装置の有無が判定に影響
  - 降雨/霧/砂塵: 偵察精度、航空運用、砲兵観測に影響
  - ファイル: `app/services/weather_effects.py`

- [ ] 地形効果 `cc:TODO`
  - 森林、山岳、水域による戦力補正
  - 視界/遮蔽判定
  - ファイル: `app/services/terrain.py`

- [ ] 膠着状態ルール `cc:TODO`
  - 2ターン以上実質的行動がない場合の対応
  - 敵の積極行動/上官压力/外部イベント発生
  - ファイル: `app/services/stalemate.py`

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
