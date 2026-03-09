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
  - 実装: 13テスト全てパス

---

## 📦 アーカイブ

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
