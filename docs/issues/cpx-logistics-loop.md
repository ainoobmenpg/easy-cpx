# CPX-LOG: 兵站サービスのターン連結＋LOGSITREP反映

### 背景
兵站サービスは独立。ターン確定時に再補給/輸送/遮断イベントを反映し、LOGSITREPへ出力したい。

### 提案
- `turn_commit`で `logistics_service.advance_turn()` を呼び、イベントをTurn/Eventsへ保存
- 兵站状態をSITREP/LOGSITREPに集約
- UI `Sustain`タブで可視化

### 受け入れ基準
- ルート遮断/在庫不足がユニット行動や審判に影響
- LOGSITREPに在庫・輸送・要求が出力
