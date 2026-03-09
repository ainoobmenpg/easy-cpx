# Plans.md

このファイルには、実装タスクを記録します。

---

## 🔴 進行中のタスク

(なし)

---

## 🟡 未着手のタスク (全36 Issue対応)

### フェーズ1：P0（8件）- セキュリティ・基盤

- [x] Issue #2: Fog of War漏洩を停止 - /api/game/{id}/stateで敵の真値を返さない `cc:完了` (2026-03-09)
  - 修正: 観測されていない敵ユニットの位置・typeを隠蔽、ammo/fuel/readiness/strengthは常にnull
  - ファイル: `backend/app/api/routes.py`

- [x] Issue #1: 起動時固定Game#1自動生成を廃止し、シナリオ開始フローへ一本化 `cc:完了` (2026-03-09)
  - 修正: startup_eventではinit_db()のみ実行、ゲーム自動生成はAPI経由（POST /api/games/, POST /api/game/start）のみ
  - ファイル: `backend/main.py`

- [x] Issue #3: 地形をgame単位で永続化 - 毎回再生成しない `cc:完了` (2026-03-09)
  - 修正: Gameモデルにmap_width/map_height追加、terrainをJSONとして保存
  - ファイル: `backend/app/models/`, `backend/app/services/initial_setup.py`

- [x] Issue #4: 攻撃目標の検証を追加 `cc:完了` (2026-03-09)
  - 修正: 攻撃目標の存在性・射程検証を追加、無効なターゲットは警告・失敗処理
  - ファイル: `backend/app/services/adjudication.py`

- [x] Issue #5: APIベースURLとCORSを環境変数化 `cc:完了` (2026-03-09)
  - 修正: .env.example追加、frontend API URL環境変数化、backend CORS環境変数化
  - ファイル: `frontend/`, `backend/main.py`

- [x] Issue #6: README/architectureのAPI一覧を実装と一致させる `cc:完了` (2026-03-09)
  - 修正: docs/architecture.mdのAPI一覧を実際のroutesと一致させる
  - ファイル: `docs/architecture.md`

- [x] Issue #7: マップサイズと座標上限をscenario駆動にする `cc:完了` (2026-03-09)
  - 修正: マップサイズをgame.map_width/map_heightから取得、ハードコード50を削除
  - ファイル: `backend/app/services/adjudication.py`, `backend/app/models/`

- [x] Issue #8: unit_type語彙を単一体系に統一する `cc:完了` (2026-03-09)
  - 修正: UnitType enum統一、LEGACY_UNIT_TYPE_MAP追加、TypeScript側でも型定義
  - ファイル: `shared/types/`, `backend/app/models/`

### 優先度：P1（コア機能）

- [x] Issue #9: MOVEの即時テレポートをやめ、移動量制限と地形コストを入れる `cc:完了`
  - ファイル: `backend/app/services/adjudication.py`
  - 実装: 移動量制限（ユニットタイプ別）と地形コストを追加し、即時テレポートを廃止

- [x] Issue #10: MOVE/RETREATの進行方向をside/scenario依存にする `cc:完了`
  - ファイル: `backend/app/services/adjudication.py`
  - 実装: side/scenarioベースの進行方向ロジックを追加

- [x] Issue #11: get_game_state()からinternal engineの責務を切り離す `cc:完了`
  - ファイル: `backend/app/api/routes.py`
  - 実装: 関数を分割し責務を明確化

- [x] Issue #12: AI契約を統一 - parse-orderとexcon-orderのID型を合わせる `cc:完了`
  - ファイル: `backend/app/services/ai_client.py`, `shared/schemas/`
  - 実装: ID型を統一

- [x] Issue #13: PlayerKnowledgeを実際のplayer viewに接続する `cc:完了`
  - 実装: player_knowledgeをAPIレスポンス(state)に追加し、 фронтенд が敵の最終確認位置等信息可以利用
  - ファイル: `backend/app/services/game_state_service.py`

- [x] Issue #14: CommanderOrderとreporting requirementをターン進行へ接続する `cc:完了`
  - 実装: DBのCommanderOrderからreporting_requirementsを取得しReportingSystemに設定
  - 偵察で敵接近(距離<=2)時にenemy_contactイベントを追加
  - 戦闘でプレイヤーユニットがdestroyされた時にunit_destroyedイベントを追加
  - ターン終了時にcheck_reporting_compliance()を呼び出して上官質疑を取得
  - ターン結果にcommander_inquiriesとreporting_summaryを追加
  - ファイル: `backend/app/services/adjudication.py`

