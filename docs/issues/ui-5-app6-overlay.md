# UI-5: APP‑6記号表示の統一＋コントロールメジャー重ね合わせ

### 症状
- `UnitMarker` 独自記号と `lib/app6.ts` の表現が混在。PL/Boundary/Airspaceの凡例/レイヤ切替がUIから行えない。

### 対応
- `UnitMarker` を `app6.ts` に統一、所属色/階層/ステータスをAPP‑6準拠で描画。
- 左上オーバーレイにレイヤトグル（PL/Boundary/Airspace）。

### 完了条件
- 記号と色が一貫し、管制線を地図に重ねて操作できる。
