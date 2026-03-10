# Docs-3: Architectureの更新（OPORD/Inject/RBAC/WS/CM/Logistics）

### 問題
`docs/architecture.md` が現状機能（OPORD/FRAGO、MEL/MIL Inject、RBAC、通知WS、Control Measures、Logistics、Structured Logging）を反映していない。図・表も旧構成。

### 対応
- サービス表に `opord_service.py` `inject_system.py` `rbac_service.py` `notification_service.py` `grid_system.py` `logistics_service.py` `structured_logging.py` を追加。
- API一覧に `/turn/commit` `/injects/*` `/games/{id}/opord` `/games/{id}/state(arcade分岐)` を追記。
- WebSocketトポロジとロール別可視性を図示。

### 完了条件
- 図版/表/説明が最新コードと一致し、レビューOK。