- [x] Issue #15: GET /api/gamesを実装するか、完全に削除する `cc:完了`
  - 実装: GET /api/games エンドポイントを追加（全ゲームリスト取得）
  - ファイル: `backend/app/api/routes.py`

- [x] Issue #16: frontendのgameId=1既定値をやめる `cc:完了`
  - ファイル: `frontend/app/game/page.tsx`
  - 実装: gameIdをURLパラメータとして必須化

- [x] Issue #17: 敵行動結果をTurn/Eventテーブルへ保存する `cc:完了`
  - ファイル: `backend/app/services/adjudication.py`, `backend/app/models/`
  - 実装: 敵行動結果をDBに保存

- [x] Issue #18: 入力バリデーションを強化する `cc:完了`
  - ファイル: `backend/app/api/routes.py`, `shared/schemas/`
  - 実装: バリデーション強化

- [x] Issue #19: create_gameをquery paramではなくrequest body化する `cc:完了`
  - ファイル: `backend/app/api/routes.py`
  - 実装: すでにbody形式対応済み（変更なし）

- [x] Issue #20: InitialSetupServiceのイスラエル2026固定前提をscenario専用化する `cc:完了`
  - ファイル: `backend/app/services/initial_setup.py`
  - 概要: scenarioパラメータを追加し、scenarioからstart_date/start_time/weather/scenario_durationを取得可能にした

### 優先度：P2（リファクタリング・品質）

- [x] Issue #21: frontendのdefault template名称を整理する `cc:完了` (2026-03-09)
  - 実装: Next.jsスキャフォールドの不要ファイル(template/default由来)を削除
    - public/next.svg, vercel.svg, file.svg, window.svg
    - app/favicon.ico, page.module.css
  - ファイル: `frontend/`

- [x] Issue #22: frontend READMEをcreate-next-appの初期文面から置き換える `cc:完了`
  - 実装: create-next-appテンプレートのデフォルト文面を削除し、Operational CPXの説明に置き換え
  - ファイル: `frontend/README.md`

- [x] Issue #23: SQLite/PostgreSQL/Alembicの設定説明を整理する `cc:完了` (2026-03-09)
  - 修正: README.mdにDATABASE_URL環境変数・Alembic移行コマンドを追記、.env.exampleにDATABASE_URL追加
  - APIエンドポイント列表を/games/命名に統一
  - ファイル: `README.md`, `docs/architecture.md`, `.env.example`

