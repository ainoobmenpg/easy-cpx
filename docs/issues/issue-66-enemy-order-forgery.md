# Issue #66: /orders API で敵ユニットを自由に操作できてしまう

- 作成日: 2026-03-09
- 種別: Security / Integrity
- 優先度: High

## 事象
`POST /api/orders/` は `unit_id` からユニットを引いて `Order` を登録するだけで、ユニットの陣営（player/enemy）を確認していない。201-246行を見ると `unit.side` も `game_id` もチェックしておらず、そのまま `Order` を保存している。citebackend/app/api/routes.py:204-246

## 影響
- 任意のクライアントが敵ユニット ID を推測（または `/internal` 漏洩を利用）し、`order_type="retreat"` 等を送るだけで敵を後退させたり自滅させたりできる。
- Classic モードでは `/turn/commit` が `create_order` を通らずとも DB 上の `Order` を処理するため、敵側にとって致命的なインテグリティ破壊となる。
- 認証が存在しない現状では誰でも悪用可能。

## 対応案
1. `create_order` で `unit.side != 'player'` の場合は 403 を返す。
2. `TurnAdvanceRequest` などゲーム ID を受け取るエンドポイントも「指定ゲーム ID のコントロール権があるか」をチェックする（ユーザ/セッション導入が望ましい）。
3. 既存の Classic/Arcade 共通ユースケースに合わせ、`turn_commit` 側でも再バリデーション（unit.side, game_id）が必要であれば追加。

## 完了条件
- 敵ユニット ID を指定して `/api/orders/` を叩いても 4xx で拒否される。
- Classic の adjudication ログで敵ユニットに不正命令が混ざらないことを確認。
- 回帰テスト（既存 `pytest`）または新規 API テストで保護が担保されている。
