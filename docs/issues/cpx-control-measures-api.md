# CPX-CM: コントロールメジャーCRUD＋UI（PL/Boundary/Airspace）

### 背景
`grid_system`にデータ構造はあるがAPI/永続化/フロント統合が未整備。

### 提案
- API: `/api/control-measures/{game_id}` でPL/Boundary/AirspaceのCRUD
- DB: `control_measures` 汎用テーブルまたは3表分割
- UI: マップオーバーレイ編集（色/線種/高度）

### 受け入れ基準
- 作成/更新/削除が永続化され、リロード後も反映
- E2Eで作図→保存→表示を確認
