# CPX-REPORTS: Plan/Sync/Situation/Sustain 4タブUIとレポート統合

### 背景
報告生成は可能だがUI統合が限定的。CPX向けに4タブ化し、OPORD/INTSUM/OPSUM/LOGSITREPを役割別に表示。

### 提案
- `Plan`(OPORD/FRAGO編集), `Sync`(時間×効果マトリクス), `Situation`(SITREP/INTSUM/OPSUM), `Sustain`(兵站)
- ロール別の表示制御と更新通知（WS）

### 受け入れ基準
- 主要レポートがタブで閲覧/更新され、ロールにより可視性が異なる
- E2Eで作成→閲覧→更新の流れを確認
