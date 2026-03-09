# CPX-2: 報告様式の標準化（SITREP/INTSUM/OPSUM/LOGSITREP/SALUTE）とAPI

### 背景
SITREPはあるが、INTSUM/OPSUM/LOGSITREPやSALUTE（敵情報）が未標準化。訓練評価と連動しづらい。

### 提案
- スキーマ: `shared/schemas` に各JSONスキーマを追加（セクション定義、信頼度タグ、SALUTE項目）。
- API: `/api/reports/sitrep|intsum|opsum|logsitrep` の返却をスキーマ準拠に。保存は`Turn`か専用`reports`テーブル。
- AI補助: `ai_client` の出力をスキーマ検証して保存（不正はフォールバック）。
- UI: `Situation`タブに各レポートのタブ切替、SALUTEタグ表示。

### 受け入れ基準
- 4種レポートの返却JSONがスキーマバリデーションを通過。
- SALUTE形式で敵情報を提示し、推定/未確認は明確に区別。
- AAR集計に各レポートの指標が取り込まれる。
