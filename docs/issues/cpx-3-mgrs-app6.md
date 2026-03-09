# CPX-3: MGRS/フェーズライン/境界＋APP-6記号統合

### 背景
座標はXY擬似値で、MGRS/グリッドやフェーズライン、境界、空域の標準表現がない。APP-6記号はデモページに限られている。

### 提案
- データ: `Game.grid_system='MGRS'`、`phase_lines`/`boundaries`/`airspace` テーブル。MGRS<->XY変換ユーティリティ追加。
- 表示: マップにフェーズライン/境界/空域オーバーレイ。APP-6のフレーム/所属色/増補符号を `UnitMarker` に反映。
- API: フィーチャ群をCRUD可能な `/api/control-measures/*` を追加。

### 受け入れ基準
- MGRS文字列入力/出力が可能で、UIでフェーズライン等が表示/編集できる。
- ユニット表示がAPP-6準拠（所属色/フレーム）に更新される。
