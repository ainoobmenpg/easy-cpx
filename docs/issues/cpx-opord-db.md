# CPX-OPORD: OPORD/FRAGO 永続化・版管理・FRAGOチェーン

### 背景
現在のOPORDはサービス内メモリ保持。訓練では版管理とFRAGO差分履歴が重要。

### 提案
- `opords`, `fragos`, `frago_links` テーブル追加（SMESC各節JSON、作成/改版/発令時刻）
- API: GET/POST/PUTで版履歴取得・差分表示
- AARへ発令履歴と効果を時系列で出力

### 受け入れ基準
- 再起動後もOPORD/FRAGOが保持され、版履歴を参照可能
- FRAGOチェーン（元OPORD→FRAGO1→FRAGO2…）をUI/JSONで確認
