# Plans.md

このファイルには、実装タスクを記録します。

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

## 🔵 新規タスク (Issues #70+)

- [x] Issue #71: CPX-5: CCIR/PIR/ROE 等の前提を審判に連結（Adjudication v1.5） `cc:完了`
  - 依存: なし（基盤）
  - 完了: 2026-03-10
  - 実装:
    1. shared/types/index.ts にCCIR/PIR/ROE型を追加（CCIR: CriticalCollectionRequirement/IntelligenceRequirement/OperationalRequirement, PIR: PriorityIntelligenceRequirement, ROE: RulesOfEngagement）
    2. backend/app/services/arcade_adjudication.py にCCIR評価機能を追加（check_ccir_met メソッド、CCIR発動条件判定）
    3. backend/app/services/debriefing.py にCCIRサマリーを追加
    4. backend/tests/test_arcade_adjudication.py にCCIRテストを追加

- [x] Issue #72: CPX-6: 多役割RBAC（BLUE/RED/WHITE/Observer）＋リアルタイム通知 `cc:完了`
  - 依存: なし（基盤）
  - 完了: 2026-03-10
  - 実装:
    1. shared/types/index.ts にRoleType, User, WebSocketMessage, NotificationPayload 型を追加
    2. backend/app/models/__init__.py にUser, UserRole, GamePlayerモデルを追加
    3. backend/app/services/rbac_service.py を作成（役割判定、権限チェック）
    4. backend/app/services/notification_service.py を作成（WebSocket通知）
    5. backend/tests/test_rbac.py を作成（26テスト全てパス）

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
