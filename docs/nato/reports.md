# レポート様式仕様

この文書はOperational CPXで使用する5つの報告様式のJSON構造・フィールド説明・サンプルを定義する。

---

## 1. SITREP (戦況報告)

### 1.1 用途
ターンごとの戦闘・移動・偵察結果を統合的に報告。プレイヤーが最も頻繁に参照する文書。

### 1.2 JSON構造

```json
{
  "report_id": "SITREP-001",
  "format": "sitrep",
  "turn": 3,
  "timestamp": "2026-03-10T08:00:00Z",
  "generated_at": "2026-03-10T08:00:00Z",
  "content": {
    "overview": "第3旅団は河岸段丘に達し、敵装甲部隊と交戦中。",
    "turn": 3,
    "time": "0800",
    "friendly_units": [
      {
        "name": "Alpha-1",
        "type": "ARMOR",
        "position": "MGRS: 34T DM 45678 12345",
        "status": "intact",
        "action": "ATTACK"
      }
    ],
    "enemy_units": [
      {
        "name": "Enemy-1",
        "type": "ARMOR",
        "position": "MGRS: 34T DM 46789 12456",
        "status": "damaged",
        "assessment": "confirmed"
      },
      {
        "name": "Enemy-2",
        "type": "INFANTRY",
        "position": "推定: (x:28, y:20)",
        "status": "estimated",
        "assessment": "estimated"
      }
    ],
    "events": [
      {
        "type": "combat",
        "description": "Alpha-1がEnemy-1を攻撃、被害2与えた"
      }
    ],
    "commander_order": "河岸を維持し、敵の突破を阻止すること",
    "score": {
      "player": 20,
      "enemy": 10,
      "turn": 3
    }
  }
}
```

### 1.3 フィールド説明

| フィールド | 型 | 説明 |
|-----------|-----|------|
| report_id | string | 固有ID (SITREP-XXXX) |
| format | string | "sitrep"固定 |
| turn | int | 現在のターン |
| timestamp | ISO8601 | 生成日時 |
| content.overview | string | 全体サマリー |
| content.friendly_units | array | 味方ユニット一覧 |
| content.enemy_units | array | 敵ユニット一覧（確認度込み） |
| content.events | array | ターン内のイベント |
| content.commander_order | string | 上官命令 |
| content.score | object | VPスコア（Arcade） |

---

## 2. INTSUM (情報要約)

### 2.1 用途
敵配置・動き・戦力を集約し、偵察結果と評価を報告。

### 2.2 JSON構造

```json
{
  "report_id": "INTSUM-001",
  "format": "intsumm",
  "turn": 3,
  "timestamp": "2026-03-10T08:00:00Z",
  "generated_at": "2026-03-10T08:00:00Z",
  "content": {
    "summary": "ターン3現在、味方は1個師団が作戦可能、敵は確認2個、推定1個大隊が行動中",
    "enemy_dispositions": [
      {
        "unit_name": "Enemy-ARMOR-1",
        "position": "(x:25, y:18)",
        "strength": "damaged",
        "assessment": "confirmed"
      },
      {
        "unit_name": "推定-Enemy-INF-2",
        "position": "(x:28, y:20)",
        "strength": "推定",
        "assessment": "estimated"
      }
    ],
    "friendly_dispositions": [
      {
        "unit_name": "Alpha-1",
        "position": "(x:22, y:18)",
        "status": "intact"
      }
    ],
    "intelligence_gaps": [
      "1個の敵大隊の位置が未確認"
    ],
    "recommendations": [
      "偵察を強化し、敵配置の把握を拡大せよ"
    ]
  }
}
```

### 2.3 フィールド説明

| フィールド | 型 | 説明 |
|-----------|-----|------|
| content.summary | string | 全体サマリー |
| content.enemy_dispositions | array | 敵配置（確認度付） |
| content.friendly_dispositions | array | 味方配置 |
| content.intelligence_gaps | array | 未確認情報リスト |
| content.recommendations | array | 指揮官への推奨 |

### 2.4 確認度区分

| assessment | 意味 | 条件 |
|------------|------|------|
| "confirmed" | 確認済み | 視覚・センサーで確認 |
| "estimated" | 推定 | 間接証拠から判断 |
| "suspected" | 疑念 | 単一情報源 |
| "unknown" | 不明 | 情報なし |

---

## 3. OPSUM (作戦要約)

### 3.1 用途
今ターン行われた作戦・結果・進行中の作戦・予定作戦を報告。

### 3.2 JSON構造

