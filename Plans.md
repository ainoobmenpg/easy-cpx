# Plans.md

このファイルには、実装タスクを記録します。

---

## 🟢 新規タスク (Issues #125)

### フェーズ10：緊急バグ修正

- [x] Issue #125: connection-indicator の next-i18next import で /scenarios などが500になる `cc:完了`
  - 概要: connection-indicator.tsx が未依存の next-i18next をimportしている問題を修正
  - 対応: useI18n() ベースへ揃えた（useTranslation → useI18n）
  - GitHub: #125

---

## 🟢 新規タスク (Issues #126-128 + #69)

### フェーズ11：緊急バグ修正

- [x] Issue #126: /game 初回表示でレポート API が SitrepGenerator import 失敗し500になる `cc:完了`
  - 概要: generate_report() が存在しない SitrepGenerator をimportしている問題を修正
  - 対応: routes.py のimportを実際のgenerator APIへ修正（SitrepGenerator → SITREPGenerator）
  - GitHub: #126

- [x] Issue #127: /games が game_mode enum の保存値不整合で500になる `cc:完了`
  - 概要: DBのlowercase値とenum定義の不一致でLookupError発生
  - 対応: Enum設定にvalues_callableを追加して小文字値をサポート
  - GitHub: #127

- [x] Issue #128: デスクトップの /game 画面で raw translation key がそのまま表示される `cc:完了`
  - 概要: translation.jsonに不足キーがあり、t()でラップされていない箇所がある
  - 対応: game/page.tsxの固定日本語文言をt()化（遊び方/敵/味方/地形 etc.） + locale JSONに不足キー追加
  - GitHub: #128

- [x] Issue #69: Order.turn比較バグ修正 (routes.py:1537) `cc:完了`
  - 概要: Order.turn <= target_turn でrelationship比較になりNotImplementedError発生
  - 対応: Turn joinへ修正（Order.turn.turn_number → Turn.turn_number）
  - 日付: 2026-03-11

---

## 🔴 未完了タスク

### Issue #68: game_mode DB migration
- 問題: DBに旧uppercase値 (SIMULATION, ARCADE, REPLAY) が残存の可能性
- 対応: 必要に応じて lowercase へ ALTER TABLE
- マーカー: `cc:TODO`

---

## 🟢 新規タスク (Issues #121-124)

### フェーズ11：緊急バグ修正

- [x] Issue #126: /game 初回表示でレポート API が SitrepGenerator import 失敗し500になる `cc:完了`
  - 概要: generate_report() が存在しない SitrepGenerator をimportしている問題を修正
  - 対応: routes.py のimportを実際のgenerator APIへ修正（SitrepGenerator → SITREPGenerator）
  - GitHub: #126

- [x] Issue #127: /games が game_mode enum の保存値不整合で500になる `cc:完了`
  - 概要: DBのlowercase値とenum定義の不一致でLookupError発生
  - 対応: Enum設定にvalues_callableを追加して小文字値をサポート
  - GitHub: #127

- [x] Issue #128: デスクトップの /game 画面で raw translation key がそのまま表示される `cc:完了`
  - 概要: translation.jsonに不足キーがあり、t()でラップされていない箇所がある
  - 対応: game/page.tsxの固定日本語文言をt()化（遊び方/敵/味方/地形 etc.）
  - GitHub: #128

---

## 🟢 新規タスク (Issues #121-124)

### フェーズ9：緊急バグ修正

- [x] Issue #121: CORS: 127.0.0.1アクセス時のlocalhost固定問題を修正 `cc:完了`
  - 概要: API URLを localhost 固定ではなく Window.location に基づいて動的に解決
  - GitHub: #121

- [x] Issue #122: /training が未実装APIに向いている問題を修正 `cc:完了`
  - 概要: /training ページが未実装のNext.js API endpointを指している問題を修正
  - GitHub: #122

- [x] Issue #123: DBスキーマ不整合による500エラー解決 `cc:完了`
  - 概要: /games とシナリオ開始時に DB スキーマ不整合で500調査と修正
エラーが発生している問題の  - GitHub: #123

- [x] Issue #124: i18n対象漏れの対応 `cc:完了`
  - 概要: /scenarios /games /training の未翻訳キーと固定文言をlocalesに移植
  - GitHub: #124

---

## 🟢 新規タスク (Issues #108-120)

### フェーズ8：UI改善 + バグ修正

