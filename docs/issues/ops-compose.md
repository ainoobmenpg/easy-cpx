# Ops-Compose: Docker Compose/Make タスク整備

### 背景
開発・検証の立上げを簡素化し、環境差を低減する。

### 提案
- `docker-compose.yml`（backend/frontend/db）と `Makefile`（up/down/test/lint）
- `.env.example` の整備

### 受け入れ基準
- `make up` で一発起動、`make test` で主要テストが走る。
