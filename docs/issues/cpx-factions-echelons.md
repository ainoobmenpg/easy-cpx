# CPX-ORG: 多国籍/階層C2（faction/echelon/callsign）拡張

### 背景
`side: player/enemy` の二值。NATO CPXとして多国籍・階層C2・コールサイン管理を表現。

### 提案
- `Unit.faction`（国/同盟）`echelon`（platoon/company/...）`callsign` を追加
- APP‑6記号の階層符号/所属色を反映

### 受け入れ基準
- 多国籍ORBATをシナリオで記述・表示可能
- Adjudication/レポートで階層が参照される
