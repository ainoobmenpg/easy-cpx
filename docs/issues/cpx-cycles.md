# CPX-CYCLES: Planning/Air/Logistics サイクルの導入

### 背景
CPXは複数の時間サイクル（作戦計画、航空任務、兵站）で動く。単一ターン軸のみでは再現が弱い。

### 提案
- `Game` に `planning_cycle`, `air_tasking_cycle`, `logistics_cycle` の概念を追加（進行/締切）。
- Turn確定時に各サイクルの進捗を更新し、未達は判定ペナルティ（Adjudication v1.6）。

### 受け入れ基準
- サイクル状態が保存・可視化され、判定に影響を与える。
