# CPX-5: CCIR/PIR/ROE 等の前提を審判に連結（Adjudication v1.5）

### 背景
攻撃/防御の成功判定が戦術数値中心で、C2/ISR/Fires/Sustainmentの前提遵守が反映されにくい。

### 提案
- 前提チェック: ISR（NAI/TAI/PIR）、Fires（FSCL/SEAD/TOT）、Sustainment（Class III/V所要）、C2（同期マトリクス/通信）をチェックリスト化。
- ロジック: 前提未達時は成功上限=Partial、重大違反はFail寄与。達成度をSITREP/OPSUMに可視化。

### 受け入れ基準
- 前提チェックの通過率がログ/レポートに記録される。
- 同条件で前提達成時は非達成時より成果が上振れする（回帰テストで確認）。