- [x] Issue #108: UI-i18n: Next.js i18n実装（ja/en） `cc:完了` - 既存実装済（i18n-provider, locales, language-switcher）
- [x] Issue #109: CPX-REPLAY: RNGシード+構造化ログからの完全リプレイ `cc:完了` - backend replay_service実装濟み、frontend replay page実装濟み
- [x] Issue #110: UI-1: バックエンド接続インジケータ＋APIベースURL診断 `cc:完了` - games/scenariosページに追加、ConnectionStateエクスポート追加
- [x] Issue #111: UI-2: 存在しない/new-gameリダイレクトの修正 `cc:完了` - /gamesへのリダイレクトに修正
- [x] Issue #112: UI-3: 文言/タイポ修正（日本語） `cc:完了` - 戦闘オッドン→戦闘オッズ
- [x] Issue #113: UI-4: 右ペインをCPX 4タブ（Plan/Sync/Situation/Sustain）に再編 `cc:完了` - report-panel.tsxに4タブ実装済み
- [x] Issue #114: UI-5: APP-6記号表示の統一＋コントロールメジャー重ね合わせ `cc:完了` - app6.tsxにUnitMarker/コントロールメジャー実装濟み、レイヤトグルボタン実装濟み
- [x] Issue #115: UI-6: アクセシビリティ/ショートカット/フォーカス `cc:完了` - キーボードショートカット追加(P/B/A/Arrow keys)、aria-label追加
- [x] Issue #116: UI-7: パン/ズームのパフォーマンス最適化 `cc:完了` - rAF + willChangeで60fps目標
- [x] Issue #117: UI-8: エラーハンドリング/ローディングの標準化 `cc:完了` - useToast/ErrorDisplay/LoadingDisplay統合
- [x] Issue #118: UI-9: シナリオランチャ（選択→開始）導線の強化 `cc:完了`
  - 概要: シナリオカード選択後に「開始」ボタンを直接表示、selectHintで導線補充、モーダルで詳細確認も可能
- [x] Issue #119: UI-10: i18n対象漏れ/固定文面の洗い出し `cc:完了` - game.page.tsxの固定文面をi18n化（ユニット/レイヤー/戦闘オッズ/SITREP履歴）
- [x] Issue #120: API-1: /api/games/startが/api/games/{game_id}と競合 `cc:done`

---

## 🟣 新規タスク (Issues #99-107)

### フェーズ7：新機能＋Ops

- [x] Issue #99: CPX-CHAT: ロール別チャット/EXCON告知チャンネル `cc:完了` - Commander/Staff/EXCONチャンネル実装、EXCON告知チャンネル追加
- [x] Issue #100: CPX-CYCLES: Planning/Air/Logisticsサイクルの導入 `cc:完了` - cycle_manager.py + Gameモデル + game_state_service更新、UI表示追加
- [x] Issue #101: CPX-VALIDATION: 生成AI出力のスキーマ検証/サニタイズ `cc:完了` - validation_service.py実装、22テスト合格
- [x] Issue #102: Ops-Compose: Docker Compose/Makeタスク整備 `cc:完了` - docker-compose.yml, Makefile, .env.example整備
- [x] Issue #103: CI-ScriptScan: 簡体字/混在表記の検出リンター `cc:完了`
- [x] Issue #104: CPX-TRAINING: 訓練評価スコアボード（MOP/MOE/CCIR） `cc:完了` - training_scoreboard.py + /trainingページ実装
- [x] Issue #105: UI-i18n: Next.js i18n実装（ja/en） `cc:完了` - i18n-provider + locales実装
- [x] Issue #106: CPX-REPLAY: RNGシード+構造化ログからの完全リプレイ `cc:完了` - replay_service.py + /replayページ実装
- [x] Issue #107: CPX-SYNC: 時間×効果の同期マトリクス（UI/エクスポート） `cc:完了`

---

## 🔴 進行中のタスク

(なし)

---

## 📦 アーカイブ

### 完了済みタスク (Issues #99-124)

- **Issues #99-107**: すべて完了 (CPX-CHAT/CYCLES/VALIDATION/Ops-Compose/TRAINING/REPLAY/SYNC等) - 2026-03-10
- **Issues #108-120**: すべて完了 (UI改善10件+API修正、i18n/接続インジケータ/シナリオランチャ等) - 2026-03-10
- **Issues #121-124**: すべて完了 (CORS/DB/i18n等緊急バグ修正) - 2026-03-10

### 完了済みタスク (Issues #1-98)

- **Issues #1-49**: すべて完了 (Fog of War、API、UI、バリデーション、テスト等) - 2026-03-09
- **Issues #50-62**: すべて完了 (2D6ルール、UI刷新、イベントデッキ、シナリオ等) - 2026-03-09/10
- **Issues #63-74**: すべて完了 (OPORD/Inject/Logistics/RNG/AAR等) - 2026-03-10
- **Issues #75-98**: すべて完了 (AUTH/RBAC/WS/ATO/ACO/Fires/Reports等) - 2026-03-10
