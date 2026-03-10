# UI-4: 右ペインをCPX 4タブ（Plan/Sync/Situation/Sustain）に再編

### 背景
- 現状 `info/history/logs/opord/reports`。CPX手順に合わせ、Plan(OPORD/FRAGO)・Sync(時間×効果)・Situation(各レポ)・Sustain(LOGSITREP/兵站)へ再編すると理解負荷が下がる。

### 対応
- 既存 `opord`/`reports` を Plan/Situation に振り分け。Sync/Sustainは新設（モックでも可）。

### 完了条件
- タブ名称・内容がCPXの語感に一致し、想起性が上がる。
