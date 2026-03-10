# CPX-REPLAY: RNGシード＋構造化ログからの完全リプレイ

### 背景
RNGと構造化ログはあるが、リプレイヤがない。

### 提案
- `replay` モードを追加し、ターン/判定/Injectログから状態を復元。
- UIでターン/イベントを追体験できるビューア。

### 受け入れ基準
- 同じシード/ログで100%一致の結果を再生可能。

### 実装 (Completed)

#### 1. GameMode enum に REPLAY モード追加
- `backend/app/models/__init__.py` に `REPLAY = "replay"` を追加

#### 2. ReplayService 実装
- `backend/app/services/replay_service.py`
- 機能:
  - `load_from_db()`: DBからターン/イベントログを読み込み
  - `load_from_logs()`: 構造化ログデータから読み込み
  - `get_state_at_turn()`: 特定ターンの状態を復元
  - `get_event_timeline()`: イベントタイムラインを取得
  - `get_turn_summary()`: ターンサマリーを取得
  - シード管理対応

#### 3. API エンドポイント追加
- `GET /replay/{game_id}/timeline` - イベントタイムライン取得
- `GET /replay/{game_id}/turn/{turn_number}` - ターンサマリー取得
- `GET /replay/{game_id}/state/{turn_number}` - 特定ターンの状態取得
- `POST /replay/from-logs` - ログデータからリプレイ作成

#### 4. テスト追加
- `backend/tests/test_replay_service.py` - 11件のテスト
