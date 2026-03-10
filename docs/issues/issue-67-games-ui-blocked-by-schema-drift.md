# Issue #67: `/games` とシナリオ開始が DB スキーマ不整合で 500 になる

- 作成日: 2026-03-10
- 種別: UI / Backend Contract
- 優先度: High

## 事象
Playwright で `http://localhost:3000/games` と `http://localhost:3000/scenarios` を確認したところ、ゲーム一覧の取得とシナリオ開始がどちらも失敗した。UI 上は「ゲームの読み込みに失敗しました」や開始失敗として見えるが、バックエンド実体は DB スキーマ不整合による 500。

- `GET /api/games/` で `sqlite3.OperationalError: no such column: games.scenario_id`
- `POST /api/games/start` で `table games has no column named scenario_id`
- `backend/app/models/__init__.py` の `Game` モデルは `scenario_id`, `game_mode`, `terrain_data`, `map_width`, `player_score` などを要求するが、`backend/alembic/versions/` の head にはそれらを追加する migration が存在しない

## 再現
1. `backend` を起動し、`frontend` を `http://localhost:3000` で開く
2. `/games` に移動する
3. 一覧取得が失敗し、エラー表示になる
4. `/scenarios` で任意シナリオを選び「ミッション開始」を押す
5. ゲーム作成が失敗する

## 影響
- 新規ゲーム開始と既存ゲーム再開の両導線が塞がる
- `/game` 以降の主画面レビューが実質不可能になる
- UI では通信失敗に見えるため、ユーザーが自己解決できない

## 対応案
1. `Game` モデルとの差分を埋める Alembic migration を追加する
2. 既存 SQLite を migrate できることを `alembic upgrade head` で確認する
3. `/api/games/` と `/api/games/start` の API テストを追加し、schema drift を検知できるようにする

## 完了条件
- 空 DB に対して `alembic upgrade head` 後、`GET /api/games/` が 200 で空配列を返す
- `/api/games/start` が 200 で `game_id` を返す
- `http://localhost:3000/games` と `http://localhost:3000/scenarios` から主導線が復旧する
