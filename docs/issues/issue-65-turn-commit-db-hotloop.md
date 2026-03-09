# Issue #65: /turn/commit(Classic) が注文毎にコミット&再クエリしており著しく非効率

- 作成日: 2026-03-09
- 種別: Performance / Database
- 優先度: High

## 事象
Classic モード用の `_classic_turn_commit` は、受け取った order を 1 件ずつ `db.add(...)` → `db.commit()` → `db.refresh()` する実装になっている。さらに、その直後の結果整形でも `result.get("results", [])` をループしながら `Order` と `Unit` を個別に再クエリする N+1 パターンとなっている。citebackend/app/api/routes.py:600-641

## 影響
- 1 ターンに 20 件の命令を送ると、最低でも 20 回のトランザクションコミット + 40 回の追加 SELECT（Order/Unit）を発行する。SQLite/Postgres どちらでも fsync/round-trip が増大し、Arcade/Classic 兼用サーバでは即ボトルネックになる。
- AI 生成や敵処理より前に I/O が詰まるため、ターン確定までのレイテンシがプレイヤー体験を悪化させる。
- 将来的にマルチプレイやCIテストで同エンドポイントを多用する場合、データベースロックやタイムアウトの温床になる。

## 対応案
1. `request.orders` をバリデートしたうえで 1 つのトランザクションにまとめて bulk insert する（`db.add_all(...)` → 1 回の `db.commit()`）。
2. Order/Unit の参照は `joinedload` などで一括取得し、追加の round-trip をなくす。
3. 余力があれば、Classic/Arcade 両方の turn commit で共通ユーティリティ化し、処理フローを整理する。

## 完了条件
- 1 ターンに複数命令を送ってもコミット回数が 1 回に収束し、N+1 クエリが解消される。
- psql/sqlite のクエリログで往復回数が減っていることを確認する。
- `pytest tests` または専用の turn commit ベンチで性能劣化がない（むしろ短縮される）。
