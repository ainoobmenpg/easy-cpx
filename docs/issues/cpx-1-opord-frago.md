# CPX-1: OPORD/FRAGO（SMESC）データモデル＋エディタ

### 背景
NATO CPXの中核であるOPORD/FRAGO（SMESC: Situation, Mission, Execution, Service Support, Command & Signal）が未実装。現在は自由文の上官命令とSITREPに依存しており、計画→同期→実行の参謀プロセスが表現できていない。

### 提案
- データモデル: `opords`（SMESC各節、ROE、CCIR、通計画、有効期間）、`fragos`（変更差分、発令時刻）を追加。`Game`に`opord_id`、`Order`に`frago_id`を外部キーで接続。
- API: `POST/GET /api/opord`, `POST/GET /api/frago`（履歴取得、差分比較）。
- UI: `Plan`タブを新設し、SMESCフォーム編集＋発令（FRAGO）を可能に。ゲームログに発令記録。
- 審判連動: `Execution`/`Service Support`の整合度を判定前提に反映（未整合時は成功上限=Partial）。

### 受け入れ基準
- OPORD/FRAGOを作成・更新・参照でき、発令履歴がTurnに記録される。
- SMESC各節がJSONで保持され、APIスキーマはdocsに定義されている。
- AdjudicationがOPORD/FRAGOの整合度を参照して結果に影響を与える。
