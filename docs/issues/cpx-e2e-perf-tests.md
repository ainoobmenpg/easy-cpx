# CPX-QA: E2E（OPORD→命令→確定→レポート）＋負荷テスト

### 背景
機能断片の単体テストは充実。CPXフロー全体のE2Eと簡易負荷テストを追加。

### 提案
- Playwright/Pytestで E2E: OPORD作成→命令→turn/commit→SITREP/INTSUM/LOGSITREP確認
- k6/locustで `/turn/commit` の性能スモーク

### 受け入れ基準
- E2EがCIで安定パス
- スモークで閾値（例: 50命令/ターンで <1.5s）を満たす
