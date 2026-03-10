# NATO/作戰用語集

この文書はOperational CPXで使用するNATO標準用語・略語の和訳とStyles Guideを定義する。

---

## 1. 基本原則

### 1.1 表記方針

| 項目 | 方針 |
|------|------|
| 日本語 | ひらがな交じり文（カタカナ語混在可） |
| 英略語 | すべて大文字（例: NATO, OPORD） |
| 数字 | 半角アラビア数字 |
| 軍隊編制 | 漢数字 + 助数詞（1個師団、2個小隊） |

### 1.2 編制階層の表記

| NATO級 | 日本語 | 略号 | 規模 |
|--------|--------|------|------|
| Section | 班 | 班 | 8-12名 |
| Platoon | 分隊 | 分隊 | 16-30名 |
| Company | 小隊 | 小隊 | 60-150名 |
| Battalion | 大隊 | 大隊 | 300-1,000名 |
| Brigade | 旅団 | 旅団 | 3,000-5,000名 |
| Division | 師団 | 師団 | 10,000-20,000名 |
| Corps | 軍団 | 軍団 | 20,000-+ |

---

## 2. 重要用語

### 2.1 計画・命令系

| 英略語 | 日本語 | 説明 |
|--------|--------|------|
| OPORD | 作戦命令 | Operation Order。完整的作戦指示書 |
| FRAGO | 変更命令 | Fragmentary Order。OPORDの変更部 |
| SMESC | SMESC形式 | Situation, Mission, Execution, Service Support, Command & Signal |
| COA | 行動案 | Course of Action |
| OPLAN | 作戦計画 | Operation Plan |

### 2.2 報告様式

| 英略語 | 日本語 | 説明 |
|--------|--------|------|
| SITREP | 戦況報告 | Situation Report。戦場状況の定期報告 |
| INTSUM | 情報要約 | Intelligence Summary。敵情報まとめ |
| OPSUM | 作戦要約 | Operations Summary |
| LOGSITREP | 兵站報告 | Logistics Situation Report |
| SALUTE | SALUTE報告 | Size, Activity, Location, Unit, Time, Equipment |
| AAR | 行動評価 | After Action Review |

### 2.3 任務・状態

| 英略語 | 日本語 | 説明 |
|--------|--------|------|
| CCIR | 重要情報要求 | Commander's Critical Information Requirement |
| PIR | 優先情報要求 | Priority Intelligence Requirement |
| ROE | 交戦規則 | Rules of Engagement |
| CC | 統制 | Command and Control |
| C2 | C2 | Command and Control |

### 2.4 航空・火力

| 英略語 | 日本語 | 説明 |
|--------|--------|------|
| ATO | 航空任務命令 | Air Tasking Order |
| ACO | 航空統制命令 | Air Control Order |
| CAS | 近接航空支援 | Close Air Support |
| SEAD | 防空排除 | Suppression of Enemy Air Defenses |
| TAI | 攻撃目標 | Target Area of Interest |
| FSCL | 前方火力支援線 | Fire Support Coordination Line |
| ROZ | 制限区域 | Restricted Operations Zone |

### 2.5 兵站・補給

| 英略語 | 日本語 | 説明 |
|--------|--------|------|
| Class I | 食糧 | Subsistence |
| Class III | 燃料 | Petroleum, Oil, Lubricants |
| Class V | 弾薬 | Ammunition |
| Class VII | 完成品 | Major End Items |
| MSR | 補給路 | Main Supply Route |
| ASR | 代替補給路 | Alternate Supply Route |
| FARP | 前進整備地域 | Forward Arming and Refueling Point |

### 2.6 地図・座標

| 英略語 | 日本語 | 説明 |
|--------|--------|------|
| MGRS |軍用グリッド参照 | Military Grid Reference System |
| APP-6 | APP-6記号 | NATO Military Symbol Standard |
| FLOT | 戦線 | Forward Line of Own Troops |
| Phase Line | フェーズライン | 作戦上の線 |
| L.O.S. | 視線 | Line of Sight |

---

## 3. 文体ガイドライン

### 3.1 SITREP文例

```
SITREP-001
Turn: 3, Time: 0800
OVERVIEW: 第3旅団は河岸段丘に達し、敵装甲部隊と交戦中。
CONFIRMED: 敵戦車4両が(x:25, y:18)を確認、撃破1両。
ESTIMATED: 敵步兵大隊が(x:28, y:20)方面に推定。
Commander's Intent: 河岸を維持し、敵の突破を阻止すること。
Next: 増援到着後、午前中にも反撃体制に入る。
```

### 3.2 確認度表現

| 区分 | 英語 | 日本語 | 意味 |
|------|------|--------|------|
| CONFIRMED | Confirmed | 確認済み | 視覚・センサーで実確認 |
| ASSESSED | Assessed | 推定 | 複数の間接証拠から判断 |
| SUSPECTED | Suspected | 疑念 | 単一情報源的 |
| UNKNOWN | Unknown | 不明 | 情報が皆無 |

### 3.3 状況形容

| 英 | 和 |
|----|----|
| Intact | 無傷 |
| Light damage | 軽損 |
| Moderate damage | 中損 |
| Heavy damage | 大損 |
| Combat ineffective | 戦闘不能 |
| Full strength | 充足 |
| Depleted | 低下 |
| Exhausted | 枯渇 |

---

## 4. クイックリファレンス

### 4.1 ターン進行

| Phase | フェーズ | 処理内容 |
|-------|----------|----------|
| Order Issue | 命令発行 | プレイヤーが命令入力 |
| Movement | 移動 | 全ユニットの位置更新 |
| Combat | 戦闘 | 攻撃・防御判定 |
| Air/AA | 防空 | 航空・対空処理 |
| Attrition | 損耗 | HP更新、破壊判定 |
| Logistics | 兵站 | 弾薬・燃料更新 |
| Intelligence | 偵察 | FoW更新 |
| Event | イベント | ランダムイベント発動 |

### 4.2 判定結果

| Diff | Result | 結果 | ダメージ |
|------|--------|------|----------|
| ≤-3 | CRITICAL_FAIL | 致命的失敗 | 攻撃者:1被害 |
| -2 | FAIL | 失敗 | なし |
| -1, 0 | PARTIAL | 部分的成功 | 防御者:1被害 |
| +1 | SUCCESS | 成功 | 防御者:2被害 |
| +2 | GREAT |  великолепный | 防御者:3被害 |
| ≥+3 | CRITICAL |  критический | 防御者:4被害 |

---

## 5. 禁忌事項

- 原文を欠落させたAI生成文書を流用しない
- 未確認情報を「確認済み」として報告しない
- プレイヤーの知り得ない情報をSITREPに含めない
- NATO用語とソ連・ロシア用語を混在させない（例:「大隊」と「BAT」を同時に使わない）

---

## 6. 関連文書

- [game-rules.md](../game-rules.md)
- [quick-ref.md](../quick-ref.md)
- [reports.md](./reports.md)
