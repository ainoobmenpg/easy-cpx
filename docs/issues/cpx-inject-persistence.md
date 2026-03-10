# CPX-INJECT: MEL/MIL（Inject）のDB永続化とルーター簡素化

### 背景
`inject_system` はメモリ常駐。`_inject_systems`（routes内のグローバル）を用いた暫定運用で、再起動耐性や監査性に課題。

### 提案
- `Inject`/`InjectLog` モデルを用いた永続化（作成/状態/履歴）。
- ルーターからグローバル辞書を排除し、サービスがDBを介して状態管理。
- 監査: structured_logging へ注入イベントを必ず記録。

### 受け入れ基準
- 再起動してもInject状態/履歴が保持。
- すべての操作がDBトランザクションで一貫。
