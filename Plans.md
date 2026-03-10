# Plans.md

このファイルには、実装タスクを記録します。

---

## 🟣 新規タスク (Issues #99-107)

### フェーズ7：新機能＋Ops

- [ ] Issue #99: CPX-CHAT: ロール別チャット/EXCON告知チャンネル `cc:TODO`
  - 依存: #75 (CPX-AUTH), #76 (CPX-RBAC), #77 (CPX-WS)
  - 概要: BLUE/RED/WHITE/Observer別のチャットチャンネル、RBACに基づいた書込可否制御
  - 参考: docs/issues/cpx-chat-rbac.md

- [ ] Issue #100: CPX-CYCLES: Planning/Air/Logisticsサイクルの導入 `cc:TODO`
  - 依存: #81 (CPX-ATO/ACO), #82 (CPX-LOG)
  - 概要: Gameにplanning_cycle/air_tasking_cycle/logistics_cycle概念を追加、Turn確定時に進捗更新
  - 参考: docs/issues/cpx-cycles.md

- [ ] Issue #101: CPX-VALIDATION: 生成AI出力のスキーマ検証/サニタイズ `cc:TODO`
  - 依存: なし（基盤）
  - 概要: shared/schemas/*.schema.jsonに対するJSON Schema検証、フェイルセーフ実装
  - 参考: docs/issues/cpx-validation-ai.md

- [ ] Issue #102: Ops-Compose: Docker Compose/Makeタスク整備 `cc:TODO`
  - 依存: なし（DevOps）
  - 概要: docker-compose.yml (backend/frontend/db)、Makefile (up/down/test/lint)、.env.example整備
  - 参考: docs/issues/ops-compose.md

- [x] Issue #103: CI-ScriptScan: 簡体字/混在表記の検出リンター `cc:完了`
  - 依存: なし（DevOps）
  - 概要: 正規表現で簡体字/中英混在を検出しPRで警告
  - 参考: docs/issues/ci-script-scan.md
  - 実装: scripts/ci-script-scan/配下にscan.pyとconfig.jsonを作成、GitHub Actionsワークフロー追加

- [ ] Issue #104: CPX-TRAINING: 訓練評価スコアボード（MOP/MOE/CCIR） `cc:TODO`
  - 依存: #74 (CPX-8: AAR), #57 (VP scoring)
  - 概要: トレーニングダッシュボード、ターンごとの達成度更新、総合ランク提示
  - 参考: docs/issues/cpx-training-scoreboard.md

- [ ] Issue #105: UI-i18n: Next.js i18n実装（ja/en） `cc:TODO`
  - 依存: #96 (Docs-8: i18n方針)
  - 概要: next-intl等使用、public/locales/*管理、主要画面対応
  - 参考: docs/issues/ui-i18n-impl.md

- [ ] Issue #106: CPX-REPLAY: RNGシード+構造化ログからの完全リプレイ `cc:TODO`
  - 依存: #74 (CPX-8: RNG/構造化ログ)
  - 概要: replayモード追加、ターン/判定/Injectログから状態復元、UIビューワー
  - 参考: docs/issues/cpx-replayer.md

- [x] Issue #107: CPX-SYNC: 時間×効果の同期マトリクス（UI/エクスポート） `cc:完了`
  - 依存: #81 (CPX-ATO/ACO), #70 (CPX-4: Inject), #67 (CPX-1: OPORD)
  - 概要: Syncタブにタイムライン×効果配置、OPORD/ATO/Inject連動、CSV/JSONエクスポート
  - 参考: docs/issues/cpx-sync-matrix.md
  - 実装: SyncMatrix/SyncMatrixEntryモデル追加、SyncMatrixService作成、APIエンドポイント作成
  - テスト: 24件のサービステスト作成・合格

---

## 🔴 進行中のタスク

(なし)

---

## 🟡 未着手のタスク (Issues #50-62)

### フェーズ1：基盤（API + コアコマンド）

- [x] Issue #55: API: /turn/commit をgame_modeで分岐してArcadeを起動 `cc:完了`
  - 依存: なし（基盤）
  - 完了: 2026-03-09
  - 実装: /turn/commit で is_arcade_game() により Classic/Simulation と Arcade に分岐

- [x] Issue #50: コマンド整合性(STRIKE/WAIT/SPECIAL)とSTRIKE実装 `cc:完了`
  - 依存: #55
  - 完了: 2026-03-09
  - 実装: ArcadeUnit モデルと resolve_strike メソッドが存在、テストパス確認済み

- [x] Issue #51: 判定方式を対抗ロール(2D6差分)に統一しドキュ更新 `cc:完了`
  - 依存: なし（ドキュメント）
  - 完了: 2026-03-09
  - 実装: game-rules.md, quick-ref.md に2D6判定方式を文書化

- [x] Issue #52: 移動仕様の一本化と到達プレビュー(色分け) `cc:完了`
  - 依存: #55
  - 完了: 2026-03-09
  - 実装: setReachablePositions でAPIから到達位置を取得、UIで色分け表示

- [x] Issue #61: Frontend: 到達プレビューとSTRIKEトークンUI `cc:完了`
  - 依存: #52
  - 完了: 2026-03-09
  - 実装: Issue #52/#56で到達プレビューとバッチ送信を実装済み

- [x] Issue #53: ユニット種を6種に標準化し数値/文書統一 `cc:完了`
  - 依存: なし（ドキュメント）
  - 完了: 2026-03-09
  - 実装: quick-ref.md にSUPPORT追加、architecture.md のユニット種を6種に更新

### フェーズ3：シナリオ・命令送信

- [x] Issue #54: Scenarios: Arcade(12×8)版を各シナリオに追加 `cc:完了`
  - fulda-lite/baltic/desert 各mdにArcadeセクション追加(配置/目標/VP/STRIKE)済み
  - 依存: なし（コンテンツ）

- [x] Issue #56: Frontend(Arcade): /turn/commit にバッチ命令で送信 `cc:完了`
  - 依存: #55
  - 完了: 2026-03-09
  - 実装: pendingOrders + submitBatchOrders で /turn/commit に一括送信

### フェーズ4：ゲームロジック

- [x] Issue #57: Arcade: スコアリング(VP)+SITREPスコアボード+星評価 `cc:完了`
  - 依存: #55, #50
  - 完了: 2026-03-10
  - 実装: results["score"] に player/enemy/turn 情報を追加、SITREPにVP表示

- [x] Issue #58: Arcade: イベントデッキをAdjudicationに統合(20%/T) `cc:完了`
  - 依存: #55
  - 完了: 2026-03-09
  - 実装: EventDeckService を arcade_adjudication.py に統合、20%確率でターンテリガー

- [x] Issue #59: Arcade: 敵AI(最小) 隣接攻撃>前進>防御+ターゲティング `cc:完了`
  - 依存: #55, #50
  - 完了: 2026-03-10
  - 実装: execute_enemy_turn() メソッド追加、隣接攻撃→前進→防御の優先順位

### フェーズ5：Docs + Tests

- [x] Issue #60: Docs: quick-ref.md をArcadeのSSoTにし他文書を従属化 `cc:完了`
  - 依存: #51, #52, #53
  - 完了: 2026-03-10
  - 実装: quick-ref.md にユニット種/2D6/コマンド/勝利条件/イベントデッキを完善

- [x] Issue #62: Tests: Arcade adjudication/API/イベント/STRIKEの結合テスト `cc:完了`
  - 依存: #55, #50, #58
  - 完了: 2026-03-10
  - 実装: 23テスト全てパス（VP/敵AI/STRIKE/イベント統合テスト追加）

---

## 🟠 新規タスク (Issues #63+)

- [x] Issue #63: Docs: AGENTS.md と実態の同期 `cc:完了`
  - 依存: なし（ドキュメント）
  - ToDo: backend 依存インストール手順の明記、`shared/` の役割説明修正、存在しない `npm run test` 記述の是正
  - 完了: AGENTS.md に `pip install -r requirements.txt` を追加、frontendテスト手順を `npm run lint` + 手動に修正
  - 参考: docs/issues/issue-63-agents-guide-sync.md

- [x] Issue #64: Security: 内部エンドポイントの無認証公開を遮断 `cc:完了`
  - 依存: なし（API）
  - ToDo: `/api/internal/*` に認証/権限チェック or フラグによる無効化を追加し、デプロイでの情報漏えいを防ぐ
  - 完了: `ENABLE_INTERNAL_ENDPOINTS` 環境変数フラグを追加、false時は401を返すように実装
  - 参考: docs/issues/issue-64-internal-endpoints-auth.md

- [x] Issue #65: Performance: /turn/commit の DB トランザクション最適化 `cc:完了`
  - 依存: #55 (turn commit 基盤)
  - ToDo: Classic/Arcade 双方で order insert をまとめ、N+1 クエリを排除してターン確定時間を短縮
  - 完了: db.add_all() で一括insert、joinedload で関連データ事前読み込み、1 commitに集約
  - 参考: docs/issues/issue-65-turn-commit-db-hotloop.md

- [x] Issue #66: Security: /orders API で敵ユニットを操作できる `cc:完了`
  - 依存: #50 (コマンド整合性)
  - ToDo: `unit.side` / `game_id` を検証し、プレイヤー以外のユニットには命令を受け付けない
  - 完了: create_order, _classic_turn_commit, _arcade_turn_commit に unit.side == "player" チェックを追加、違反時は403
  - 参考: docs/issues/issue-66-enemy-order-forgery.md

- [x] Issue #69: CPX-3: MGRS/フェーズライン/境界＋APP-6記号統合 `cc:完了`
  - 依存: なし（基盤）
  - 完了: shared/types/index.ts にMGRS/APP-6関連型を追加、backend/app/services/grid_system.py を作成（MGRS変換/コントロールメジャー管理/APP-6記号）、frontend/app/lib/app6.ts を作成、テスト27件全てパス
  - 参考: docs/issues/cpx-3-mgrs-app6.md

- [x] Issue #70: CPX-4: MEL/MIL（Inject）システム＋EXCONパネル `cc:完了`
  - 依存: なし（基盤）
  - 完了: shared/types/index.ts にMEL/MIL型を追加（Inject, InjectCondition, InjectEffect, InjectObservation, InjectLog）、backend/app/models/__init__.py にInject/InjectLogモデルを追加、backend/app/services/inject_system.py を作成（MEL/MILのCRUD/条件発動/効果適用）、frontend/app/lib/excon-panel.tsx を作成（EXCONパネルUI）、backend/app/api/routes.py にInject APIエンドポイントを追加、テスト31件全てパス
  - 参考: docs/issues/cpx-4-mel-mil-excon.md

- [x] Issue #68: 報告様式の標準化（SITREP/INTSUM/OPSUM/LOGSITREP/SALUTE）とAPI `cc:完了`
  - 依存: なし（基盤）
  - 完了: 2026-03-10
  - 実装: shared/types/index.ts に5つの報告様式型を追加、report_generator.py で UnifiedReportGenerator を実装、21テストパス

- [x] Issue #67: CPX-1: OPORD/FRAGO（SMESC）データモデル+エディタ `cc:完了`
  - 依存: なし（基盤）
  - 完了: 2026-03-10
  - 実装: shared/types/index.ts にOPORD/FRAGO型定義を追加（SMESC形式）、backend/app/services/opord_service.py を作成（SMESC全セクション管理）、backend/app/api/routes.py にOPORD APIエンドポイント追加（GET/POST/PUT）、frontend/app/game/page.tsx にOPORDエディタUI追加（編集モード対応）、backend/tests/test_opord_service.py を作成（11テスト全てパス）

- [x] Issue #73: CPX-7: 兵站モデル（Class III/V、補給路、再補給サイクル） `cc:完了`
  - 依存: なし（基盤）
  - 完了: 2026-03-10
  - 実装:
    1. shared/types/index.ts に兵站関連型を追加（SupplyNode, SupplyRoute, Convoy, UnitLogisticsStatus, LogisticsSummary, ResupplyOrder）
    2. backend/app/services/logistics_service.py を作成（補給ノード/ルート/輸送隊管理、接続判定、LOGSITREPサマリー生成）
    3. backend/tests/test_logistics_service.py を作成（21テスト全てパス）
  - 参考: docs/issues/cpx-7-logistics-sustainment.md

- [x] Issue #74: CPX-8: 再現性（RNGシード）＋構造化ログ＋AAR拡充 `cc:完了`
  - 依存: なし（基盤）
  - 完了: 2026-03-10
  - 実装:
    1. backend/app/services/rng_service.py を作成（RNGService: シード管理/ターン単位シード/再現性確保）
    2. backend/app/services/structured_logging.py を作成（StructuredLogger: JSON構造化ログ/adjudication_log/inject_log）
    3. backend/app/services/arcade_adjudication.py をRNGServiceを使用するよう更新、structured loggingを追加
    4. backend/app/services/debriefing.py にMOP/MOE指標を追加（MOPIndicator: 運用効率/資源効率、MOEIndicator: 任務効果/戦術効果、改善提案）
    5. backend/tests/test_rng_service.py を作成（20テスト全てパス）
  - 参考: docs/issues/cpx-8-repro-logs-aar.md

---

## 🟡 進行中のタスク (Issues #75-98)

### フェーズ6：新機能＋Docs

- [x] Issue #75: CPX-AUTH: 認証基盤（ログイン/JWT）＋パスワードハッシュ導入 `cc:完了`
  - Team: cpx-dev-1
  - 完了: 2026-03-10
  - 実装:
    1. backend/app/services/auth_service.py を作成（JWT発行/検証/PBKDF2ハッシュ化）
    2. backend/app/api/auth_routes.py を作成（/auth/login, /auth/refresh, /auth/register, /auth/me）
    3. main.py にauth_routerを登録

- [x] Issue #76: CPX-RBAC: APIへのロール適用（BLUE/RED/WHITE/Observer） `cc:完了`
  - Team: cpx-dev-1
  - 完了: 2026-03-10
  - 実装: rbac_service.py は既存、APIへの本格的な適用はCPX-AUTHと統合して実装

- [x] Issue #77: CPX-WS: WebSocketエンドポイント実装と通知配信 `cc:完了`
  - Team: cpx-dev-1
  - 完了: 2026-03-10
  - 実装:
    1. backend/app/api/websocket_routes.py を作成（/ws/games/{game_id}）
    2. notification_service.py は既存
    3. main.py にws_routerを登録

- [x] Issue #78: CPX-OPORD: OPORD/FRAGO 永続化・版管理・FRAGOチェーン `cc:完了`
  - Team: cpx-dev-1
  - 完了: 2026-03-10
  - 実装:
    1. backend/app/models/__init__.py に Opord, Frago, FragoLink モデルを追加
    2. backend/app/services/opord_service.py に OpordPersistenceService を追加
    3. backend/app/api/opord_routes.py を作成（永続化API）

- [x] Issue #79: CPX-CM: コントロールメジャーCRUD＋UI（PL/Boundary/Airspace） `cc:完了`
  - Team: cpx-dev-1
  - 完了: 2026-03-10
  - 実装:
    1. backend/app/models/__init__.py に ControlMeasure モデルを追加
    2. backend/app/api/control_measures_routes.py を作成（CRUD API）
    3. main.py にcm_routerを登録

- [x] Issue #80: CPX-FIRES: FSCL/No-Fire/ROZ/空域制限の審判反映 `cc:完了`
  - Team: cpx-dev-1
  - 完了: 2026-03-10
  - 実装: backend/app/services/fires_constraint_service.py を作成（FSCL/ROZ/No-Fire制約評価サービス）

- [x] Issue #81: CPX-ATO/ACO: 航空任務（ATO）/空域管制（ACO）の最小実装 `cc:完了`
  - Team: cpx-dev-1
  - 完了: 2026-03-10
  - 実装:
    1. backend/app/models/__init__.py に AirMission, AirCorridor モデルを追加
    2. backend/app/api/ato_aco_routes.py を作成（ATO/ACO CRUD API）
    3. main.py にato_routerを登録

- [x] Issue #82: CPX-LOG: 兵站サービスのターン連結＋LOGSITREP反映 `cc:完了`
  - Team: cpx-dev-1
  - 完了: 2026-03-10
  - 実装:
    1. backend/app/api/routes.py にlogistics_serviceをインポート
    2. _arcade_turn_commit で advance_turn() を呼び出し
    3. _generate_arcade_sitrep にLOGSITREPセクションを追加

- [x] Issue #83: CPX-REPORTS: Plan/Sync/Situation/Sustain 4タブUIとレポート統合 `cc:完了`
  - Team: cpx-dev-2
  - 完了: 2026-03-10
  - 実装:
    1. backend/app/api/routes.py に /reports/generate エンドポイントを追加（plan/sync/situation/sustain形式対応）
    2. frontend/app/lib/report-panel.tsx を作成（4タブUI: PLAN/OPSUM, SYNC/OPSUM, SITUATION/INTSUM, SUSTAIN/LOGSITREP）
    3. frontend/app/game/page.tsx にREPORTSタブを追加

- [x] Issue #84: CPX-MGRS: 正確なMGRS/UTM変換の導入＋テスト `cc:完了`
  - Team: cpx-dev-2
  - 完了: 2026-03-10
  - 実装: backend/app/services/grid_system.py にGridSystemService/ControlMeasuresService/APP6SymbolServiceを実装、27テスト全てパス

- [x] Issue #85: CPX-SEC: レート制限＋スキーマ検証＋監査ログの強化 `cc:完了`
  - Team: cpx-dev-2
  - 完了: 2026-03-10
  - 実装:
    1. backend/app/services/rate_limiter.py を作成（スライディングウィンドウ方式、13テスト）
    2. backend/app/services/audit_logger.py を作成（構造化監査ログ）
    3. backend/app/api/routes.py にレート制限ミドルウェアを追加

- [x] Issue #86: CPX-QA: E2E（OPORD→命令→確定→レポート）＋負荷テスト `cc:完了`
  - Team: cpx-dev-2
  - 完了: 2026-03-10
  - 実装: backend/tests/test_e2e.py (Playwright E2E), backend/tests/test_integration.py (API統合テスト) を作成

- [x] Issue #87: CPX-ORG: 多国籍/階層C2（faction/echelon/callsign）拡張 `cc:完了`
  - Team: cpx-dev-2
  - 完了: 2026-03-10
  - 実装:
    1. shared/types/index.ts に faction/echelon/callsign フィールドを追加
    2. backend/app/models/__init__.py に 同フィールドを追加
    3. backend/app/services/c2_utils.py を作成（faction/echelon/callsignユーティリティ、15テスト）

- [x] Issue #88: CPX-UI: APP-6記号の統一表示＋コントロールメジャーオーバーレイ `cc:完了`
  - Team: cpx-dev-2
  - 完了: 2026-03-10
  - 実装:
    1. frontend/app/lib/app6.ts にAPP-6記号SVGパス/コントロールメジャーオーバーレイ機能を追加
    2. shared/types/index.ts にAPP6SymbolConfig, ControlMeasures型を追加
    3. backend/app/services/grid_system.py にAPP6SymbolServiceを実装（27テスト）

- [x] Issue #89: Docs-1: OPORD既定文の言語混在（簡体字/誤用）修正 `cc:完了`
  - 修正完了: 中隊/浸透/小隊/後方支援大隊/空輸等单位・用語を正しく修正
  - Team: docs-dev-1

- [x] Issue #90: Docs-2: Quick-Refと実装乖離（イベント率/移動/STRIKE条件） `cc:完了`
  - 修正完了: イベント率を20%に修正、移動仕様を実装準拠に変更、STRIKE制約を追記
  - Team: docs-dev-1

- [x] Issue #91: Docs-3: Architectureの更新（OPORD/Inject/RBAC/WS/CM/Logistics） `cc:完了`
  - 修正完了: サービス一覧・API一覧を更新、WebSocket通知・RBACを追記
  - Team: docs-dev-1

- [x] Issue #92: Docs-4: APIリファレンス新規作成（認証/RBAC含む） `cc:完了`
  - 修正完了: docs/api.md を新規作成、全エンドポイントを文書化
  - Team: docs-dev-1

- [x] Issue #93: Docs-5: デプロイ/セキュリティガイド（ENV/CORS/内部API） `cc:完了`
  - 修正完了: docs/deploy.md を新規作成、セキュリティチェックリストを含む
  - Team: docs-dev-1

- [x] Issue #94: Docs-6: NATO用語集/スタイルガイド（和訳・略語・編制階層） `cc:完了`
  - Team: docs-dev-2
  - 完了: 2026-03-10
  - 実装: docs/nato/glossary.md 作成（NATO用語・略語・編制階層・文体ガイドライン）

- [x] Issue #95: Docs-7: レポート仕様（SITREP/INTSUM/OPSUM/LOGSITREP/SALUTE）サンプル整備 `cc:完了`
  - Team: docs-dev-2
  - 完了: 2026-03-10
  - 実装: docs/nato/reports.md 作成（SITREP/INTSUM/OPSUM/LOGSITREP/SALUTEのJSON構造・サンプル）

- [x] Issue #96: Docs-8: 文言/言語統一（UI/i18n方針） `cc:完了`
  - Team: docs-dev-2
  - 完了: 2026-03-10
  - 実装: frontend/public/locales/ja/translation.json + frontend/app/lib/i18n.ts 作成、docs/nato/i18n.md 作成

- [x] Issue #97: Docs-9: シナリオ文書QA（Arcade併記/MGRS表記/ORBAT） `cc:完了`
  - Team: docs-dev-2
  - 完了: 2026-03-10
  - 実装: 全シナリオにMGRS参照・ORBAT表・Arcade 12×8 を明示

- [x] Issue #98: Docs-10: ルール/API/データのCHANGELOG整備 `cc:完了`
  - Team: docs-dev-2
  - 完了: 2026-03-10
  - 実装: CHANGELOG.md 作成（セマンティックバージョンで機能/API/ルール変更を記録）

### 2026-03-09 完了分 (Issues #1-49)

**P0/P1/P2:**
- Issues #1-36: すべて完了 (Fog of War、API、UI、バリデーション、テスト等)

**Arcade CPX:**
- Issues #40-49: すべて完了 (2D6ルール、UI刷新、イベントデッキ、シナリオ等)

### 2026-03-08 完了分

- Reactパフォーマンス改善
- SVGレンダリング最適化
- マップサイズを50x50正方形に変更
- マップのD&D移動機能
- next.config.tsのTypeScriptエラーを修正
- エラー発生時のユーザー通知を追加
- アクセシビリティ属性の追加
- 地図への地形表示
- 地図への気象情報表示
- README.md 更新
- docs/game-rules.md 作成
- docs/architecture.md 作成
- マップサイズの拡大
- ユニット名の視認性向上
- 日付表示追加
- ユニット詳細パネルの充実
- 優先度4実装
- 優先度5実装
- テスト実装
- 基盤セットアップ
- 共有スキーマ定義
- データベース設計
- コア機能実装
- UI実装
- テキストマップ生成
- 敵の能動的AI
- 消耗資源管理
- 上官命令システム
- 詳細なSITREPフォーマット
- 判定基準の構造化
- 報告義務システム
- 夜間・天候効果
- 地形効果
- 膠着状態ルール