- [x] Issue #24: route namingを統一する `cc:完了` (2026-03-09)
  - 修正: 既存のルートは既に/games/*に統一されているのを確認
  - ファイル: `backend/app/api/routes.py`

- [x] Issue #25: Fog of War向けUI表示をexact markerと分離する `cc:完了`
  - 実装: FoW関連UIマーカーを整理
  - ファイル: `frontend/app/game/page.tsx`

- [x] Issue #26: map rendererとfrontend mapの責務を整理する `cc:完了`
  - 実装: backend map rendererとfrontend mapの責務を整理
  - ファイル: `backend/app/services/`, `frontend/`

- [x] Issue #27: localizationの混在を修正する `cc:完了` (2026-03-09)
  - 修正: フロントエンドのUI文字列を日本語に統一（Start Mission→ミッション開始、Cancel→キャンセル、Loading...→読み込み中など）
  - ファイル: `frontend/app/scenarios/page.tsx`, `frontend/app/debriefing/page.tsx`, `frontend/app/game/page.tsx`

- [x] Issue #28: logging.basicConfig()をサービスモジュールから外す `cc:完了`
  - 実装: adjudication.pyからlogging.basicConfig()を削除、logger定義のみ残存
  - ファイル: `backend/app/services/adjudication.py`

- [x] Issue #29: DBモデルにcascade/orphan制御を入れる `cc:完了` (2026-03-09)
  - 実装: GameからUnit/Turn/Orderへのrelationshipにcascade="all, delete-orphan"を追加
  - UnitからOrder、TurnからOrder/Eventへのrelationshipもcascade追加
  - PlayerKnowledge/EnemyKnowledge/CommanderOrderへのrelationshipも追加
  - ファイル: `backend/app/models/__init__.py`

- [x] Issue #30: Game一覧・シナリオ選択・開始画面をfrontendに追加する `cc:完了` (2026-03-09)
  - 修正: /games页面を追加し、ゲーム一覧表示・継続プレイ機能を実装
  - ファイル: `frontend/app/games/page.tsx`, `frontend/app/lib/api.ts`

- [x] Issue #31: debriefingをAAR用に構造化する `cc:完了` (2026-03-09)
  - 実装: AAR形式（ver 1.0）に構造化、以下のセクションを追加
    - executive_summary: 重要指標・評価・コメントの要約
    - turn_summaries: 各ターンの命令・状況サマリー
    - combat_analysis: 戦闘力比率・損害分布・戦闘効果分析
    - resource_analysis: 弾薬・燃料・整備状態の評価
    - tactical_analysis: 戦術アプローチ・防御評価
    - lessons_learned: 構造化された教訓（カテゴリ・観察・教訓・影響）
  - 後方互換性を維持するため旧キー(mission_result, grade, statistics, commentary)も残存
  - ファイル: `backend/app/services/debriefing.py`

- [x] Issue #32: テスト追加 - Fog of War / terrain stability / target validation / scenario map size `cc:完了` (2026-03-09)
  - 実装: 新規テストファイルtest_p2_issues.pyを作成、以下のテストを追加
    - Fog of War: プレイヤーUnitの可視性、敵Unit非観測時の情報隠蔽
    - Terrain Stability: シード固定での地形生成一貫性、異なるシードでの地形差分
    - Target Validation: 攻撃ターゲットの範囲内/範囲外処理
    - Scenario Map Size: シナリオ設定からのマップサイズ取得
  - ファイル: `backend/tests/test_p2_issues.py`

- [x] Issue #33: OpenAPIサンプルを充实させる `cc:完了` (2026-03-09)
  - 実装: 各Pydantic schemaにjson_schema_extra exampleを追加
  - ファイル: `backend/app/api/routes.py`

- [x] Issue #34: true-state APIをinternal/admin専用に分離する `cc:完了` (2026-03-09)
  - 実装: /internal/games/{id}/true-state と /internal/games/{id}/units エンドポイントを追加、既存の/games/{id}/unitsはFoW適用に変更
  - ファイル: `backend/app/api/routes.py`

- [x] Issue #35: ExConの戦術ロジックをscenario非依存にする `cc:完了` (2026-03-09)
  - 実装: ハードコードされたマップサイズ(50, 30)をgame_stateから取得、scenario非依存に
  - ファイル: `backend/app/services/excon_ai.py`

- [x] Issue #36: frontendとbackendのroute/DTO共通定義をsharedに寄せる `cc:完了` (2026-03-09)
  - 実装: shared/types/index.tsにUnit, GameState, Sitrep, TurnLog, API Response型を追加
  - frontendのgame/page.tsxでshared/typesをimportして使用、tsconfig.jsonに@sharedパス追加
  - ファイル: `shared/types/index.ts`, `frontend/tsconfig.json`, `frontend/app/game/page.tsx`

---

## 📦 アーカイブ

### 2026-03-08 完了分

- [x] Reactパフォーマンス改善 (2026-03-08)
- [x] SVGレンダリング最適化 (2026-03-08)
- [x] マップサイズを50x50正方形に変更 (2026-03-08)
- [x] マップのD&D移動機能 (2026-03-08)
- [x] next.config.tsのTypeScriptエラーを修正 (2026-03-08)
- [x] エラー発生時のユーザー通知を追加 (2026-03-08)
- [x] アクセシビリティ属性の追加 (2026-03-08)
- [x] 地図への地形表示 (2026-03-08)
- [x] 地図への気象情報表示 (2026-03-08)
- [x] README.md 更新 (2026-03-08)
- [x] docs/game-rules.md 作成 (2026-03-08)
- [x] docs/architecture.md 作成 (2026-03-08)
- [x] マップサイズの拡大 (2026-03-08)
- [x] ユニット名の視認性向上 (2026-03-08)
- [x] 日付表示追加 (2026-03-08)
- [x] ユニット詳細パネルの充実 (2026-03-08)
- [x] 優先度4実装 (2026-03-08)
- [x] 優先度5実装 (2026-03-08)
- [x] テスト実装 (2026-03-08)
- [x] 基盤セットアップ (2026-03-08)
- [x] 共有スキーマ定義 (2026-03-08)
- [x] データベース設計 (2026-03-08)
- [x] コア機能実装 (2026-03-08)
- [x] UI実装 (2026-03-08)
- [x] テキストマップ生成 (2026-03-08)
- [x] 敵の能動的AI (2026-03-08)
- [x] 消耗資源管理 (2026-03-08)
- [x] 上官命令システム (2026-03-08)
- [x] 詳細なSITREPフォーマット (2026-03-08)
- [x] 判定基準の構造化 (2026-03-08)
- [x] 報告義務システム (2026-03-08)
- [x] 夜間・天候効果 (2026-03-08)
- [x] 地形効果 (2026-03-08)
- [x] 膠着状態ルール (2026-03-08)