```json
{
  "report_id": "OPSUM-001",
  "format": "opsumm",
  "turn": 3,
  "timestamp": "2026-03-10T08:00:00Z",
  "generated_at": "2026-03-10T08:00:00Z",
  "content": {
    "operations_conducted": [
      {
        "operation_name": "Alpha-1の作戦",
        "objective": "敵装甲部隊撃破",
        "outcome": "success",
        "units_involved": ["Alpha-1"],
        "results": "任務成功"
      }
    ],
    "current_operations": [
      {
        "operation_name": "河岸防御",
        "status": "ongoing",
        "units_involved": ["Alpha-1", "Bravo-1"]
      }
    ],
    "planned_operations": [
      {
        "operation_name": "右翼包囲",
        "objective": "敵側面攻撃",
        "planned_time": "Turn 4",
        "units_assigned": ["Charlie-1"]
      }
    ],
    "commander_assessment": "概ね作戦成功 - 戦況控制的"
  }
}
```

### 3.3 フィールド説明

| フィールド | 型 | 説明 |
|-----------|-----|------|
| content.operations_conducted | array | 今ターン完了した作戦 |
| content.current_operations | array | 進行中の作戦 |
| content.planned_operations | array | 予定作戦 |
| content.commander_assessment | string | 指揮官評価 |

---

## 4. LOGSITREP (兵站報告)

### 4.1 用途
弾薬・燃料・整備状況と補給要求を報告。

### 4.2 JSON構造

```json
{
  "report_id": "LOGSITREP-001",
  "format": "logsitrep",
  "turn": 3,
  "timestamp": "2026-03-10T08:00:00Z",
  "generated_at": "2026-03-10T08:00:00Z",
  "content": {
    "supply_status": {
      "ammo": {
        "full": 4,
        "depleted": 2,
        "exhausted": 0
      },
      "fuel": {
        "full": 3,
        "depleted": 2,
        "exhausted": 1
      },
      "readiness": {
        "full": 5,
        "depleted": 1,
        "exhausted": 0
      }
    },
    "supply_lines": [
      {
        "line_id": "main-supply",
        "status": "open",
        "last_verified": "0800"
      }
    ],
    "attrition": [
      {
        "unit": "Alpha-1",
        "ammo_spent": 120,
        "fuel_spent": 80,
        "maintenance_needed": false
      }
    ],
    "resupply_requests": [
      {
        "unit": "Bravo-1",
        "type": "fuel",
        "priority": "high",
        "status": "pending"
      }
    ]
  }
}
```

### 4.3 フィールド説明

| フィールド | 型 | 説明 |
|-----------|-----|------|
| content.supply_status | object | 弾薬/燃料/整備の充足状況 |
| content.supply_lines | array | 補給路状況 |
| content.attrition | array | 各ユニットの消費量 |
| content.resupply_requests | array | 補給要求 |

---

## 5. SALUTE (敵情報報告)

### 5.1 用途
個別敵ユニットの詳細な報告。発見時に生成。

### 5.2 JSON構造

```json
{
  "report_id": "SALUTE-001",
  "format": "salute",
  "turn": 3,
  "timestamp": "2026-03-10T08:00:00Z",
  "generated_at": "2026-03-10T08:00:00Z",
  "content": {
    "report_id": "SALUTE-001",
    "turn": 3,
    "timestamp": "2026-03-10T08:00:00Z",
    "size": "大隊",
    "activity": "移動中",
    "location": "MGRS: 34T DM 46789 12456",
    "unit": "敵装甲歩兵大隊",
    "time": "0800",
    "equipment": "戦車4両、装甲車8両",
    "assessment": "河岸段丘方面へ移動中、側面が暴露している"
  }
}
```

### 5.3 フィールド説明

| フィールド | 型 | 説明 |
|-----------|-----|------|
| content.size | string | 規模（班/分隊/小隊/大隊等） |
| content.activity | string | 行動（静止/移動/集結等） |
| content.location | string | 位置（MGRSまたは座標） |
| content.unit | string | 部隊名/種別 |
| content.time | string | 観察時刻 |
| content.equipment | string | 装備 |
| content.assessment | string | 評価・interop |

---

## 6. AAR (行動評価) との関係

AARはゲーム終了後に生成され、MOP/MOE指標を含む。

### MOP (Measure of Performance) - 運用効率

| 指標 | 計算 |
|------|------|
| 損害率 | 被害ユニット数 / 投入ユニット数 |
| 弾薬効率 | 与えた被害 / 消費弾薬 |
| 目標達成率 | 達成目標数 / 総目標数 |

### MOE (Measure of Effectiveness) - 任務効果

| 指標 | 計算 |
|------|------|
| 戦術的優位 | 敵被害 / 味被害 |
| 速度 | 目標達成ターン / 目標期限ターン |
| 情報優位 | 確認済み敵 / 総敵ユニット |

---

## 7. レポート生成条件

| レポート | 生成タイミング |
|----------|----------------|
| SITREP | ターン終了時（必須） |
| INTSUM | 偵察 результат発生時、ターン終了時 |
| OPSUM | 作戦 результат発生時 |
| LOGSITREP | ターン終了時（兵站フェーズ後） |
| SALUTE | 敵ユニット初回発見時 |

---

## 8. 関連文書

- [glossary.md](./glossary.md)
- [game-rules.md](../game-rules.md)
- [quick-ref.md](../quick-ref.md)
- `backend/app/services/report_generator.py`
