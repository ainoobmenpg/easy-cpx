# CPX-REPORTS: SITREP/INTSUM/OPSUM/LOGSITREP/SALUTE API実装

### 背景
`report_generator.py` に標準レポート生成器があるが、公開APIが未整備。UIや外部連携のためAPI化が必要。

### 提案
- `GET /api/games/{id}/reports?type={sitrep|intsum|opsum|logsitrep|salute}&turn={n}`
- 生成/保存戦略: 低コストではオンデマンド生成、必要に応じ `turns.reports` JSONにキャッシュ。
- RBAC: BLUE/REDはFoW適用、WHITE/ADMINはフル。

### 受け入れ基準
- 各typeでJSONを返却し、スキーマ準拠（Docs-7と一致）。
- RBACにより機微情報が遮断される（テストあり）。
