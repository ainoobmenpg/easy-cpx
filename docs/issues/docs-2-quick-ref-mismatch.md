# Docs-2: Quick-Refと実装乖離（イベント率/移動/STRIKE条件）

### 問題
`docs/quick-ref.md` の記述が実装と齟齬。
- イベント発生率: Quick-Ref=40%（Turn Flow/Deck） vs 実装=`ArcadeAdjudication.EVENT_DRAW_CHANCE=0.2`（20%）
- 移動仕様: Quick-Refは地形ごとのCells/Turn固定だが、実装は「ユニットMOVE × 地形コスト（Manhattan距離）」
- STRIKE条件/効果: 実装は「隣接必要・連続使用制限・次ターン攻撃不可フラグ」等の制約あり。Quick-Ref未記載。

### 対応
- Quick-Refを実装基準に修正（率20%/移動ルール差替え/STRIKE制約明記）。
- もしくは実装をQuick-Refに合わせる（要合意）。

### 完了条件
- テキストとコードの差分が0（レビューで確認）。
